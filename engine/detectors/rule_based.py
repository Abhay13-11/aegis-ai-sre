"""
AEGIS Rule-Based Anomaly Detector
Static / threshold-based baseline anomaly detection.
"""

from typing import List, Optional
from engine.models.schemas import AnomalyEvent, AnomalySeverity, ServiceSnapshot

class RuleBasedDetector:
    def __init__(
        self,
        error_rate_threshold: float = 5.0,  # %
        p95_latency_threshold: float = 400.0,  # ms
        cpu_threshold: float = 85.0,  # %
        memory_threshold: float = 90.0,  # %
    ):
        self.error_rate_threshold = error_rate_threshold
        self.p95_latency_threshold = p95_latency_threshold
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def evaluate(self, snapshot: ServiceSnapshot) -> List[AnomalyEvent]:
        anomalies = []
        sid = snapshot.service_id

        # 1. Error Rate Rule
        if snapshot.error_rate > self.error_rate_threshold:
            sev = AnomalySeverity.CRITICAL if snapshot.error_rate > 20.0 else AnomalySeverity.HIGH
            anomalies.append(AnomalyEvent(
                service_id=sid,
                detector_type="RULE_BASED",
                metric_name="error_rate",
                current_value=snapshot.error_rate,
                expected_value=self.error_rate_threshold,
                deviation_score=round(snapshot.error_rate - self.error_rate_threshold, 2),
                severity=sev,
                summary=f"Rule breach: {sid} error rate {snapshot.error_rate:.1f}% exceeds threshold {self.error_rate_threshold}%"
            ))

        # 2. Latency Rule
        if snapshot.p95_latency_ms > self.p95_latency_threshold:
            sev = AnomalySeverity.CRITICAL if snapshot.p95_latency_ms > 1000.0 else AnomalySeverity.HIGH
            anomalies.append(AnomalyEvent(
                service_id=sid,
                detector_type="RULE_BASED",
                metric_name="p95_latency",
                current_value=snapshot.p95_latency_ms,
                expected_value=self.p95_latency_threshold,
                deviation_score=round(snapshot.p95_latency_ms - self.p95_latency_threshold, 1),
                severity=sev,
                summary=f"Rule breach: {sid} p95 latency {snapshot.p95_latency_ms:.1f}ms exceeds threshold {self.p95_latency_threshold}ms"
            ))

        # 3. CPU Rule
        if snapshot.cpu_percent > self.cpu_threshold:
            anomalies.append(AnomalyEvent(
                service_id=sid,
                detector_type="RULE_BASED",
                metric_name="cpu_utilization",
                current_value=snapshot.cpu_percent,
                expected_value=self.cpu_threshold,
                deviation_score=round(snapshot.cpu_percent - self.cpu_threshold, 1),
                severity=AnomalySeverity.HIGH,
                summary=f"Rule breach: {sid} CPU utilization {snapshot.cpu_percent:.1f}% exceeds threshold {self.cpu_threshold}%"
            ))

        # 4. Memory Rule
        if snapshot.memory_percent > self.memory_threshold:
            anomalies.append(AnomalyEvent(
                service_id=sid,
                detector_type="RULE_BASED",
                metric_name="memory_utilization",
                current_value=snapshot.memory_percent,
                expected_value=self.memory_threshold,
                deviation_score=round(snapshot.memory_percent - self.memory_threshold, 1),
                severity=AnomalySeverity.HIGH,
                summary=f"Rule breach: {sid} Memory {snapshot.memory_percent:.1f}% exceeds threshold {self.memory_threshold}%"
            ))

        # 5. DB Waiting queries rule (if applicable)
        waiting = snapshot.metadata.get("waiting_queries")
        if waiting and waiting > 3:
            anomalies.append(AnomalyEvent(
                service_id=sid,
                detector_type="RULE_BASED",
                metric_name="db_pool_waiting",
                current_value=float(waiting),
                expected_value=0.0,
                deviation_score=float(waiting),
                severity=AnomalySeverity.CRITICAL,
                summary=f"Rule breach: {sid} has {waiting} queries stalled in DB connection wait queue"
            ))

        return anomalies
