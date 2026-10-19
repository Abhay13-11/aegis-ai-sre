# AEGIS — AI-Enhanced Guided Investigation System

> Autonomous Root Cause Analysis & Remediation Engine for Microservices

[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## Overview

AEGIS is a full-stack simulated microservices observability platform that demonstrates **automated incident detection, root cause analysis (RCA), and safe remediation**. It combines graph-based topology analysis, multi-modal evidence fusion, chaos engineering, and an AI investigation agent into a complete incident lifecycle loop.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AEGIS System Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │   API    │──▶│  Order   │──▶│Inventory │──▶│PostgreSQL│     │
│  │ Gateway  │   │ Service  │   │ Service  │   │  (Pool)  │     │
│  └──────────┘   └────┬─────┘   └──────────┘   └──────────┘     │
│                      │                                           │
│                      ▼                                           │
│                 ┌──────────┐   ┌──────────┐                     │
│                 │ Payment  │──▶│  Redis   │                     │
│                 │ Service  │   │ (Cache)  │                     │
│                 └──────────┘   └──────────┘                     │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  User    │  (Auth / Token Validation)                        │
│  │ Service  │                                                    │
│  └──────────┘                                                    │
├─────────────────────────────────────────────────────────────────┤
│  Telemetry Pipeline │ Chaos Engine │ Detectors │ RCA │ Agent    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 🔍 Multi-Signal Telemetry Pipeline
- **Metrics Collector** — Time-series storage with statistical queries (mean, p95, stddev)
- **Log Store** — Structured log ingestion with filtered search and error retrieval
- **Trace Store** — Distributed trace indexing with bottleneck span identification

### 🗺️ Service Dependency Graph (DSA Algorithms)
- **BFS/DFS** traversal for upstream/downstream discovery
- **Blast radius** computation with impact scoring
- **Shortest propagation path** (BFS) from root cause to symptom
- **Topological relevance ranking** for RCA candidate scoring

### 🧮 Evidence Fusion RCA Engine
Multi-modal weighted scoring formula:

$$\text{RootCauseScore} = 0.30 \cdot S_{dep} + 0.25 \cdot S_{temporal} + 0.20 \cdot S_{severity} + 0.15 \cdot S_{trace} + 0.10 \cdot S_{history}$$

| Factor | Weight | Description |
|--------|--------|-------------|
| Dependency Relevance | 30% | Topological graph reachability coverage |
| Temporal Correlation | 25% | Exponential decay based on anomaly onset time |
| Anomaly Severity | 20% | Weighted severity (CRITICAL > HIGH > MEDIUM > LOW) |
| Trace Propagation | 15% | Bottleneck span concentration in error traces |
| Historical Similarity | 10% | Past incident pattern matching |

### 🔴 Anomaly Detectors
| Detector | Type | Method |
|----------|------|--------|
| Rule-Based | Threshold | Static thresholds on error rate, latency, CPU |
| Z-Score | Statistical | Standard deviation from rolling mean |
| MAD | Statistical | Median Absolute Deviation (outlier-robust) |
| Isolation Forest | ML | Multivariate anomaly scoring via scikit-learn |

### 💥 Chaos Engineering
8 injectable fault types:
- DB Latency / DB Pool Exhaustion
- Redis Failure
- CPU Spike / Memory Leak
- Network Delay / Service Crash
- Bad Config / Cascading Failure

### 🤖 AI Investigation Agent
- Bounded tool-calling (max 10 calls per investigation)
- Read-only scoped tools: graph queries, metric stats, logs, traces, deployments
- Schema-validated `StructuredDiagnosisOutput` with uncertainty notes
- Evidence-grounded root cause ranking

### 🛡️ Safe Remediation
- **Policy Gate** — Risk classification (LOW/MEDIUM/HIGH), approval workflow
- **Sandboxed Executor** — Allowlisted actions only (pool tuning, cache clear, restart, scale, rollback)
- **Grounded Verifier** — Post-action telemetry re-sampling with threshold checks

## Project Structure

```
majorproject/
├── engine/
│   ├── agent/              # LLM Investigation Agent & Tools
│   ├── benchmarks/         # Evaluation framework
│   ├── chaos/              # Fault injection engine
│   ├── detectors/          # Anomaly detection (rule, z-score, MAD, iforest)
│   ├── models/             # Pydantic schemas & data models
│   ├── rca/                # Evidence fusion & incident management
│   ├── remediation/        # Policy gate, executor, verifier
│   ├── telemetry/          # Metrics, logs, traces pipeline
│   └── topology/           # Dependency graph & DSA algorithms
├── services/
│   └── testbed_manager.py  # Simulated 5-service microservices testbed
├── tests/                  # 15 comprehensive pytest tests
├── docs/                   # PRD & Project Bible
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# Clone
git clone https://github.com/<your-username>/majorproject.git
cd majorproject

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v
```

### Expected Output
```
tests/test_agent.py::test_agent_tool_registry PASSED
tests/test_agent.py::test_agent_investigation_workflow_and_schema_validation PASSED
tests/test_chaos_e2e.py::test_end_to_end_aegis_investigation_and_recovery_loop PASSED
tests/test_detectors.py::test_rule_based_detector_triggers_on_high_error_rate PASSED
tests/test_detectors.py::test_z_score_detector PASSED
tests/test_detectors.py::test_mad_detector PASSED
tests/test_detectors.py::test_isolation_forest_detector PASSED
tests/test_evidence_fusion.py::test_evidence_fusion_weights_and_ranking PASSED
tests/test_remediation.py::test_policy_gate_blocks_forbidden_and_dangerous_actions PASSED
tests/test_remediation.py::test_policy_gate_risk_classification_and_approval PASSED
tests/test_remediation.py::test_remediation_execution_and_telemetry_verification PASSED
tests/test_topology.py::test_dependency_graph_topology PASSED
tests/test_topology.py::test_blast_radius_computation PASSED
tests/test_topology.py::test_shortest_propagation_path PASSED
tests/test_topology.py::test_topological_relevance_scoring PASSED

15 passed
```

## Test Coverage

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| `test_topology.py` | 4 | Graph BFS/DFS, blast radius, shortest path, relevance scoring |
| `test_detectors.py` | 4 | Rule-based, Z-Score, MAD, Isolation Forest anomaly detection |
| `test_evidence_fusion.py` | 1 | Multi-factor RCA scoring and candidate ranking |
| `test_remediation.py` | 3 | Policy gate, risk classification, execution & verification |
| `test_agent.py` | 2 | Tool registry, full investigation workflow |
| `test_chaos_e2e.py` | 1 | **Full lifecycle**: Healthy → Chaos → Detect → RCA → Investigate → Remediate → Verify |

## E2E Lifecycle Flow

```
1. Healthy Baseline    → All 5 services report HEALTHY status
2. Chaos Injection     → DB Pool Exhaustion on inventory_service
3. Traffic Generation  → Gateway transactions manifest cascading errors
4. Anomaly Detection   → Rule-based & ML detectors trigger alerts
5. Incident Creation   → Evidence fusion ranks inventory_service as root cause
6. AI Investigation    → Agent queries traces, logs, metrics to confirm diagnosis
7. Policy Gate         → High-risk action requires human approval
8. Remediation         → Pool limit tuned, queue flushed
9. Verification        → Fresh telemetry confirms recovery (latency, error rate, DB queue)
10. Resolution         → Incident status transitions to RESOLVED
```

## Requirements

- Python 3.12+
- FastAPI, Uvicorn
- Pydantic v2
- scikit-learn
- pytest, pytest-asyncio

## License

MIT
