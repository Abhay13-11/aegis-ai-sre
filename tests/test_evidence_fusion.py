"""
Tests for Evidence Fusion & Deterministic Root Cause Analysis Formula
"""

import time
import pytest
from engine.topology.graph import DependencyGraph
from engine.rca.evidence_fusion import EvidenceFusionEngine
from engine.models.schemas import AnomalyEvent, AnomalySeverity, EvidenceItem, SignalType

def test_evidence_fusion_weights_and_ranking():
    graph = DependencyGraph()
    fusion = EvidenceFusionEngine(dependency_graph=graph)

    # Injected situation: inventory_service fails, causing symptoms on order_service and api_gateway
    now = time.time()
    anomalies = [
        AnomalyEvent(
            service_id="inventory_service",
            detector_type="Z_SCORE",
            metric_name="p95_latency",
            current_value=1200.0,
            expected_value=25.0,
            deviation_score=15.0,
            severity=AnomalySeverity.CRITICAL,
            timestamp=now - 20.0, # Started FIRST
            summary="DB latency spike"
        ),
        AnomalyEvent(
            service_id="order_service",
            detector_type="RULE_BASED",
            metric_name="error_rate",
            current_value=35.0,
            expected_value=5.0,
            deviation_score=30.0,
            severity=AnomalySeverity.HIGH,
            timestamp=now - 5.0, # Started LATER
            summary="Cascading 500 error from downstream"
        ),
        AnomalyEvent(
            service_id="api_gateway",
            detector_type="RULE_BASED",
            metric_name="error_rate",
            current_value=20.0,
            expected_value=5.0,
            deviation_score=15.0,
            severity=AnomalySeverity.HIGH,
            timestamp=now, # Started LAST
            summary="Gateway 502 bad gateway"
        )
    ]

    evidence = [
        EvidenceItem(
            signal_type=SignalType.METRIC,
            service_id="inventory_service",
            summary="Postgres pool exhaustion",
            timestamp=now - 20.0
        )
    ]

    candidates = fusion.compute_scores(
        candidate_services=["inventory_service", "order_service", "api_gateway", "user_service"],
        anomalies=anomalies,
        incident_evidence=evidence
    )

    # Check that candidates are ranked
    assert len(candidates) == 4
    # Root cause candidate #1 must be inventory_service because it failed first,
    # has topological ancestry, and highest severity!
    assert candidates[0].component_id == "inventory_service"
    assert candidates[0].rank == 1
    assert candidates[0].score > candidates[1].score
    assert candidates[0].score_breakdown.temporal_correlation > candidates[1].score_breakdown.temporal_correlation
