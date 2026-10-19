"""
AEGIS Anomaly Detector Manager
Coordinates Rule-based, Statistical (Z-Score, MAD), and ML (Isolation Forest) detectors.
"""

from typing import List, Dict, Any
from engine.models.schemas import AnomalyEvent, ServiceSnapshot
from .rule_based import RuleBasedDetector
from .z_score import ZScoreDetector, MADDetector
from .isolation_forest_detector import IsolationForestDetector

class AnomalyDetectorManager:
    def __init__(self, metrics_collector=None):
        self.metrics_collector = metrics_collector
        self.rule_detector = RuleBasedDetector()
        self.z_detector = ZScoreDetector()
        self.mad_detector = MADDetector()
        self.iforest_detector = IsolationForestDetector()
        self.detected_anomalies: List[AnomalyEvent] = []

    def evaluate_services(self, snapshots: Dict[str, ServiceSnapshot]) -> List[AnomalyEvent]:
        current_anomalies: List[AnomalyEvent] = []

        for sid, snapshot in snapshots.items():
            # 1. Rule-based evaluation
            rule_anoms = self.rule_detector.evaluate(snapshot)
            current_anomalies.extend(rule_anoms)

            # 2. Statistical evaluation (Z-Score & MAD)
            if self.metrics_collector:
                for metric in ["p95_latency", "error_rate", "cpu_utilization"]:
                    samples = self.metrics_collector.query(sid, metric)
                    if len(samples) >= 10:
                        vals = [s.value for s in samples]
                        z_anom = self.z_detector.evaluate(sid, metric, vals)
                        if z_anom:
                            current_anomalies.append(z_anom)
                        mad_anom = self.mad_detector.evaluate(sid, metric, vals)
                        if mad_anom:
                            current_anomalies.append(mad_anom)

            # 3. Multivariate ML evaluation (Isolation Forest)
            if_anom = self.iforest_detector.evaluate(snapshot)
            if if_anom:
                current_anomalies.append(if_anom)

        # Retain recent anomalies in memory
        self.detected_anomalies.extend(current_anomalies)
        if len(self.detected_anomalies) > 500:
            self.detected_anomalies = self.detected_anomalies[-500:]

        return current_anomalies

    def get_recent_anomalies(self, limit: int = 50) -> List[AnomalyEvent]:
        return self.detected_anomalies[-limit:]

    def clear(self):
        self.detected_anomalies.clear()
