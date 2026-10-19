"""
AEGIS AI-SRE Core Platform Backend
FastAPI server exposing all REST APIs for topology, telemetry,
incidents, agent investigation, remediation policy, and research benchmarks.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import time
import asyncio

from engine.models.schemas import (
    ServiceSnapshot,
    FaultInjectionRequest,
    ActiveFault,
    Incident,
    IncidentStatus,
    StructuredDiagnosisOutput,
    RemediationActionProposal,
    VerificationReport,
    ActionState
)

from services.testbed_manager import MicroservicesTestbed
from engine.telemetry import TelemetryPipeline
from engine.chaos import ChaosEngine, CHAOS_BENCHMARK_SCENARIOS
from engine.detectors import AnomalyDetectorManager
from engine.topology import DependencyGraph
from engine.rca import EvidenceFusionEngine, IncidentManager
from engine.agent import AgentToolRegistry, InvestigationAgent
from engine.remediation import PolicyGate, RemediationExecutorAndVerifier
from engine.benchmarks import BenchmarkEvaluator

app = FastAPI(
    title="AEGIS AI-SRE Intelligence Platform",
    description="Evidence-Grounded AI-SRE for Microservice Incident Diagnosis & Safe Remediation",
    version="1.0.0"
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Component Initialization ---
telemetry_pipeline = TelemetryPipeline()
testbed = MicroservicesTestbed(telemetry_pipeline=telemetry_pipeline)
dependency_graph = DependencyGraph()
chaos_engine = ChaosEngine(testbed=testbed)
detector_manager = AnomalyDetectorManager(metrics_collector=telemetry_pipeline.metrics)
fusion_engine = EvidenceFusionEngine(dependency_graph=dependency_graph, trace_store=telemetry_pipeline.traces)
incident_manager = IncidentManager(fusion_engine=fusion_engine, dependency_graph=dependency_graph, telemetry_pipeline=telemetry_pipeline)

tool_registry = AgentToolRegistry(dependency_graph=dependency_graph, telemetry_pipeline=telemetry_pipeline, testbed=testbed)
investigation_agent = InvestigationAgent(tool_registry=tool_registry, fusion_engine=fusion_engine)

policy_gate = PolicyGate()
remediation_executor = RemediationExecutorAndVerifier(testbed=testbed, incident_manager=incident_manager, telemetry_pipeline=telemetry_pipeline)

benchmark_evaluator = BenchmarkEvaluator(
    testbed=testbed,
    chaos_engine=chaos_engine,
    detector_manager=detector_manager,
    fusion_engine=fusion_engine,
    graph=dependency_graph,
    agent=investigation_agent,
    policy_gate=policy_gate,
    executor=remediation_executor
)

# Background Telemetry & Anomaly Worker Loop
_background_loop_task = None

async def system_monitoring_loop():
    """Periodically collects metrics, checks anomalies, and auto-detects incidents."""
    while True:
        try:
            snapshots = testbed.collect_service_metrics()
            anomalies = detector_manager.evaluate_services(snapshots)
            
            # If critical anomalies detected and no active incident is open, create one
            if anomalies:
                has_critical = any(a.severity.value in ("CRITICAL", "HIGH") for a in anomalies)
                active_inc = incident_manager.get_incident(incident_manager.active_incident_id) if incident_manager.active_incident_id else None
                if has_critical and (not active_inc or active_inc.status == IncidentStatus.RESOLVED):
                    incident_manager.create_incident_from_anomalies(anomalies)
        except Exception:
            pass
        await asyncio.sleep(2.0)

@app.on_event("startup")
async def startup_event():
    global _background_loop_task
    testbed.start_traffic()
    _background_loop_task = asyncio.create_task(system_monitoring_loop())

@app.on_event("shutdown")
async def shutdown_event():
    testbed.stop_traffic()
    if _background_loop_task:
        _background_loop_task.cancel()

# --- Health & Status ---

@app.get("/api/health")
def get_health():
    return {
        "status": "HEALTHY",
        "system": "AEGIS AI-SRE Platform",
        "version": "1.0.0",
        "traffic_running": testbed.traffic_running,
        "active_faults_count": len(chaos_engine.list_active_faults()),
        "open_incidents_count": sum(1 for inc in incident_manager.incidents.values() if inc.status != IncidentStatus.RESOLVED)
    }

# --- Service Topology & Health ---

@app.get("/api/services")
def list_services() -> Dict[str, ServiceSnapshot]:
    return testbed.collect_service_metrics()

@app.get("/api/topology")
def get_topology():
    return dependency_graph.to_dict()

@app.get("/api/services/{service_id}/blast_radius")
def get_service_blast_radius(service_id: str):
    return dependency_graph.compute_blast_radius(service_id)

# --- Telemetry APIs ---

@app.get("/api/telemetry/metrics")
def query_metrics(service_id: str, metric_name: str, window: float = 60.0):
    return telemetry_pipeline.metrics.get_stats(service_id, metric_name, window)

@app.get("/api/telemetry/logs")
def query_logs(
    service_id: Optional[str] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50
):
    return [l.model_dump() for l in telemetry_pipeline.logs.query(service_id=service_id, keyword=keyword, limit=limit)]

@app.get("/api/telemetry/traces")
def query_traces(limit: int = 25, error_only: bool = False):
    return telemetry_pipeline.traces.get_recent_traces(limit=limit, error_only=error_only)

@app.get("/api/telemetry/traces/{trace_id}")
def get_trace_detail(trace_id: str):
    t = telemetry_pipeline.traces.get_trace(trace_id)
    if not t:
        raise HTTPException(status_code=404, detail="Trace ID not found")
    return t

# --- Incidents & Investigation ---

@app.get("/api/incidents")
def list_incidents(limit: int = 50) -> List[Incident]:
    return incident_manager.list_incidents(limit=limit)

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str) -> Incident:
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@app.post("/api/incidents/{incident_id}/investigate")
def investigate_incident(incident_id: str) -> StructuredDiagnosisOutput:
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_manager.update_status(incident_id, IncidentStatus.INVESTIGATING)
    diagnosis = investigation_agent.investigate(inc)
    
    # Update incident with root cause & candidates
    top_root = diagnosis.root_cause_candidates[0].component_id if diagnosis.root_cause_candidates else None
    incident_manager.update_status(incident_id, IncidentStatus.DIAGNOSED, root_cause=top_root)
    inc.candidates = diagnosis.root_cause_candidates

    incident_manager.add_timeline_event(
        incident_id=incident_id,
        event_type="DIAGNOSED",
        description=f"AI Investigation concluded: {diagnosis.summary}",
        actor="INVESTIGATION_AGENT"
    )

    return diagnosis

# --- Remediation & Safety Policy ---

@app.post("/api/incidents/{incident_id}/actions/propose")
def propose_remediation_action(
    incident_id: str,
    action_type: str,
    target_service: str,
    parameters: Optional[Dict[str, Any]] = None
) -> RemediationActionProposal:
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        proposal = policy_gate.validate_proposal(action_type, target_service, parameters or {})
        proposal.incident_id = incident_id
        remediation_executor.actions[proposal.action_id] = proposal

        incident_manager.update_status(incident_id, IncidentStatus.REMEDIATION_PROPOSED)
        incident_manager.add_timeline_event(
            incident_id=incident_id,
            event_type="ACTION_PROPOSED",
            description=f"Remediation proposed: {action_type} on {target_service} (Risk: {proposal.risk_level.value})",
            actor="POLICY_GATE"
        )
        return proposal
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/actions/{action_id}/approve")
def approve_action(action_id: str, approver: str = "Lead SRE Operator") -> RemediationActionProposal:
    action = remediation_executor.actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    try:
        policy_gate.approve_action(action, approver)
        incident_manager.add_timeline_event(
            incident_id=action.incident_id,
            event_type="ACTION_APPROVED",
            description=f"Action {action.action_type} approved by {approver}",
            actor=approver
        )
        return action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/actions/{action_id}/execute")
async def execute_and_verify_action(action_id: str):
    action = remediation_executor.actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    try:
        incident_manager.update_status(action.incident_id, IncidentStatus.REMEDIATING)
        executed_action = await remediation_executor.execute_action(action)
        
        # Grounded Post-Action Verification
        incident_manager.update_status(action.incident_id, IncidentStatus.VERIFYING)
        report = await remediation_executor.verify_recovery(executed_action, wait_seconds=1.0)
        
        return {
            "action": executed_action,
            "verification_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/actions/{action_id}/verification")
def get_verification_report(action_id: str):
    report = remediation_executor.verification_reports.get(action_id)
    if not report:
        raise HTTPException(status_code=404, detail="Verification report not found")
    return report

# --- Chaos & Fault Injection ---

@app.get("/api/chaos/scenarios")
def list_chaos_scenarios():
    return CHAOS_BENCHMARK_SCENARIOS

@app.get("/api/chaos/active")
def list_active_faults():
    return chaos_engine.list_active_faults()

@app.post("/api/chaos/inject")
def inject_fault(request: FaultInjectionRequest):
    fault = chaos_engine.inject_fault(request)
    
    # Trigger an immediate metric collection & incident creation
    snapshots = testbed.collect_service_metrics()
    anomalies = detector_manager.evaluate_services(snapshots)
    incident = None
    if anomalies:
        incident = incident_manager.create_incident_from_anomalies(
            anomalies,
            title_prefix=f"Injected Chaos ({request.fault_type.value})"
        )
        incident.ground_truth_fault_id = fault.fault_id
    
    return {
        "fault": fault,
        "incident": incident
    }

@app.post("/api/chaos/recover/{fault_id}")
def recover_fault(fault_id: str):
    success = chaos_engine.recover_fault(fault_id)
    return {"recovered": success, "fault_id": fault_id}

@app.post("/api/chaos/reset")
def reset_all_chaos():
    chaos_engine.reset_all()
    testbed.collect_service_metrics()
    return {"message": "All faults cleared; testbed reset to clean baseline"}

# --- Research Benchmarking Suite ---

@app.post("/api/benchmarks/run")
def run_benchmark(sample_size: int = Query(default=10, le=36)):
    scenarios_to_run = CHAOS_BENCHMARK_SCENARIOS[:sample_size]
    results = benchmark_evaluator.run_full_benchmark(scenarios=scenarios_to_run)
    return results

# --- Synthetic Traffic Toggle ---

@app.post("/api/traffic/toggle")
def toggle_traffic():
    if testbed.traffic_running:
        testbed.stop_traffic()
        state = "STOPPED"
    else:
        testbed.start_traffic()
        state = "RUNNING"
    return {"traffic_status": state}
