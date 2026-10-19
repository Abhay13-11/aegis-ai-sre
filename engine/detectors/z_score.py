"""
AEGIS Statistical Anomaly Detectors: Z-Score and MAD
Implements standard statistical anomaly detection with dynamic baselines.
"""

from typing import List, Optional
import numpy as np
from engine.models.schemas import AnomalyEvent, AnomalySeverity

class ZScoreDetector:
    def __init__(self, z_threshold: float = 3.0, min_samples: int = 10):
        self.z_threshold = z_threshold
        self.min_samples = min_samples

    def evaluate(self, service_id: str, metric_name: str, values: List[float]) -> Optional[AnomalyEvent]:
        if len(values) < self.min_samples:
            return None

        arr = np.array(values[:-1])  # Historical baseline
        curr = values[-1]

        mean = np.mean(arr)
        std = np.std(arr)

        if std < 1e-4:
            return None

        z_score = abs(curr - mean) / std

        if z_score >= self.z_threshold:
            sev = AnomalySeverity.CRITICAL if z_score > 5.0 else AnomalySeverity.HIGH
            return AnomalyEvent(
                service_id=service_id,
                detector_type="Z_SCORE",
                metric_name=metric_name,
                current_value=round(curr, 2),
                expected_value=round(float(mean), 2),
                deviation_score=round(float(z_score), 2),
                severity=sev,
                summary=f"Z-Score anomaly on {service_id}:{metric_name} (Z={z_score:.2f} >= {self.z_threshold})"
            )
        return None

class MADDetector:
    """Median Absolute Deviation (MAD) detector - robust to outliers."""
    def __init__(self, threshold: float = 3.5, min_samples: int = 10):
        self.threshold = threshold
        self.min_samples = min_samples

    def evaluate(self, service_id: str, metric_name: str, values: List[float]) -> Optional[AnomalyEvent]:
        if len(values) < self.min_samples:
            return None

        arr = np.array(values[:-1])
        curr = values[-1]

        med = np.median(arr)
        mad = np.median(np.abs(arr - med))

        if mad < 1e-4:
            return None

        # Modified Z-score using MAD
        modified_z = 0.6745 * abs(curr - med) / mad

        if modified_z >= self.threshold:
            sev = AnomalySeverity.CRITICAL if modified_z > 6.0 else AnomalySeverity.HIGH
            return AnomalyEvent(
                service_id=service_id,
                detector_type="MAD",
                metric_name=metric_name,
                current_value=round(curr, 2),
                expected_value=round(float(med), 2),
                deviation_score=round(float(modified_z), 2),
                severity=sev,
                summary=f"MAD robust anomaly on {service_id}:{metric_name} (ModZ={modified_z:.2f} >= {self.threshold})"
            )
        return None
