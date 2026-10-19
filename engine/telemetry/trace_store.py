"""
AEGIS Distributed Trace Store
Indexes OpenTelemetry-compatible spans, reconstructs call trees,
and identifies critical paths and bottleneck spans.
"""

from typing import List, Dict, Optional, Any
from engine.models.schemas import Span

class TraceStore:
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        # trace_id -> List[Span]
        self._traces: Dict[str, List[Span]] = {}
        self._trace_order: List[str] = []

    def record(self, span: Span):
        tid = span.trace_id
        if tid not in self._traces:
            self._traces[tid] = []
            self._trace_order.append(tid)
            if len(self._trace_order) > self.max_traces:
                oldest = self._trace_order.pop(0)
                self._traces.pop(oldest, None)

        self._traces[tid].append(span)

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        spans = self._traces.get(trace_id)
        if not spans:
            return None

        # Sort spans by start_time
        sorted_spans = sorted(spans, key=lambda s: s.start_time)
        root_span = next((s for s in sorted_spans if not s.parent_span_id), sorted_spans[0])
        total_duration = max(s.end_time for s in sorted_spans) - min(s.start_time for s in sorted_spans)

        # Compute children map to calculate exclusive (self) time
        children_map: Dict[str, List[Span]] = {}
        for s in sorted_spans:
            if s.parent_span_id:
                if s.parent_span_id not in children_map:
                    children_map[s.parent_span_id] = []
                children_map[s.parent_span_id].append(s)

        # Identify bottleneck: deepest failing span if errors present, else highest exclusive self-time
        error_spans = [s for s in sorted_spans if s.status_code >= 400]
        has_error = len(error_spans) > 0

        if has_error:
            # Pick leaf error span (no children that also failed, or deepest)
            leaf_error_spans = [s for s in error_spans if s.span_id not in children_map or not any(c.status_code >= 400 for c in children_map.get(s.span_id, []))]
            bottleneck_span = leaf_error_spans[0] if leaf_error_spans else error_spans[-1]
        else:
            # Highest exclusive time
            def exclusive_time(s: Span) -> float:
                child_time = sum(c.duration_ms for c in children_map.get(s.span_id, []))
                return max(0.0, s.duration_ms - child_time)
            bottleneck_span = max(sorted_spans, key=exclusive_time)

        return {
            "trace_id": trace_id,
            "root_service": root_span.service_id,
            "root_operation": root_span.operation,
            "total_duration_ms": round(total_duration * 1000.0, 2),
            "span_count": len(sorted_spans),
            "has_error": has_error,
            "bottleneck_service": bottleneck_span.service_id,
            "bottleneck_operation": bottleneck_span.operation,
            "bottleneck_duration_ms": round(bottleneck_span.duration_ms, 2),
            "spans": [s.model_dump() for s in sorted_spans]
        }

    def get_recent_traces(self, limit: int = 50, error_only: bool = False) -> List[Dict[str, Any]]:
        results = []
        for tid in reversed(self._trace_order):
            trace_info = self.get_trace(tid)
            if trace_info:
                if error_only and not trace_info["has_error"]:
                    continue
                results.append(trace_info)
                if len(results) >= limit:
                    break
        return results

    def clear(self):
        self._traces.clear()
        self._trace_order.clear()
