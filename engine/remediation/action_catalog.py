"""
AEGIS Remediation Action Catalog & Policy Definitions
Defines allowlisted operational actions, risk levels, and preconditions.
"""

from typing import Dict, Any, List
from engine.models.schemas import ActionRiskLevel

ALLOWLISTED_ACTIONS: Dict[str, Dict[str, Any]] = {
    "inspect_connection_pool": {
        "action_type": "inspect_connection_pool",
        "description": "Inspect active and waiting connections in database pool",
        "risk_level": ActionRiskLevel.LOW,
        "requires_approval": False,
        "is_read_only": True,
        "parameters_schema": {}
    },
    "clear_redis_cache": {
        "action_type": "clear_redis_cache",
        "description": "Flush transient Redis keys and reset cache connection pool",
        "risk_level": ActionRiskLevel.LOW,
        "requires_approval": False,
        "is_read_only": False,
        "parameters_schema": {}
    },
    "scale_replicas": {
        "action_type": "scale_replicas",
        "description": "Scale up container replica count to relieve CPU/traffic pressure",
        "risk_level": ActionRiskLevel.MEDIUM,
        "requires_approval": True,
        "is_read_only": False,
        "parameters_schema": {"replicas": "int"}
    },
    "restart_service": {
        "action_type": "restart_service",
        "description": "Perform graceful rolling restart of the target service container",
        "risk_level": ActionRiskLevel.MEDIUM,
        "requires_approval": True,
        "is_read_only": False,
        "parameters_schema": {}
    },
    "rollback_deployment": {
        "action_type": "rollback_deployment",
        "description": "Roll back to previous known stable deployment version and config",
        "risk_level": ActionRiskLevel.HIGH,
        "requires_approval": True,
        "is_read_only": False,
        "parameters_schema": {"target_version": "str"}
    },
    "tune_connection_pool_limit": {
        "action_type": "tune_connection_pool_limit",
        "description": "Dynamically adjust DB pool max_connections and clear waiting queues",
        "risk_level": ActionRiskLevel.HIGH,
        "requires_approval": True,
        "is_read_only": False,
        "parameters_schema": {"max_connections": "int"}
    },
    "toggle_circuit_breaker": {
        "action_type": "toggle_circuit_breaker",
        "description": "Trip or reset circuit breaker for failing downstream dependencies",
        "risk_level": ActionRiskLevel.MEDIUM,
        "requires_approval": True,
        "is_read_only": False,
        "parameters_schema": {"state": "str"}
    }
}
