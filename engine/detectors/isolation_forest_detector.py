"""
AEGIS Isolation Forest Multivariate Anomaly Detector
Leverages scikit-learn IsolationForest to identify non-linear multivariate operational anomalies.
"""

from typing import List, Optional, Dict
import numpy as np
from sklearn.ensemble import IsolationForest
from engine.models.schemas import AnomalyEvent, AnomalySeverity, ServiceSnapshot

class IsolationForestDetector:
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        # service_id -> IsolationForest model
        self.models: Dict[str, IsolationForest] = {}
        # service_id -> List of feature vectors
        self.feature_history: Dict[str, List[List[float]]] = {}

    def _extract_vector(self, snapshot: ServiceSnapshot) -> List[float]:
        # Vector: [cpu_percent, memory_percent, p95_latency_ms, error_rate]
        return [
            float(snapshot.cpu_percent),
            float(snapshot.memory_percent),
            float(snapshot.p95_latency_ms),
            float(snapshot.error_rate)
        ]

    def train_or_update(self, service_id: str, history: List[List[float]]):
        if len(history) < 15:
            return
        X = np.array(history)
        model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=50
        )
        model.fit(X)
        self.models[service_id] = model

    def evaluate(self, snapshot: ServiceSnapshot) -> Optional[AnomalyEvent]:
        sid = snapshot.service_id
        vec = self._extract_vector(snapshot)

        if sid not in self.feature_history:
            self.feature_history[sid] = []
        self.feature_history[sid].append(vec)

        if len(self.feature_history[sid]) > 300:
            self.feature_history[sid].pop(0)

        # Train model if not present or periodic
        if sid not in self.models and len(self.feature_history[sid]) >= 15:
            self.train_or_update(sid, self.feature_history[sid])

        model = self.models.get(sid)
        if not model:
            return None

        X_curr = np.array([vec])
        pred = model.predict(X_curr)[0] # -1 for anomaly, 1 for normal
        score = model.score_samples(X_curr)[0] # lower is more abnormal

        if pred == -1:
            anomaly_score = round(abs(float(score)), 3)
            sev = AnomalySeverity.CRITICAL if anomaly_score > 0.65 else AnomalySeverity.HIGH
            return AnomalyEvent(
                service_id=sid,
                detector_type="ISOLATION_FOREST",
                metric_name="multivariate[cpu,mem,lat,err]",
                current_value=round(snapshot.p95_latency_ms, 1),
                expected_value=25.0,
                deviation_score=anomaly_score,
                severity=sev,
                summary=f"Multivariate Isolation Forest anomaly on {sid} (outlier score={anomaly_score})"
            )
        return None
