"""
AEGIS Bounded Read-Only Agent Tools
Provides safe, scoped telemetry and topology query tools for the LLM Investigator.
"""

from typing import Dict, Any, List, Optional
from engine.models.schemas import AgentToolCall

class AgentToolRegistry:
    def __init__(self, dependency_graph, telemetry_pipeline, testbed=None):
        self.graph = dependency_graph
        self.telemetry = telemetry_pipeline
        self.testbed = testbed
        self.audit_log: List[AgentToolCall] = []

    def get_service_graph(self) -> Dict[str, Any]:
        """Tool 1: Return the complete service dependency graph nodes and edges."""
        result = self.graph.to_dict()
        self.audit_log.append(AgentToolCall(
            tool_name="get_service_graph",
            parameters={},
            output_summary=f"Returned {len(result['nodes'])} nodes and {len(result['edges'])} edges"
        ))
        return result

    def get_metric(self, service: str, metric_name: str, window_seconds: float = 60.0) -> Dict[str, Any]:
        """Tool 2: Query time-series metrics statistics for a service."""
        if not self.telemetry:
            return {"error": "Telemetry pipeline unavailable"}
        
        stats = self.telemetry.metrics.get_stats(service, metric_name, window_seconds)
        self.audit_log.append(AgentToolCall(
            tool_name="get_metric",
            parameters={"service": service, "metric_name": metric_name, "window_seconds": window_seconds},
            output_summary=f"{service}:{metric_name} mean={stats['mean']:.1f}, current={stats['current']:.1f}"
        ))
        return {
            "service": service,
            "metric_name": metric_name,
            "stats": stats
        }

    def get_logs(self, service: str, query: Optional[str] = None, level: Optional[str] = "ERROR", limit: int = 10) -> List[Dict[str, Any]]:
        """Tool 3: Query filtered logs for a target service."""
        if not self.telemetry:
            return []
        
        entries = self.telemetry.logs.query(service_id=service, keyword=query, limit=limit)
        self.audit_log.append(AgentToolCall(
            tool_name="get_logs",
            parameters={"service": service, "query": query, "level": level, "limit": limit},
            output_summary=f"Found {len(entries)} matching log entries for {service}"
        ))
        return [e.model_dump() for e in entries]

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Tool 4: Inspect distributed trace span tree and bottleneck breakdown."""
        if not self.telemetry:
            return None
        
        trace = self.telemetry.traces.get_trace(trace_id)
        self.audit_log.append(AgentToolCall(
            tool_name="get_trace",
            parameters={"trace_id": trace_id},
            output_summary=f"Trace {trace_id}: total={trace.get('total_duration_ms') if trace else 'not found'}ms"
        ))
        return trace

    def get_recent_deployments(self, service: str) -> Dict[str, Any]:
        """Tool 5: Query recent deployment versions and configuration changes."""
        version = "v1.0.0"
        bad_cfg = {}
        if self.testbed and service in self.testbed.services:
            version = self.testbed.services[service].version
            bad_cfg = self.testbed.bad_configs.get(service, {})

        result = {
            "service": service,
            "current_version": version,
            "recent_deployments": [
                {"version": version, "deployed_at": "1 hour ago", "status": "ACTIVE"}
            ],
            "active_config_overrides": bad_cfg
        }
        self.audit_log.append(AgentToolCall(
            tool_name="get_recent_deployments",
            parameters={"service": service},
            output_summary=f"Version={version}, Overrides={len(bad_cfg)}"
        ))
        return result

    def get_incident_history(self, service: str) -> List[Dict[str, Any]]:
        """Tool 6: Query previous historical incidents affecting this service."""
        history = [
            {
                "incident_id": "INC-HIST-882",
                "service": "inventory_service",
                "root_cause": "PostgreSQL connection pool exhaustion",
                "resolution": "tune_connection_pool_limit",
                "timestamp": "3 days ago"
            },
            {
                "incident_id": "INC-HIST-741",
                "service": "payment_service",
                "root_cause": "Redis connection timeout",
                "resolution": "clear_redis_cache",
                "timestamp": "2 weeks ago"
            }
        ]
        matches = [h for h in history if h["service"] == service]
        self.audit_log.append(AgentToolCall(
            tool_name="get_incident_history",
            parameters={"service": service},
            output_summary=f"Found {len(matches)} historical incident records for {service}"
        ))
        return matches
