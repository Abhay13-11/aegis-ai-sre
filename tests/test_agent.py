"""
Tests for LLM Investigation Agent (Bounded Tools, Schema Validation, Guardrails)
"""

import pytest
from engine.topology.graph import DependencyGraph
from engine.telemetry import TelemetryPipeline
from engine.rca.evidence_fusion import EvidenceFusionEngine
from engine.agent.tools import AgentToolRegistry
from engine.agent.investigator import InvestigationAgent
from engine.models.schemas import Incident, IncidentSeverity, IncidentStatus

def test_agent_tool_registry():
    graph = DependencyGraph()
    telemetry = TelemetryPipeline()
    tools = AgentToolRegistry(graph, telemetry)

    # 1. Test get_service_graph tool
    topo = tools.get_service_graph()
    assert "nodes" in topo
    assert "edges" in topo
    assert len(tools.audit_log) == 1

    # 2. Test get_metric tool
    metric = tools.get_metric("order_service", "p95_latency")
    assert metric["service"] == "order_service"
    assert "stats" in metric

def test_agent_investigation_workflow_and_schema_validation():
    graph = DependencyGraph()
    telemetry = TelemetryPipeline()
    fusion = EvidenceFusionEngine(graph)
    tools = AgentToolRegistry(graph, telemetry)
    agent = InvestigationAgent(tools, fusion)

    incident = Incident(
        incident_id="inc_test_101",
        title="Payment Latency Anomaly",
        severity=IncidentSeverity.P1_CRITICAL,
        status=IncidentStatus.OPEN,
        affected_services=["payment_service", "order_service"]
    )

    output = agent.investigate(incident)
    # Validate Pydantic schema structure
    assert output.schema_version == "1.0"
    assert output.incident_id == "inc_test_101"
    assert output.status in ("diagnosed", "needs_human_review", "inconclusive")
    assert output.requires_approval is True
    assert len(output.root_cause_candidates) > 0
    assert output.recommended_action_type in ("clear_redis_cache", "inspect_connection_pool", "scale_replicas", "restart_service")
