# AEGIS — Evidence-Grounded AI-SRE for Microservice Incident Diagnosis & Safe Remediation
## FINAL MAJOR PROJECT • PROJECT BIBLE

**One-line idea:** AEGIS is an AI-powered SRE platform that detects failures in distributed microservice systems, correlates metrics + logs + traces + service dependencies to identify root cause, quantifies evidential confidence, devises remediation plans, and verifies/gates risky actions before and after execution.

**Domain:** Distributed Systems + AIOps + Observability + Applied ML + LLM Agents

### 1. Project Positioning & Technical Identity
- **The Core Differentiation:** The LLM is an investigator, not the source of truth. The system grounds decisions in independently computed evidence, graph topology, policy, and post-action verification.
- **Workflow:** Observe → Detect → Correlate → Diagnose → Verify → Recommend/Remediate → Re-check.

### 2. End-to-End Architecture
1. **Microservice Testbed:** API Gateway → User Service → Order Service → Payment Service (Redis) & Inventory Service (PostgreSQL).
2. **Observability Pipeline:** OpenTelemetry collectors routing metrics, logs, traces.
3. **Detection Layer:** Rules, Z-score, MAD, EWMA/CUSUM, and Isolation Forest.
4. **Service Dependency Graph:** Directed topology graph (BFS/DFS, path propagation, blast radius).
5. **Evidence Fusion Engine:** Measurable signal scoring:
   $$RootCauseScore = 0.30 \times \text{dependency} + 0.25 \times \text{temporal} + 0.20 \times \text{severity} + 0.15 \times \text{trace} + 0.10 \times \text{history}$$
6. **LLM Investigation Agent:** Bounded read-only tools (`get_service_graph`, `get_metric`, `get_logs`, `get_trace`, `get_recent_deployments`, `get_incident_history`).
7. **Safe Remediation & Verification:** Allowlisted actions, risk scoring, human approval gates, sandboxed execution, and telemetry-based recovery verification.
8. **Research Benchmarking:** Baselines B1–B4, ablation studies, and 30–50 controlled fault scenarios.
