"""
AEGIS End-to-End System Test
Tests the full lifecycle: Healthy -> Chaos Injection -> Detection -> RCA -> Investigation -> Remediation -> Verification.
"""

import pytest
import asyncio
from services.testbed_manager import MicroservicesTestbed
from engine.telemetry import TelemetryPipeline
from engine.topology import DependencyGraph
from engine.chaos import ChaosEngine
from engine.detectors import AnomalyDetectorManager
from engine.rca import EvidenceFusionEngine, IncidentManager
from engine.agent import AgentToolRegistry, InvestigationAgent
from engine.remediation import PolicyGate, RemediationExecutorAndVerifier
from engine.models.schemas import FaultType, FaultInjectionRequest, IncidentStatus

def test_end_to_end_aegis_investigation_and_recovery_loop():
    async def _run():
        # 1. Initialize complete stack
        telemetry = TelemetryPipeline()
        testbed = MicroservicesTestbed(telemetry_pipeline=telemetry)
        graph = DependencyGraph()
        chaos = ChaosEngine(testbed)
        detectors = AnomalyDetectorManager(telemetry.metrics)
        fusion = EvidenceFusionEngine(graph, telemetry.traces)
        incident_mgr = IncidentManager(fusion, graph, telemetry)
        
        tools = AgentToolRegistry(graph, telemetry, testbed)
        agent = InvestigationAgent(tools, fusion)
        
        policy = PolicyGate()
        executor = RemediationExecutorAndVerifier(testbed, incident_mgr, telemetry)

        # 2. Verify initial healthy baseline
        baseline_snaps = testbed.collect_service_metrics()
        assert baseline_snaps["inventory_service"].status.value == "HEALTHY"

        # 3. Inject Controlled Chaos: PostgreSQL Pool Exhaustion
        fault_req = FaultInjectionRequest(
            fault_type=FaultType.DB_POOL_EXHAUSTION,
            target_service="inventory_service",
            params={"pool_size": 15},
            description="E2E PostgreSQL Pool Exhaustion Test"
        )
        active_fault = chaos.inject_fault(fault_req)
        assert active_fault.is_active is True

        # 4. Generate traffic through testbed to manifest errors
        for _ in range(3):
            await testbed.execute_gateway_transaction("/api/checkout")
        
        # 5. Collect metrics & Detect Anomalies
        snaps = testbed.collect_service_metrics()
        anomalies = detectors.evaluate_services(snaps)
        assert len(anomalies) > 0

        # 6. Automatic Incident Creation & Correlated Evidence Fusion
        incident = incident_mgr.create_incident_from_anomalies(anomalies, title_prefix="E2E Test Incident")
        assert incident.status == IncidentStatus.OPEN
        assert "inventory_service" in incident.affected_services
        # Top root cause candidate should be inventory_service
        assert incident.root_cause_service == "inventory_service"

        # 7. LLM Investigation Agent runs bounded tools & returns grounded diagnosis
        diagnosis = agent.investigate(incident)
        assert diagnosis.status in ("diagnosed", "needs_human_review")
        assert diagnosis.root_cause_candidates[0].component_id == "inventory_service"
        assert diagnosis.recommended_action_type == "tune_connection_pool_limit"

        # 8. Safe Policy Gate: Validate proposal & Require Approval for High-Risk action
        action_proposal = policy.validate_proposal(
            action_type=diagnosis.recommended_action_type,
            target_service=diagnosis.root_cause_candidates[0].component_id,
            parameters={"max_connections": 30}
        )
        action_proposal.incident_id = incident.incident_id
        assert action_proposal.requires_approval is True

        # Human Approver approves action
        approved_action = policy.approve_action(action_proposal, approver_name="Senior SRE")

        # 9. Execute Sandboxed Remediation
        executed_action = await executor.execute_action(approved_action)
        assert executed_action.state.value == "SUCCEEDED"

        # 10. Post-Action Grounded Verification
        report = await executor.verify_recovery(executed_action, wait_seconds=0.1)
        assert report.overall_recovery_verified is True
        # The incident status must transition to RESOLVED!
        assert incident.status == IncidentStatus.RESOLVED

        # Clean up chaos
        chaos.reset_all()

    asyncio.run(_run())
