"""
Tests for Anomaly Detection Layer (Rule-Based, Z-Score, MAD, Isolation Forest)
"""

import pytest
from engine.models.schemas import ServiceSnapshot, ServiceHealthStatus
from engine.detectors.rule_based import RuleBasedDetector
from engine.detectors.z_score import ZScoreDetector, MADDetector
from engine.detectors.isolation_forest_detector import IsolationForestDetector

def test_rule_based_detector_triggers_on_high_error_rate():
    detector = RuleBasedDetector(error_rate_threshold=5.0)
    snap = ServiceSnapshot(
        service_id="order_service",
        name="Order Service",
        status=ServiceHealthStatus.DEGRADED,
        error_rate=12.5,
        p95_latency_ms=100.0
    )
    anomalies = detector.evaluate(snap)
    assert len(anomalies) == 1
    assert anomalies[0].metric_name == "error_rate"
    assert anomalies[0].current_value == 12.5

def test_z_score_detector():
    z_detector = ZScoreDetector(z_threshold=3.0, min_samples=10)
    # Baseline normal values around 50ms
    history = [50.0, 52.0, 48.0, 51.0, 49.0, 53.0, 50.0, 51.0, 49.0, 52.0]
    # No anomaly for normal point
    assert z_detector.evaluate("order_service", "latency", history + [53.0]) is None

    # Huge spike to 950ms should trigger anomaly
    spike = z_detector.evaluate("order_service", "latency", history + [950.0])
    assert spike is not None
    assert spike.deviation_score > 3.0
    assert spike.detector_type == "Z_SCORE"

def test_mad_detector():
    mad_detector = MADDetector(threshold=3.5, min_samples=10)
    history = [20.0, 21.0, 19.0, 20.0, 22.0, 20.0, 19.0, 21.0, 20.0, 20.0]
    spike = mad_detector.evaluate("inventory_service", "p95_latency", history + [400.0])
    assert spike is not None
    assert spike.detector_type == "MAD"

def test_isolation_forest_detector():
    if_detector = IsolationForestDetector()
    # Provide synthetic normal samples
    for i in range(25):
        snap = ServiceSnapshot(
            service_id="payment_service",
            name="Payment Service",
            status=ServiceHealthStatus.HEALTHY,
            cpu_percent=25.0 + (i % 3),
            memory_percent=40.0 + (i % 2),
            p95_latency_ms=30.0 + (i % 5),
            error_rate=0.0
        )
        if_detector.evaluate(snap)

    # Anomaly vector with extreme CPU and error rate
    abnormal_snap = ServiceSnapshot(
        service_id="payment_service",
        name="Payment Service",
        status=ServiceHealthStatus.CRITICAL,
        cpu_percent=99.0,
        memory_percent=95.0,
        p95_latency_ms=1800.0,
        error_rate=80.0
    )
    result = if_detector.evaluate(abnormal_snap)
    assert result is not None
    assert result.detector_type == "ISOLATION_FOREST"
