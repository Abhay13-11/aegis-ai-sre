"""
AEGIS Benchmark Evaluation CLI
Runs scientific research evaluation across B1-B4, Full AEGIS, and Ablations.
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.testbed_manager import MicroservicesTestbed
from engine.telemetry import TelemetryPipeline
from engine.chaos import ChaosEngine, CHAOS_BENCHMARK_SCENARIOS
from engine.detectors import AnomalyDetectorManager
from engine.topology import DependencyGraph
from engine.rca import EvidenceFusionEngine, IncidentManager
from engine.agent import AgentToolRegistry, InvestigationAgent
from engine.remediation import PolicyGate, RemediationExecutorAndVerifier
from engine.benchmarks import BenchmarkEvaluator

def main():
    parser = argparse.ArgumentParser(description="Run AEGIS Research Benchmarking Suite")
    parser.add_argument("--samples", type=int, default=10, help="Number of scenarios to evaluate (max 36)")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Output JSON filename")
    args = parser.parse_args()

    print(f"\n[AEGIS Benchmark] Initializing evaluation stack across {args.samples} scenarios...")

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

    scenarios = CHAOS_BENCHMARK_SCENARIOS[:args.samples]
    results = evaluator.run_full_benchmark(scenarios=scenarios)

    print("\n" + "=" * 90)
    print(f"{'VARIANT':<25} | {'TOP-1 (%)':<10} | {'TOP-3 (%)':<10} | {'MRR':<8} | {'AVG LATENCY':<12} | {'SAFETY':<12}")
    print("=" * 90)
    for r in results["summary"]:
        print(f"{r['system_variant']:<25} | {r['top_1_accuracy_percent']:<10.1f} | {r['top_3_accuracy_percent']:<10.1f} | {r['mrr']:<8.3f} | {r['avg_diagnosis_time_ms']:<7.1f} ms | {r['unsafe_actions_prevented_percent']}%")
    print("=" * 90)

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[AEGIS Benchmark] Full detailed results exported to {args.output}\n")

if __name__ == '__main__':
    main()
