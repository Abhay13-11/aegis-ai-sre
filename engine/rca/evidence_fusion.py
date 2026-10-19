"""
AEGIS Deterministic Evidence Fusion & Root Cause Analysis Engine
Implements the multi-modal evidence fusion formula:
RootCauseScore = 0.30 * dependency_relevance
               + 0.25 * temporal_correlation
               + 0.20 * anomaly_severity
               + 0.15 * trace_propagation
               + 0.10 * historical_similarity
"""

import math
import time
from typing import List, Dict, Any, Optional
from engine.models.schemas import (
    RootCauseCandidate,
    ScoreBreakdown,
    EvidenceItem,
    SignalType,
    AnomalyEvent,
    AnomalySeverity
)

class EvidenceFusionEngine:
    def __init__(self, dependency_graph, trace_store=None):
        self.graph = dependency_graph
        self.trace_store = trace_store

        # Mathematical weights
        self.w_dep = 0.30
        self.w_temporal = 0.25
        self.w_severity = 0.20
        self.w_trace = 0.15
        self.w_history = 0.10

    def compute_scores(
        self,
        candidate_services: List[str],
        anomalies: List[AnomalyEvent],
        incident_evidence: List[EvidenceItem],
        historical_matches: Optional[Dict[str, float]] = None
    ) -> List[RootCauseCandidate]:
        if not candidate_services:
            return []

        anomalous_service_ids = list({a.service_id for a in anomalies})
        if not anomalous_service_ids:
            anomalous_service_ids = candidate_services

        # 1. Compute earliest anomaly timestamp per service
        earliest_times: Dict[str, float] = {}
        for a in anomalies:
            if a.service_id not in earliest_times or a.timestamp < earliest_times[a.service_id]:
                earliest_times[a.service_id] = a.timestamp

        global_first_time = min(earliest_times.values()) if earliest_times else time.time()

        candidates: List[RootCauseCandidate] = []

        # 2. Trace bottleneck analysis
        bottleneck_counts: Dict[str, int] = {c: 0 for c in candidate_services}
        total_slow_traces = 0
        if self.trace_store:
            recent_traces = self.trace_store.get_recent_traces(limit=40)
            for t in recent_traces:
                if t.get("has_error") or t.get("total_duration_ms", 0) > 300.0:
                    total_slow_traces += 1
                    bn_svc = t.get("bottleneck_service")
                    if bn_svc in bottleneck_counts:
                        bottleneck_counts[bn_svc] += 1

        for candidate in candidate_services:
            # S_dep: Topological graph relevance
            s_dep = self.graph.calculate_topological_relevance(candidate, anomalous_service_ids)

            # S_temporal: Did this service show symptoms first?
            c_first = earliest_times.get(candidate)
            if c_first is not None:
                delta_t = max(0.0, c_first - global_first_time)
                # Exponential decay: delta_t = 0 -> 1.0; delta_t = 30s -> 0.60
                s_temporal = math.exp(-delta_t / 30.0)
            else:
                s_temporal = 0.15

            # S_severity: Anomaly severity score
            c_anoms = [a for a in anomalies if a.service_id == candidate]
            if c_anoms:
                severity_weights = {
                    AnomalySeverity.CRITICAL: 1.0,
                    AnomalySeverity.HIGH: 0.75,
                    AnomalySeverity.MEDIUM: 0.50,
                    AnomalySeverity.LOW: 0.25
                }
                max_sev = max(severity_weights.get(a.severity, 0.5) for a in c_anoms)
                count_factor = min(1.0, len(c_anoms) / 3.0)
                s_severity = 0.7 * max_sev + 0.3 * count_factor
            else:
                s_severity = 0.10

            # S_trace: Trace bottleneck concentration
            if total_slow_traces > 0:
                s_trace = bottleneck_counts[candidate] / total_slow_traces
            else:
                s_trace = 0.20

            # S_history: Historical similarity
            s_history = 0.50
            if historical_matches and candidate in historical_matches:
                s_history = historical_matches[candidate]

            # Evidence Fusion Formula
            final_score = (
                self.w_dep * s_dep +
                self.w_temporal * s_temporal +
                self.w_severity * s_severity +
                self.w_trace * s_trace +
                self.w_history * s_history
            )
            final_score = round(min(1.0, max(0.0, final_score)), 3)

            breakdown = ScoreBreakdown(
                dependency_relevance=round(s_dep, 3),
                temporal_correlation=round(s_temporal, 3),
                anomaly_severity=round(s_severity, 3),
                trace_propagation=round(s_trace, 3),
                historical_similarity=round(s_history, 3),
                final_score=final_score
            )

            # Gather supporting and contradicting evidence
            supporting_ids = [
                ev.evidence_id for ev in incident_evidence
                if ev.service_id == candidate
            ]
            contradicting_ids = []
            if s_dep < 0.2 and s_severity > 0.8:
                contradicting_ids.append("ev_topological_isolation")

            explanation = (
                f"Candidate {candidate}: dep_relevance={s_dep:.2f}, "
                f"temporal_lead={s_temporal:.2f}, severity={s_severity:.2f}, "
                f"trace_bottleneck={s_trace:.2f}."
            )

            candidates.append(RootCauseCandidate(
                component_id=candidate,
                rank=1, # assigned after sorting
                score=final_score,
                score_type="ranking_score",
                score_breakdown=breakdown,
                supporting_evidence_ids=supporting_ids,
                contradicting_evidence_ids=contradicting_ids,
                root_cause_explanation=explanation
            ))

        # Sort candidates descending by final_score
        candidates.sort(key=lambda c: c.score, reverse=True)
        for i, c in enumerate(candidates):
            c.rank = i + 1

        return candidates
