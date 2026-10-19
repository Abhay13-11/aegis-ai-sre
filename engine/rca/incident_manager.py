"""
AEGIS Incident Manager & Lifecycle Coordinator
Tracks active and resolved incidents, chronologically links multi-signal evidence,
and manages transitions across the incident state machine.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from engine.models.schemas import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimelineEvent,
    EvidenceItem,
    SignalType,
    AnomalyEvent,
    RootCauseCandidate
)

class IncidentManager:
    def __init__(self, fusion_engine, dependency_graph, telemetry_pipeline=None):
        self.fusion_engine = fusion_engine
        self.graph = dependency_graph
        self.telemetry = telemetry_pipeline
        self.incidents: Dict[str, Incident] = {}
        self.active_incident_id: Optional[str] = None

    def create_incident_from_anomalies(
        self,
        anomalies: List[AnomalyEvent],
        title_prefix: str = "Automated Incident Alert"
    ) -> Incident:
        if not anomalies:
            raise ValueError("Cannot create incident without anomalies")

        affected = sorted(list({a.service_id for a in anomalies}))
        incident_id = f"inc_{uuid.uuid4().hex[:8]}"

        # Calculate max severity
        has_critical = any(a.severity.value == "CRITICAL" for a in anomalies)
        severity = IncidentSeverity.P1_CRITICAL if has_critical else IncidentSeverity.P2_HIGH

        now = time.time()
        timeline = [
            IncidentTimelineEvent(
                timestamp=now,
                event_type="DETECTED",
                description=f"Anomaly detector triggered incident across services: {', '.join(affected)}",
                actor="DETECTOR_MANAGER"
            )
        ]

        # Extract EvidenceItems from anomalies, logs, traces
        evidence: List[EvidenceItem] = []
        for a in anomalies:
            evidence.append(EvidenceItem(
                signal_type=SignalType.METRIC,
                service_id=a.service_id,
                summary=a.summary,
                timestamp=a.timestamp,
                metric_ref=f"{a.service_id}:{a.metric_name}",
                anomaly_score=a.deviation_score,
                provenance="anomaly_detector"
            ))

        # Query recent error logs
        if self.telemetry:
            for s in affected:
                errors = self.telemetry.logs.get_recent_errors(service_id=s, limit=3)
                for err in errors:
                    evidence.append(EvidenceItem(
                        signal_type=SignalType.LOG,
                        service_id=s,
                        summary=f"Error Log: {err.message[:120]}",
                        timestamp=err.timestamp,
                        log_ref=err.log_id,
                        trace_ref=err.trace_id,
                        anomaly_score=1.0,
                        provenance="log_collector"
                    ))

        # Compute blast radius
        blast_radius = []
        for s in affected:
            blast_radius.extend(self.graph.get_all_upstream_impacted(s))
        blast_radius = sorted(list(set(blast_radius + affected)))

        # Run Deterministic Evidence Fusion RCA
        candidates = self.fusion_engine.compute_scores(
            candidate_services=affected,
            anomalies=anomalies,
            incident_evidence=evidence
        )
        root_cause = candidates[0].component_id if candidates else affected[0]

        timeline.append(IncidentTimelineEvent(
            timestamp=time.time(),
            event_type="CORRELATED",
            description=f"Correlated {len(evidence)} evidence signals against topology. Top root-cause candidate: {root_cause}",
            actor="EVIDENCE_FUSION_ENGINE"
        ))

        incident = Incident(
            incident_id=incident_id,
            title=f"{title_prefix}: Anomaly detected on {', '.join(affected)}",
            severity=severity,
            status=IncidentStatus.OPEN,
            affected_services=affected,
            root_cause_service=root_cause,
            created_at=now,
            updated_at=time.time(),
            blast_radius=blast_radius,
            evidence_items=evidence,
            candidates=candidates,
            timeline=timeline
        )

        self.incidents[incident_id] = incident
        self.active_incident_id = incident_id
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.incidents.get(incident_id)

    def list_incidents(self, limit: int = 50) -> List[Incident]:
        return list(reversed(list(self.incidents.values())))[:limit]

    def add_timeline_event(self, incident_id: str, event_type: str, description: str, actor: str = "AEGIS_SYSTEM", metadata: Dict[str, Any] = None):
        incident = self.get_incident(incident_id)
        if incident:
            incident.timeline.append(IncidentTimelineEvent(
                timestamp=time.time(),
                event_type=event_type,
                description=description,
                actor=actor,
                metadata=metadata or {}
            ))
            incident.updated_at = time.time()

    def update_status(self, incident_id: str, status: IncidentStatus, root_cause: Optional[str] = None):
        incident = self.get_incident(incident_id)
        if incident:
            incident.status = status
            if root_cause:
                incident.root_cause_service = root_cause
            if status == IncidentStatus.RESOLVED:
                incident.resolved_at = time.time()
            incident.updated_at = time.time()
            self.add_timeline_event(incident_id, "STATUS_CHANGE", f"Incident transitioned to {status.value}")

    def clear(self):
        self.incidents.clear()
        self.active_incident_id = None
