"""
Research benchmark and baseline evaluation tests.
Verifies evaluation of B1-B4, Full AEGIS, and ablation studies
across controlled chaos scenarios.
"""

import pytest
from services.testbed_manager import MicroservicesTestbed
from engine.telemetry import TelemetryPipeline
from engine.chaos import ChaosEngine, CHAOS_BENCHMARK_SCENARIOS
from engine.detectors import AnomalyDetectorManager
from engine.topology import DependencyGraph
from engine.rca import EvidenceFusionEngine, IncidentManager
from engine.agent import AgentToolRegistry, InvestigationAgent
from engine.remediation import PolicyGate, RemediationExecutorAndVerifier
from engine.benchmarks import BenchmarkEvaluator

@pytest.fixture
def evaluator_stack():
    telemetry = TelemetryPipeline()
    testbed = MicroservicesTestbed(telemetry_pipeline=telemetry)
    graph = DependencyGraph()
    chaos = ChaosEngine(testbed=testbed)
    detectors = AnomalyDetectorManager(metrics_collector=telemetry.metrics)
    fusion = EvidenceFusionEngine(dependency_graph=graph, trace_store=telemetry.traces)
    inc_manager = IncidentManager(fusion_engine=fusion, dependency_graph=graph, telemetry_pipeline=telemetry)
    tools = AgentToolRegistry(dependency_graph=graph, telemetry_pipeline=telemetry, testbed=testbed)
    agent = InvestigationAgent(tool_registry=tools, fusion_engine=fusion)
    policy = PolicyGate()
    executor = RemediationExecutorAndVerifier(testbed=testbed, incident_manager=inc_manager, telemetry_pipeline=telemetry)

    evaluator = BenchmarkEvaluator(
        testbed=testbed,
        chaos_engine=chaos,
        detector_manager=detectors,
        fusion_engine=fusion,
        graph=graph,
        agent=agent,
        policy_gate=policy,
        executor=executor
    )
    return evaluator

def test_benchmark_evaluator_single_scenario(evaluator_stack):
    scenario = CHAOS_BENCHMARK_SCENARIOS[0] # PostgreSQL Pool Exhaustion
    res = evaluator_stack.evaluate_scenario(scenario, variant="FULL_AEGIS")
    assert res["scenario_id"] == "SCN-DB-01"
    assert res["ground_truth_root"] == "inventory_service"
    assert res["top_1"] is True
    assert res["reciprocal_rank"] == 1.0

def test_benchmark_evaluator_variants_and_ablations(evaluator_stack):
    scenario = CHAOS_BENCHMARK_SCENARIOS[0]
    res_b1 = evaluator_stack.evaluate_scenario(scenario, variant="B1_RULE_BASED")
    assert "rank" in res_b1

    res_b4 = evaluator_stack.evaluate_scenario(scenario, variant="B4_TELEMETRY_GRAPH")
    assert "top_1" in res_b4

    res_abl = evaluator_stack.evaluate_scenario(scenario, variant="ABLATION_NO_GRAPH")
    assert "reciprocal_rank" in res_abl

def test_benchmark_full_summary(evaluator_stack):
    subset = CHAOS_BENCHMARK_SCENARIOS[:3]
    result = evaluator_stack.run_full_benchmark(scenarios=subset)
    summary = result["summary"]
    assert len(summary) >= 5
    variants = [row["system_variant"] for row in summary]
    assert "FULL_AEGIS" in variants
    assert "B1_RULE_BASED" in variants
    for row in summary:
        assert 0.0 <= row["mrr"] <= 1.0
        assert 0.0 <= row["top_1_accuracy_percent"] <= 100.0
