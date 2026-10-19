"""
Tests for Safe Remediation (Policy Gate, Human Approval, Execution & Verification)
"""

import pytest
import asyncio
from engine.models.schemas import ActionRiskLevel, ActionState, IncidentStatus, IncidentSeverity, Incident
from engine.remediation.policy_gate import PolicyGate
from engine.remediation.executor_and_verifier import RemediationExecutorAndVerifier
from services.testbed_manager import MicroservicesTestbed
from engine.rca.incident_manager import IncidentManager
from engine.rca.evidence_fusion import EvidenceFusionEngine
from engine.topology.graph import DependencyGraph

def test_policy_gate_blocks_forbidden_and_dangerous_actions():
    gate = PolicyGate()

    # Blocked if not allowlisted
    with pytest.raises(PermissionError):
        gate.validate_proposal("delete_database_records", "inventory_service", {})

    # Blocked if command injection attempted
    with pytest.raises(ValueError):
        gate.validate_proposal("tune_connection_pool_limit", "inventory_service", {"max_connections": "20; rm -rf /"})

def test_policy_gate_risk_classification_and_approval():
    gate = PolicyGate()

    # Low risk action (e.g. inspect_connection_pool) requires no approval
    low_action = gate.validate_proposal("inspect_connection_pool", "inventory_service", {})
    assert low_action.risk_level == ActionRiskLevel.LOW
    assert low_action.requires_approval is False
    assert low_action.state == ActionState.APPROVED

    # High risk action (e.g. tune_connection_pool_limit) requires approval
    high_action = gate.validate_proposal("tune_connection_pool_limit", "inventory_service", {"max_connections": 30})
    assert high_action.risk_level == ActionRiskLevel.HIGH
    assert high_action.requires_approval is True
    assert high_action.state == ActionState.PENDING_APPROVAL

    # Approve action
    approved = gate.approve_action(high_action, approver_name="Lead SRE")
    assert approved.state == ActionState.APPROVED
    assert approved.approved_by == "Lead SRE"

def test_remediation_execution_and_telemetry_verification():
    async def _run():
        testbed = MicroservicesTestbed()
        graph = DependencyGraph()
        fusion = EvidenceFusionEngine(graph)
        inc_mgr = IncidentManager(fusion, graph)
        executor = RemediationExecutorAndVerifier(testbed, inc_mgr)

        # Incur an active pool issue
        testbed.postgres.exhaustion_mode = True
        testbed.postgres.waiting_queries = 8

        # Create dummy incident
        inc = Incident(
            incident_id="inc_rem_test",
            title="DB Pool Saturation",
            severity=IncidentSeverity.P1_CRITICAL,
            status=IncidentStatus.OPEN,
            affected_services=["inventory_service"]
        )
        inc_mgr.incidents[inc.incident_id] = inc

        gate = PolicyGate()
        action = gate.validate_proposal("tune_connection_pool_limit", "inventory_service", {"max_connections": 30})
        action.incident_id = inc.incident_id
        gate.approve_action(action, "Lead SRE")

        # Execute
        executed = await executor.execute_action(action)
        assert executed.state == ActionState.SUCCEEDED
        assert testbed.postgres.exhaustion_mode is False

        # Verify recovery
        report = await executor.verify_recovery(executed, wait_seconds=0.05)
        assert report.overall_recovery_verified is True
        assert report.status == ActionState.VERIFIED_RECOVERED
        assert inc.status == IncidentStatus.RESOLVED

    asyncio.run(_run())
