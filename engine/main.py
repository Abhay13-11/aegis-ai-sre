"""
AEGIS AI-SRE Core Platform Backend
FastAPI server exposing all REST APIs for topology, telemetry,
incidents, agent investigation, remediation policy, and research benchmarks.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List, Optional
import time
import asyncio
import uuid
import os

from engine.models.schemas import (
    ServiceSnapshot,
    FaultInjectionRequest,
    ActiveFault,
    Incident,
    IncidentStatus,
    IncidentSeverity,
    StructuredDiagnosisOutput,
    RemediationActionProposal,
    VerificationReport,
    ActionState,
    ManualIncidentCreateRequest,
    ActionProposeRequest,
    AuditEvent,
    AnomalyEvent,
    AnomalySeverity,
    SignalType,
    EvidenceItem
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
from contextlib import asynccontextmanager

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

# --- Audit & Result Registries ---
investigations_store: Dict[str, StructuredDiagnosisOutput] = {}
experiments_store: Dict[str, Dict[str, Any]] = {}
audit_log_store: List[AuditEvent] = []

def record_audit_event(actor: str, event_type: str, entity_id: str, details: Dict[str, Any] = None) -> AuditEvent:
    evt = AuditEvent(
        actor=actor,
        event_type=event_type,
        entity_id=entity_id,
        details=details or {}
    )
    audit_log_store.append(evt)
    return evt

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
                    new_inc = incident_manager.create_incident_from_anomalies(anomalies)
                    record_audit_event(
                        actor="DETECTOR_MANAGER",
                        event_type="INCIDENT_TRIGGERED",
                        entity_id=new_inc.incident_id,
                        details={"affected": new_inc.affected_services, "anomalies_count": len(anomalies)}
                    )
        except Exception:
            pass
        await asyncio.sleep(2.0)

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    global _background_loop_task
    if os.environ.get("AEGIS_TESTING") != "1":
        testbed.start_traffic()
        record_audit_event("SYSTEM", "STARTUP", "aegis_core", {"version": "1.0.0", "traffic": "STARTED"})
        _background_loop_task = asyncio.create_task(system_monitoring_loop())
    yield
    if os.environ.get("AEGIS_TESTING") != "1":
        testbed.stop_traffic()
        record_audit_event("SYSTEM", "SHUTDOWN", "aegis_core", {"traffic": "STOPPED"})
        if _background_loop_task:
            _background_loop_task.cancel()

app = FastAPI(
    title="AEGIS AI-SRE Intelligence Platform",
    description="Evidence-Grounded AI-SRE for Microservice Incident Diagnosis & Safe Remediation",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/services/{service_id}/topology")
def get_service_topology(service_id: str):
    if service_id not in dependency_graph.nodes and service_id not in testbed.services:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "service_id": service_id,
        "dependencies": dependency_graph.get_dependencies(service_id),
        "dependents": dependency_graph.get_dependents(service_id),
        "all_downstream": dependency_graph.get_all_downstream_dependencies(service_id),
        "all_upstream_impacted": dependency_graph.get_all_upstream_impacted(service_id),
        "blast_radius": dependency_graph.compute_blast_radius(service_id)
    }

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

@app.post("/api/incidents")
def create_manual_incident(request: ManualIncidentCreateRequest) -> Incident:
    """Manual/test incident trigger for operator evaluation (FR-005, PRD Section 12)."""
    # Create synthetic anomalies for requested services
    anomalies: List[AnomalyEvent] = []
    for svc in request.affected_services:
        anomalies.append(
            AnomalyEvent(
                service_id=svc,
                detector_type="MANUAL_OPERATOR",
                metric_name="p95_latency",
                current_value=850.0,
                expected_value=45.0,
                deviation_score=0.88,
                severity=AnomalySeverity.HIGH,
                summary=f"Manual operator alert simulated for {svc}: {request.description}"
            )
        )
    inc = incident_manager.create_incident_from_anomalies(anomalies, title_prefix=request.title)
    record_audit_event(
        actor="OPERATOR",
        event_type="MANUAL_INCIDENT_CREATED",
        entity_id=inc.incident_id,
        details={"title": request.title, "affected": request.affected_services}
    )
    return inc

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str) -> Incident:
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@app.get("/api/incidents/{incident_id}/evidence")
def get_incident_evidence(incident_id: str):
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "incident_id": incident_id,
        "evidence_items": inc.evidence_items,
        "candidates": inc.candidates,
        "blast_radius": inc.blast_radius
    }

@app.post("/api/incidents/{incident_id}/investigate")
def investigate_incident(incident_id: str) -> StructuredDiagnosisOutput:
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_manager.update_status(incident_id, IncidentStatus.INVESTIGATING)
    diagnosis = investigation_agent.investigate(inc)
    
    # Store investigation run
    investigations_store[diagnosis.run_id] = diagnosis

    # Update incident with root cause & candidates
    top_root = diagnosis.root_cause_candidates[0].component_id if diagnosis.root_cause_candidates else None
    incident_manager.update_status(incident_id, IncidentStatus.DIAGNOSED, root_cause=top_root)
    inc.candidates = diagnosis.root_cause_candidates

    incident_manager.add_timeline_event(
        incident_id=incident_id,
        event_type="DIAGNOSED",
        description=f"AI Investigation concluded: {diagnosis.summary}",
        actor="INVESTIGATION_AGENT",
        metadata={"run_id": diagnosis.run_id, "top_root": top_root}
    )

    record_audit_event(
        actor="INVESTIGATION_AGENT",
        event_type="INVESTIGATION_CONCLUDED",
        entity_id=diagnosis.run_id,
        details={"incident_id": incident_id, "root_cause": top_root, "status": diagnosis.status}
    )

    return diagnosis

@app.get("/api/investigations/{run_id}")
def get_investigation_run(run_id: str) -> StructuredDiagnosisOutput:
    run = investigations_store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    return run

# --- Remediation & Safety Policy ---

@app.post("/api/incidents/{incident_id}/actions/propose")
@app.post("/api/incidents/{incident_id}/actions")
def propose_remediation_action(
    incident_id: str,
    proposal_req: ActionProposeRequest
) -> RemediationActionProposal:
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        proposal = policy_gate.validate_proposal(proposal_req.action_type, proposal_req.target_service, proposal_req.parameters)
        proposal.incident_id = incident_id
        remediation_executor.actions[proposal.action_id] = proposal

        incident_manager.update_status(incident_id, IncidentStatus.REMEDIATION_PROPOSED)
        incident_manager.add_timeline_event(
            incident_id=incident_id,
            event_type="ACTION_PROPOSED",
            description=f"Remediation proposed: {proposal_req.action_type} on {proposal_req.target_service} (Risk: {proposal.risk_level.value})",
            actor="POLICY_GATE"
        )

        record_audit_event(
            actor="POLICY_GATE",
            event_type="ACTION_PROPOSED",
            entity_id=proposal.action_id,
            details={"type": proposal_req.action_type, "target": proposal_req.target_service, "risk": proposal.risk_level.value}
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
        record_audit_event(
            actor=approver,
            event_type="ACTION_APPROVED",
            entity_id=action_id,
            details={"action_type": action.action_type, "target": action.target_service}
        )
        return action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/actions/{action_id}/reject")
def reject_action(action_id: str, reason: str = "Operator rejected proposal", rejector: str = "Lead SRE Operator"):
    action = remediation_executor.actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    policy_gate.reject_action(action, reason)
    incident_manager.add_timeline_event(
        incident_id=action.incident_id,
        event_type="ACTION_REJECTED",
        description=f"Action {action.action_type} rejected: {reason}",
        actor=rejector
    )
    record_audit_event(
        actor=rejector,
        event_type="ACTION_REJECTED",
        entity_id=action_id,
        details={"reason": reason}
    )
    return action

@app.post("/api/actions/{action_id}/execute")
async def execute_and_verify_action(action_id: str):
    action = remediation_executor.actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    try:
        incident_manager.update_status(action.incident_id, IncidentStatus.REMEDIATING)
        record_audit_event(
            actor=action.approved_by or "SYSTEM",
            event_type="ACTION_EXECUTING",
            entity_id=action_id,
            details={"action_type": action.action_type, "target": action.target_service}
        )
        
        executed_action = await remediation_executor.execute_action(action)
        
        # Grounded Post-Action Verification
        incident_manager.update_status(action.incident_id, IncidentStatus.VERIFYING)
        report = await remediation_executor.verify_recovery(executed_action, wait_seconds=1.0)
        
        record_audit_event(
            actor="REMEDIATION_VERIFIER",
            event_type="RECOVERY_VERIFIED" if report.overall_recovery_verified else "RECOVERY_UNVERIFIED",
            entity_id=report.verification_id,
            details={"recovered": report.overall_recovery_verified, "summary": report.summary}
        )

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
    
    record_audit_event(
        actor="CHAOS_ENGINE",
        event_type="FAULT_INJECTED",
        entity_id=fault.fault_id,
        details={"type": request.fault_type.value, "target": request.target_service}
    )

    return {
        "fault": fault,
        "incident": incident
    }

@app.post("/api/chaos/recover/{fault_id}")
def recover_fault(fault_id: str):
    success = chaos_engine.recover_fault(fault_id)
    record_audit_event(
        actor="CHAOS_ENGINE",
        event_type="FAULT_RECOVERED",
        entity_id=fault_id,
        details={"success": success}
    )
    return {"recovered": success, "fault_id": fault_id}

@app.post("/api/chaos/reset")
def reset_all_chaos():
    chaos_engine.reset_all()
    testbed.collect_service_metrics()
    record_audit_event("CHAOS_ENGINE", "ALL_FAULTS_RESET", "testbed", {})
    return {"message": "All faults cleared; testbed reset to clean baseline"}

# --- Research Benchmarking & Experiments Suite ---

@app.post("/api/benchmarks/run")
@app.post("/api/experiments")
def run_benchmark(sample_size: int = Query(default=10, le=36)):
    """Executes scientific evaluation across B1-B4, Full AEGIS, and ablations (PRD Section 12 & 15)."""
    scenarios_to_run = CHAOS_BENCHMARK_SCENARIOS[:sample_size]
    results = benchmark_evaluator.run_full_benchmark(scenarios=scenarios_to_run)
    
    experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
    experiment_record = {
        "experiment_id": experiment_id,
        "sample_size": sample_size,
        "created_at": time.time(),
        "summary": results.get("summary", []),
        "detailed_runs": results.get("detailed_runs", {})
    }
    experiments_store[experiment_id] = experiment_record

    record_audit_event(
        actor="BENCHMARK_EVALUATOR",
        event_type="EXPERIMENT_COMPLETED",
        entity_id=experiment_id,
        details={"scenarios_count": sample_size}
    )

    return experiment_record

@app.get("/api/experiments")
def list_experiments():
    return list(experiments_store.values())

@app.get("/api/experiments/{experiment_id}/results")
def get_experiment_results(experiment_id: str):
    exp = experiments_store.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

# --- Audit Events ---

@app.get("/api/audit")
def get_audit_trail(limit: int = 100, event_type: Optional[str] = None):
    results = audit_log_store
    if event_type:
        results = [e for e in results if e.event_type == event_type]
    return results[-limit:]

# --- Synthetic Traffic Toggle ---

@app.post("/api/traffic/toggle")
def toggle_traffic():
    if testbed.traffic_running:
        testbed.stop_traffic()
        state = "STOPPED"
    else:
        testbed.start_traffic()
        state = "RUNNING"
    record_audit_event("OPERATOR", "TRAFFIC_TOGGLE", "traffic_generator", {"state": state})
    return {"traffic_status": state}

# Serve web static assets if built
_dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")
_assets_dir = os.path.join(_dist_dir, "assets")

if os.path.isdir(_assets_dir):
    try:
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")
    except Exception as e:
        print(f"[WARN] StaticFiles mount for /assets skipped: {e}", flush=True)

from fastapi.responses import HTMLResponse

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
    index_file = os.path.join(_dist_dir, "index.html")
    if os.path.isfile(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except Exception:
            pass
    return {"message": "AEGIS AI-SRE Platform API running."}
