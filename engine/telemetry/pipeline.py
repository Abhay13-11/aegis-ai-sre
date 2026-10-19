"""
AEGIS Telemetry Pipeline Coordinator
Orchestrates metrics, logs, and distributed traces into a unified telemetry API.
"""

from typing import Dict, Any, List, Optional
from engine.models.schemas import MetricSample, LogEntry, Span
from .metrics_collector import MetricsCollector
from .log_store import LogStore
from .trace_store import TraceStore

class TelemetryPipeline:
    def __init__(self):
        self.metrics = MetricsCollector()
        self.logs = LogStore()
        self.traces = TraceStore()

    def record_metric(self, sample: MetricSample):
        self.metrics.record(sample)

    def record_log(self, log_entry: LogEntry):
        self.logs.record(log_entry)

    def record_span(self, span: Span):
        self.traces.record(span)

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "recent_traces_count": len(self.traces._trace_order),
            "recent_logs_count": len(self.logs._logs),
            "recent_traces": self.traces.get_recent_traces(limit=10),
            "recent_errors": [l.model_dump() for l in self.logs.get_recent_errors(limit=10)]
        }

    def clear(self):
        self.metrics.clear()
        self.logs.clear()
        self.traces.clear()
