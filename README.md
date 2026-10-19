# AEGIS — Adaptive Evidence-Grounded Incident Intelligence & Safe-Remediation System

> **Evidence-Grounded AI-SRE for Microservice Incident Diagnosis & Safe Remediation**
> 
> *Core Principle: The LLM is an investigator, not the source of truth.*

[![Tests](https://img.shields.io/badge/tests-28%2F28%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)]()
[![Frontend](https://img.shields.io/badge/frontend-React%2018%20%7C%20Vite%20%7C%20Tailwind-purple)]()
[![Docker](https://img.shields.io/badge/docker-ready-2496ed)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 📖 Executive Summary

**AEGIS** is a full-stack, web-based AI Site Reliability Engineering (AI-SRE) platform designed to diagnose incidents in distributed microservice architectures and safely verify recovery.

Distributed microservices produce cascading operational signals across boundaries. When a symptom surfaces at the API Gateway, manual diagnosis requires correlating timestamps, logs, metrics, distributed traces, and dependency graphs. 

AEGIS provides an autonomous, deterministic, and verifiable end-to-end loop:
1. **Observe** — Collects metrics, structured logs, and distributed traces with OpenTelemetry-style trace IDs.
2. **Detect** — Employs Multi-Detector Anomaly Engine (Rules, Z-Score, Median Absolute Deviation, and Multivariate Isolation Forest).
3. **Correlate & Rank** — Applies Directed Dependency Graph DSA algorithms (BFS/DFS, blast radius) and 5-factor Evidence Fusion to rank root causes independently of any LLM.
4. **Investigate** — AI-SRE Investigation Agent inspects evidence through bounded, read-only tools and emits schema-validated diagnoses with quantified uncertainty.
5. **Gate & Remediate** — Strict Policy Gate enforces allowlisted actions, risk classification (LOW/MEDIUM/HIGH), and authorized human approval before sandboxed execution.
6. **Verify** — Post-action telemetry verification samples fresh operational metrics against defined thresholds before marking incidents resolved.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                AEGIS System Architecture                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐    ┌────────────────┐  │
│  │  API Gateway   │───▶│ Order Service  │───▶│Inventory Service───▶│   PostgreSQL   │  │
│  │ (Port 8000/API)│    │                │    │                │    │(Connection Pool│  │
│  └───────┬────────┘    └───────┬────────┘    └────────────────┘    └────────────────┘  │
│          │                     │                                                       │
│          ▼                     ▼                                                       │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐                        │
│  │  User Service  │    │ Payment Service│───▶│  Redis Cache   │                        │
│  │ (Auth / Token) │    │                │    │(Idempotency)   │                        │
│  └────────────────┘    └────────────────┘    └────────────────┘                        │
│                                                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Observability │ Anomaly Detectors │ Topology Graph │ Evidence Fusion │ Policy Gate    │
│ Traces / Logs │ Rule, Z-Score, MAD│ BFS, Shortest  │ Multi-factor    │ Approval Barrier│
│ Metrics Store │ Isolation Forest  │ Blast Radius   │ Scoring Formula │ Sandboxed Exec │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                       Modern Web Dashboard (React + TypeScript + Vite)                 │
│ Overview • Topology • Incidents & Timeline • Evidence Explorer • AI Console • Chaos   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Architectural Modules & Features

### 1. 🔍 Multi-Signal Telemetry Pipeline
- **Metrics Store** — In-memory time-series collector with rolling statistics (mean, p95 latency, stddev, min, max).
- **Log Store** — Structured log indexing with level filtering (`INFO`, `WARN`, `ERROR`, `FATAL`), keyword search, and trace correlation.
- **Trace Store** — Distributed trace indexing with span hierarchy, duration waterfalls, status codes, and automatic identification of deepest bottleneck spans.

### 2. 🗺️ Directed Service Topology Graph (DSA Algorithms)
- **Directed Graph Adjacency** — Forward (callees) and backward (callers) adjacency lists.
- **BFS / DFS Traversal** — Transitive downstream dependency discovery.
- **Topological Blast Radius** — Immediate upstream caller impact propagation and blast radius score.
- **Shortest Propagation Path** — BFS path from root failure to symptom.
- **Topological Relevance Ranking** — Quantifies structural proximity to anomalous services.

### 3. 🧮 Evidence Fusion Root Cause Analysis Engine
Deterministic multi-modal weighted scoring formula:

$$\text{RootCauseScore} = 0.30 \cdot S_{\text{dep}} + 0.25 \cdot S_{\text{temporal}} + 0.20 \cdot S_{\text{severity}} + 0.15 \cdot S_{\text{trace}} + 0.10 \cdot S_{\text{history}}$$

| Component | Weight | Mathematical Methodology |
|:---|:---:|:---|
| **$S_{\text{dep}}$ (Dependency Relevance)** | 30% | Graph reachability and blast radius coverage |
| **$S_{\text{temporal}}$ (Temporal Precedence)** | 25% | Exponential decay based on earliest anomaly onset: $e^{-\Delta t / 30}$ |
| **$S_{\text{severity}}$ (Anomaly Severity)** | 20% | Weighted severity (`CRITICAL`: 1.0, `HIGH`: 0.75, `MEDIUM`: 0.50, `LOW`: 0.25) |
| **$S_{\text{trace}}$ (Trace Propagation)** | 15% | Concentration of bottleneck spans in slow/error traces |
| **$S_{\text{history}}$ (Historical Pattern)** | 10% | Recurrence pattern matching |

### 4. 🤖 AI-SRE Investigation Agent
- **Strictly Bounded** — Max 10 tool calls per investigation run; guardrailed budgets.
- **Read-Only Scope** — `get_service_graph`, `get_metric`, `get_logs`, `get_trace`, `get_recent_deployments`, `get_incident_history`.
- **Structured Output** — Schema-validated JSON (`schema_version: "1.0"`) with ranked candidates, recommended allowlisted action, and explicit uncertainty notes.
- **Status Accounting** — Emits `diagnosed` or `needs_human_review`.

### 5. 🛡️ Safe Remediation & Grounded Verification
- **Explicit Action Allowlist** — `tune_connection_pool_limit`, `clear_redis_cache`, `restart_service`, `scale_replicas`, `rollback_deployment`, `inspect_connection_pool`.
- **Injection Prevention** — Rejects command injection, SQL injection (`rm -rf`, `drop table`, `exec`, `bash`).
- **Human Approval Barrier** — State-changing actions mandate authorized human approval (`ActionRiskLevel.HIGH` / `MEDIUM`).
- **State Machine Enforcer**:
  $$\text{PROPOSED} \longrightarrow \text{PENDING\_APPROVAL} \longrightarrow \text{APPROVED / REJECTED} \longrightarrow \text{EXECUTING} \longrightarrow \text{VERIFYING} \longrightarrow \text{VERIFIED\_RECOVERED / NOT\_RECOVERED}$$
- **Post-Action Telemetry Verification** — Re-samples metrics after remediation and requires threshold satisfaction (e.g. latency $\le 100\text{ms}$, error rate $\le 2\%$, DB pool queue cleared) before resolving.

### 6. 💥 Chaos Engineering & Research Benchmarks
- **35+ Controlled Incident Scenarios** across 5 categories:
  - Database Incidents (Pool Exhaustion, Lock Contention, Query Latency, Replica Lag)
  - Cache Incidents (Redis Outage, Timeout Cascade, Memory Pressure)
  - Compute & Process (CPU Thrashing, Memory Leak)
  - Network & Infrastructure (Service Crash, Inter-service Delays)
  - Configuration & Cascades (Invalid Configuration Rollout, Cascading Failure)
- **Comparative Research Evaluation**:
  - **B1**: Rule/Threshold-based baseline
  - **B2**: Telemetry-only LLM baseline
  - **B3**: Telemetry + Historical RAG baseline
  - **B4**: Telemetry + Graph Topology baseline
  - **Full AEGIS**: Multimodal Evidence Fusion + Bounded AI Agent
  - **Ablation Studies**: No Graph ($w_{\text{dep}}=0$), No Temporal ($w_{\text{temporal}}=0$)
- **Evaluation Metrics Computed**: Top-1 Accuracy (%), Top-3 Accuracy (%), Mean Reciprocal Rank (MRR), Average Diagnosis Latency, Unsafe Actions Blocked (%).

---

## 💻 Modern Web Dashboard

The web dashboard is built with **React 18, TypeScript, Vite, and Tailwind CSS**:

1. **Overview Dashboard** — Cluster status, traffic generator toggle, service health cards with latency/error/CPU badges, quick chaos launchers, active alerts queue.
2. **Service Topology** — Interactive SVG diagram of the 5 microservices + PostgreSQL + Redis with animated dependency edges, health color indicators, and click-to-inspect blast radius panel.
3. **Incidents & Timeline** — Filterable incident list, root-cause diagnosis cards, and chronological lifecycle timeline.
4. **Evidence Explorer** — Tabbed multi-signal telemetry viewer:
   - *Metrics*: Statistical breakdown (p95, mean, min, max, stddev).
   - *Logs*: Filterable log stream with log level selector and keyword search.
   - *Traces*: Distributed trace waterfall visualizer showing bottleneck spans and latencies.
5. **AI Investigation Console** — Displays agent findings, 5-factor evidence fusion score breakdown bars, supporting/contradicting evidence badges, bounded tool calls list, uncertainty notes, and raw schema JSON.
6. **Safe Remediation Console** — Remediation action proposals, risk badges, human approval/rejection controls, sandbox execution trigger, and post-action verification checks table.
7. **Chaos Engineering Lab** — Interactive catalog of 35+ scenarios, 1-click injection, active faults table with instant recovery, and global reset button.
8. **Research Benchmarking Suite** — Run scientific benchmark evaluation (5 to 36 scenarios), view comparative accuracy/MRR table, and export results to JSON.
9. **Audit Trail** — Append-only chronological audit log of all system decisions, approvals, and state changes.

---

## 🚀 Quick Start

### Option 1: Local Python & Node Setup

```bash
# 1. Clone repository
git clone https://github.com/your-username/majorproject.git
cd majorproject

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Build Web Dashboard (already pre-built in web/dist)
cd web
npm install
npm run build
cd ..

# 4. Start AEGIS Platform (Unified Backend & Web Dashboard on Port 8000)
python scripts/run_platform.py
```
Open **`http://localhost:8000`** in your browser.

---

### Option 2: Docker Compose (PRD AC-01 Compliant)

```bash
docker-compose up --build
```
Open **`http://localhost:8000`** in your browser.

---

## 🧪 Automated Test Suite (28 / 28 Passing)

AEGIS includes a comprehensive, multi-level test suite covering unit logic, DSA graph algorithms, anomaly detectors, FastAPI REST APIs, research benchmarks, and negative safety gates:

```bash
python -m pytest -v
```

### Test Coverage Table:

| Test File | Tests | Coverage Area |
|:---|:---:|:---|
| `test_topology.py` | 4 | Dependency graph BFS/DFS, blast radius computation, shortest propagation path, topological relevance scoring |
| `test_detectors.py` | 4 | Rule-based detector, Z-Score detector, MAD detector, Isolation Forest ML detector |
| `test_evidence_fusion.py` | 1 | Multi-factor evidence fusion weights and candidate ranking |
| `test_agent.py` | 2 | Agent tool registry bounds, investigation workflow, and `StructuredDiagnosisOutput` validation |
| `test_remediation.py` | 3 | Allowlist filtering, risk level classification, approval gates, sandbox execution, telemetry verification |
| `test_safety_negative.py` | 3 | Blocking unapproved execution, SQL/command injection prevention, rejection of forbidden actions |
| `test_api.py` | 7 | FastAPI endpoints: health, topology, telemetry, manual incidents, investigation, remediation, chaos, audit trail |
| `test_benchmarks.py` | 3 | Research evaluator, Baselines B1–B4, Ablation studies, MRR calculation |
| `test_chaos_e2e.py` | 1 | **Full E2E Lifecycle**: Healthy $\to$ Chaos Injection $\to$ Detection $\to$ Correlated RCA $\to$ AI Investigation $\to$ Approved Remediation $\to$ Verified Recovery |
| **Total** | **28** | **100% Passing** |

---

## 🔬 CLI Benchmark Runner

Run scientific research benchmarks directly from terminal:

```bash
python scripts/run_benchmarks.py --samples 10 --output benchmark_results.json
```

Example Output:
```
==========================================================================================
VARIANT                   | TOP-1 (%)  | TOP-3 (%)  | MRR      | AVG LATENCY  | SAFETY      
==========================================================================================
B1_RULE_BASED             | 70.0       | 90.0       | 0.783    | 0.1     ms   | 0.0%
B2_TELEMETRY_ONLY_LLM     | 60.0       | 80.0       | 0.717    | 0.1     ms   | 0.0%
B3_TELEMETRY_RAG          | 70.0       | 90.0       | 0.800    | 0.1     ms   | 0.0%
B4_TELEMETRY_GRAPH        | 80.0       | 100.0      | 0.867    | 0.2     ms   | 0.0%
FULL_AEGIS                | 100.0      | 100.0      | 1.000    | 0.9     ms   | 100.0%
ABLATION_NO_GRAPH         | 80.0       | 90.0       | 0.850    | 0.7     ms   | 100.0%
ABLATION_NO_TEMPORAL      | 90.0       | 100.0      | 0.933    | 0.7     ms   | 100.0%
==========================================================================================
```

---

## 📡 REST API Reference

| Method | Path | Purpose |
|:---|:---|:---|
| `GET` | `/api/health` | System health, traffic status, fault counts, open incident count |
| `GET` | `/api/services` | Service snapshots, status, p95 latency, error rates, CPU |
| `GET` | `/api/topology` | Directed graph nodes and dependency edges |
| `GET` | `/api/services/{id}/topology` | Service inbound callees, outbound callers, and blast radius |
| `GET` | `/api/services/{id}/blast_radius` | Upstream blast radius calculation and score |
| `GET` | `/api/telemetry/metrics` | Statistical metric query (`mean`, `p95`, `min`, `max`, `stddev`) |
| `GET` | `/api/telemetry/logs` | Filterable structured logs by service, level, keyword |
| `GET` | `/api/telemetry/traces` | Distributed traces list with bottleneck identification |
| `GET` | `/api/telemetry/traces/{id}` | Full trace waterfall span detail |
| `GET` | `/api/incidents` | List active and resolved incidents |
| `POST` | `/api/incidents` | Trigger manual simulated incident |
| `GET` | `/api/incidents/{id}` | Incident detail and chronological timeline |
| `GET` | `/api/incidents/{id}/evidence` | Correlated evidence items for incident |
| `POST` | `/api/incidents/{id}/investigate` | Start bounded AI investigation |
| `GET` | `/api/investigations/{run_id}` | Fetch investigation run by ID |
| `POST` | `/api/incidents/{id}/actions` | Propose allowlisted remediation action |
| `POST` | `/api/actions/{id}/approve` | Authorized human approval of action |
| `POST` | `/api/actions/{id}/reject` | Reject action proposal with reason |
| `POST` | `/api/actions/{id}/execute` | Execute approved action in sandbox and run verification |
| `GET` | `/api/actions/{id}/verification` | Retrieve post-action telemetry verification report |
| `GET` | `/api/chaos/scenarios` | List 35+ benchmark chaos scenarios |
| `GET` | `/api/chaos/active` | List active injected faults |
| `POST` | `/api/chaos/inject` | Inject controlled chaos fault |
| `POST` | `/api/chaos/recover/{id}` | Clear specific active fault |
| `POST` | `/api/chaos/reset` | Clear all chaos and reset testbed to clean baseline |
| `POST` | `/api/benchmarks/run` | Run scientific research evaluation across B1–B4 |
| `GET` | `/api/experiments` | List historical benchmark experiment runs |
| `GET` | `/api/experiments/{id}/results` | Fetch experiment result metrics |
| `GET` | `/api/audit` | Chronological immutable audit trail |
| `POST` | `/api/traffic/toggle` | Start/stop synthetic traffic generator |

---

## 📂 Project Structure

```
majorproject/
├── Dockerfile                  # Multi-stage Docker build (React + Python runtime)
├── docker-compose.yml          # Containerized local environment (AC-01)
├── requirements.txt            # Python dependencies (FastAPI, Scikit-learn, etc.)
├── README.md                   # Comprehensive platform documentation
├── engine/
│   ├── main.py                 # FastAPI platform server and REST endpoints
│   ├── agent/                  # Bounded LLM investigation agent & tool registry
│   ├── benchmarks/             # Research evaluation suite (B1-B4, Ablations, MRR)
│   ├── chaos/                  # Chaos engine & 35+ benchmark scenarios
│   ├── detectors/              # Anomaly detectors (Rule, Z-Score, MAD, Isolation Forest)
│   ├── models/                 # Pydantic schemas, state machines, and contracts
│   ├── rca/                    # Evidence fusion engine & incident lifecycle manager
│   ├── remediation/            # Policy gate, action catalog, executor, and verifier
│   ├── telemetry/              # Metrics collector, log store, distributed trace store
│   └── topology/               # Directed dependency graph & DSA algorithms
├── services/
│   └── testbed_manager.py      # Simulated 5-service testbed with Postgres & Redis
├── scripts/
│   ├── run_platform.py         # Platform launcher on port 8000
│   ├── run_benchmarks.py       # Benchmark evaluation CLI
│   ├── inject_fault.py         # Chaos fault injection CLI
│   └── run_tests.py            # Comprehensive test suite runner
├── tests/                      # 28 passing pytest tests
│   ├── test_agent.py
│   ├── test_api.py
│   ├── test_benchmarks.py
│   ├── test_chaos_e2e.py
│   ├── test_detectors.py
│   ├── test_evidence_fusion.py
│   ├── test_remediation.py
│   ├── test_safety_negative.py
│   └── test_topology.py
└── web/                        # Modern React 18 + Vite + Tailwind dashboard
    ├── src/
    │   ├── api.ts              # Typed backend REST client
    │   ├── types.ts            # TypeScript interfaces
    │   ├── App.tsx             # Root dashboard controller
    │   ├── components/         # Modular views (Overview, Topology, Incidents, etc.)
    │   └── main.tsx
    └── dist/                   # Production-compiled assets served by FastAPI
```

---

## 📜 License

MIT License — Academic & Open Research.
