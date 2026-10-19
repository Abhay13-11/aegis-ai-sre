"""
AEGIS Metrics Collector
Collects, aggregates, and provides time-series window queries for microservice metrics.
"""

import time
from typing import Dict, List, Any, Optional
import numpy as np
from engine.models.schemas import MetricSample

class MetricsCollector:
    def __init__(self, max_samples_per_series: int = 1000):
        self.max_samples_per_series = max_samples_per_series
        # (service_id, metric_name) -> List[MetricSample]
        self._series: Dict[str, List[MetricSample]] = {}

    def _key(self, service_id: str, metric_name: str) -> str:
        return f"{service_id}:{metric_name}"

    def record(self, sample: MetricSample):
        key = self._key(sample.service_id, sample.metric_name)
        if key not in self._series:
            self._series[key] = []
        
        self._series[key].append(sample)
        if len(self._series[key]) > self.max_samples_per_series:
            self._series[key].pop(0)

    def query(self, service_id: str, metric_name: str, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[MetricSample]:
        key = self._key(service_id, metric_name)
        samples = self._series.get(key, [])
        if not start_time and not end_time:
            return samples[-60:] # Default last 60 samples
        
        start = start_time or 0.0
        end = end_time or time.time()
        return [s for s in samples if start <= s.timestamp <= end]

    def get_latest_value(self, service_id: str, metric_name: str, default: float = 0.0) -> float:
        key = self._key(service_id, metric_name)
        samples = self._series.get(key, [])
        return samples[-1].value if samples else default

    def get_stats(self, service_id: str, metric_name: str, window_seconds: float = 60.0) -> Dict[str, float]:
        now = time.time()
        samples = self.query(service_id, metric_name, start_time=now - window_seconds, end_time=now)
        if not samples:
            return {"mean": 0.0, "std": 0.0, "p95": 0.0, "current": 0.0, "count": 0}
        
        vals = [s.value for s in samples]
        arr = np.array(vals)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "p95": float(np.percentile(arr, 95)),
            "max": float(np.max(arr)),
            "min": float(np.min(arr)),
            "current": vals[-1],
            "count": len(vals)
        }

    def clear(self):
        self._series.clear()
