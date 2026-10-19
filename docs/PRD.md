# AEGIS — Product Requirements Document (PRD)
## Version 1.0 • Implementation Baseline

### Core Principle
**The LLM is an investigator, not the source of truth.**

### 1. Functional Requirements Summary
- **FR-001 - FR-006:** Service Inventory, Health endpoints, OpenTelemetry collection, Trace correlation propagation, Incident lifecycle & timeline.
- **FR-007 - FR-008:** Anomaly detection (Z-Score, MAD, EWMA, Isolation Forest).
- **FR-009 - FR-015:** Service Dependency Graph (directed graph, blast radius, topological candidate ranking, evidence fusion formula, uncalibrated score vs calibrated confidence).
- **FR-016 - FR-019:** Bounded read-only tools for LLM agent, structured schema validation, inconclusive/uncertainty reporting, cost and token guardrails.
- **FR-020 - FR-026:** Remediation allowlist, risk tiers (Low/Medium/High), human approval workflow, sandbox execution, post-action telemetry re-check and recovery verification.
- **FR-027 - FR-032:** Chaos engine with ground truth (target 30-50 controlled scenarios), research evaluation suite (Top-1, Top-3, MRR, baselines B1-B4, ablation studies).
- **FR-033 - FR-038:** Modern web dashboard (overview, topology, incident timeline, evidence explorer, investigation & safe remediation console, chaos lab & research benchmarks).

### 2. State Machine for Remediation
`PROPOSED` → `PENDING_APPROVAL` → `APPROVED` / `REJECTED` → `EXECUTING` → `SUCCEEDED` / `FAILED` → `VERIFYING` → `VERIFIED_RECOVERED` / `NOT_RECOVERED` / `INCONCLUSIVE`.
Backend strictly prevents invalid state transitions.
