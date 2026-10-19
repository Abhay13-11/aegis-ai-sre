"""
Integration tests for AEGIS FastAPI REST endpoints.
Tests health, topology, telemetry, incident creation, investigations,
remediation proposals, approval, execution, and benchmarking.
"""

import os
os.environ["AEGIS_TESTING"] = "1"
import pytest
from fastapi.testclient import TestClient
from engine.main import app
from engine.models.schemas import IncidentSeverity

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "active_faults_count" in data
    assert "open_incidents_count" in data

def test_api_services_and_topology():
    res_svc = client.get("/api/services")
    assert res_svc.status_code == 200
    services = res_svc.json()
    assert "inventory_service" in services
    assert "api_gateway" in services

    res_topo = client.get("/api/topology")
    assert res_topo.status_code == 200
    topo = res_topo.json()
    assert "nodes" in topo
    assert "edges" in topo

    res_svc_topo = client.get("/api/services/inventory_service/topology")
    assert res_svc_topo.status_code == 200
    svc_topo = res_svc_topo.json()
    assert svc_topo["service_id"] == "inventory_service"
    assert "blast_radius" in svc_topo

def test_api_telemetry_queries():
    res_metrics = client.get("/api/telemetry/metrics?service_id=inventory_service&metric_name=p95_latency&window=60")
    assert res_metrics.status_code == 200
    stats = res_metrics.json()
    assert "mean" in stats

    res_logs = client.get("/api/telemetry/logs?limit=10")
    assert res_logs.status_code == 200
    assert isinstance(res_logs.json(), list)

    res_traces = client.get("/api/telemetry/traces?limit=10")
    assert res_traces.status_code == 200
    assert isinstance(res_traces.json(), list)

def test_api_incident_lifecycle_and_investigation():
    # 1. Create a test incident
    create_payload = {
        "title": "API Test Database Outage",
        "severity": "P1_CRITICAL",
        "affected_services": ["inventory_service", "order_service"],
        "description": "Simulated connection pool saturation"
    }
    res_create = client.post("/api/incidents", json=create_payload)
    assert res_create.status_code == 200
    inc = res_create.json()
    inc_id = inc["incident_id"]

    # 2. Get incident detail
    res_get = client.get(f"/api/incidents/{inc_id}")
    assert res_get.status_code == 200
    assert res_get.json()["incident_id"] == inc_id

    # 3. Get evidence
    res_ev = client.get(f"/api/incidents/{inc_id}/evidence")
    assert res_ev.status_code == 200
    assert "evidence_items" in res_ev.json()

    # 4. Trigger AI investigation
    res_inv = client.post(f"/api/incidents/{inc_id}/investigate")
    assert res_inv.status_code == 200
    diag = res_inv.json()
    assert diag["incident_id"] == inc_id
    assert "run_id" in diag
    assert len(diag["root_cause_candidates"]) > 0

    # 5. Fetch investigation by run_id
    res_run = client.get(f"/api/investigations/{diag['run_id']}")
    assert res_run.status_code == 200
    assert res_run.json()["run_id"] == diag["run_id"]

def test_api_remediation_workflow():
    # Propose an action for an incident
    inc_res = client.post("/api/incidents", json={
        "title": "Remediation Test Incident",
        "severity": "P2_HIGH",
        "affected_services": ["payment_service"]
    })
    inc_id = inc_res.json()["incident_id"]

    prop_res = client.post(f"/api/incidents/{inc_id}/actions", json={
        "action_type": "clear_redis_cache",
        "target_service": "payment_service",
        "parameters": {}
    })
    assert prop_res.status_code == 200
    action = prop_res.json()
    act_id = action["action_id"]

    # Action approval
    app_res = client.post(f"/api/actions/{act_id}/approve?approver=Lead_SRE")
    assert app_res.status_code == 200
    assert app_res.json()["state"] == "APPROVED"

    # Action execution
    exec_res = client.post(f"/api/actions/{act_id}/execute")
    assert exec_res.status_code == 200
    result = exec_res.json()
    assert "verification_report" in result

def test_api_chaos_and_benchmarks():
    # Scenarios list
    scn_res = client.get("/api/chaos/scenarios")
    assert scn_res.status_code == 200
    scenarios = scn_res.json()
    assert len(scenarios) >= 35

    # Run quick benchmark
    bench_res = client.post("/api/benchmarks/run?sample_size=3")
    assert bench_res.status_code == 200
    exp = bench_res.json()
    assert "experiment_id" in exp
    assert "summary" in exp

    # Get experiment results
    exp_res = client.get(f"/api/experiments/{exp['experiment_id']}/results")
    assert exp_res.status_code == 200
    assert exp_res.json()["experiment_id"] == exp["experiment_id"]

def test_api_audit_trail():
    audit_res = client.get("/api/audit?limit=20")
    assert audit_res.status_code == 200
    events = audit_res.json()
    assert isinstance(events, list)
    assert len(events) > 0
