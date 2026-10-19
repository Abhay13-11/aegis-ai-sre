"""
AEGIS Chaos Engine & Fault Injector
Provides controlled failure injection across all 5 services with ground-truth tracking.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from engine.models.schemas import (
    FaultType,
    ActiveFault,
    FaultInjectionRequest,
    LogLevel
)

class ChaosEngine:
    def __init__(self, testbed):
        self.testbed = testbed
        self.active_faults: Dict[str, ActiveFault] = {}

    def inject_fault(self, request: FaultInjectionRequest) -> ActiveFault:
        fault_id = f"flt_{uuid.uuid4().hex[:8]}"
        fault = ActiveFault(
            fault_id=fault_id,
            fault_type=request.fault_type,
            target_service=request.target_service,
            params=request.params,
            injected_at=time.time(),
            duration_seconds=request.duration_seconds,
            is_active=True
        )

        # Apply fault to testbed
        ftype = request.fault_type
        svc = request.target_service
        params = request.params

        if ftype == FaultType.DB_LATENCY:
            latency = float(params.get("latency_ms", 1200.0))
            self.testbed.postgres.injected_latency_ms = latency
            self.testbed.log(svc, LogLevel.WARN, f"[CHAOS] Injected DB latency: {latency}ms")

        elif ftype == FaultType.DB_POOL_EXHAUSTION:
            self.testbed.postgres.exhaustion_mode = True
            self.testbed.log(svc, LogLevel.FATAL, "[CHAOS] Injected DB connection pool exhaustion")

        elif ftype == FaultType.REDIS_FAILURE:
            self.testbed.redis.failure_mode = True
            self.testbed.log(svc, LogLevel.FATAL, "[CHAOS] Injected Redis failure (ECONNREFUSED)")

        elif ftype == FaultType.CPU_SPIKE:
            cpu = float(params.get("cpu_percent", 98.0))
            self.testbed.injected_cpu_spikes[svc] = cpu
            self.testbed.log(svc, LogLevel.WARN, f"[CHAOS] Injected CPU saturation: {cpu}%")

        elif ftype == FaultType.MEMORY_LEAK:
            mem = float(params.get("memory_percent", 96.0))
            self.testbed.injected_memory_leaks[svc] = mem
            self.testbed.log(svc, LogLevel.WARN, f"[CHAOS] Injected memory leak: {mem}% heap allocated")

        elif ftype == FaultType.NETWORK_DELAY:
            delay = float(params.get("delay_ms", 650.0))
            self.testbed.injected_network_delays[svc] = delay
            self.testbed.log(svc, LogLevel.WARN, f"[CHAOS] Injected network delay on {svc}: {delay}ms")

        elif ftype == FaultType.SERVICE_CRASH:
            self.testbed.killed_services.add(svc)
            self.testbed.log(svc, LogLevel.FATAL, f"[CHAOS] Service process terminated: SIGKILL {svc}")

        elif ftype == FaultType.BAD_CONFIG:
            key = params.get("key", "timeout_ms")
            val = params.get("value", 20)
            self.testbed.bad_configs[svc] = {key: val}
            self.testbed.log(svc, LogLevel.ERROR, f"[CHAOS] Bad config applied: {key}={val}")

        elif ftype == FaultType.CASCADING_FAILURE:
            # PostgreSQL pool exhaustion cascades to Inventory -> Order -> Gateway
            self.testbed.postgres.exhaustion_mode = True
            self.testbed.injected_network_delays["order_service"] = 800.0
            self.testbed.log("inventory_service", LogLevel.FATAL, "[CHAOS] Injected cascading DB exhaustion & pipeline stall")

        self.active_faults[fault_id] = fault
        return fault

    def recover_fault(self, fault_id: str) -> bool:
        fault = self.active_faults.get(fault_id)
        if not fault or not fault.is_active:
            return False

        ftype = fault.fault_type
        svc = fault.target_service

        if ftype == FaultType.DB_LATENCY:
            self.testbed.postgres.injected_latency_ms = 0.0
        elif ftype in (FaultType.DB_POOL_EXHAUSTION, FaultType.CASCADING_FAILURE):
            self.testbed.postgres.exhaustion_mode = False
            self.testbed.postgres.waiting_queries = 0
            self.testbed.injected_network_delays.pop("order_service", None)
        elif ftype == FaultType.REDIS_FAILURE:
            self.testbed.redis.failure_mode = False
        elif ftype == FaultType.CPU_SPIKE:
            self.testbed.injected_cpu_spikes.pop(svc, None)
        elif ftype == FaultType.MEMORY_LEAK:
            self.testbed.injected_memory_leaks.pop(svc, None)
        elif ftype == FaultType.NETWORK_DELAY:
            self.testbed.injected_network_delays.pop(svc, None)
        elif ftype == FaultType.SERVICE_CRASH:
            self.testbed.killed_services.discard(svc)
        elif ftype == FaultType.BAD_CONFIG:
            self.testbed.bad_configs.pop(svc, None)

        fault.is_active = False
        self.testbed.log(svc, LogLevel.INFO, f"[CHAOS] Recovered fault {fault_id} ({ftype.value})")
        return True

    def reset_all(self):
        """Clean recovery of all chaos injections."""
        self.testbed.postgres.injected_latency_ms = 0.0
        self.testbed.postgres.exhaustion_mode = False
        self.testbed.postgres.failure_mode = False
        self.testbed.postgres.waiting_queries = 0
        self.testbed.redis.failure_mode = False
        self.testbed.injected_cpu_spikes.clear()
        self.testbed.injected_memory_leaks.clear()
        self.testbed.injected_network_delays.clear()
        self.testbed.killed_services.clear()
        self.testbed.bad_configs.clear()
        self.testbed.error_counts = {s: 0 for s in self.testbed.services}

        for f in self.active_faults.values():
            f.is_active = False

    def list_active_faults(self) -> List[ActiveFault]:
        return [f for f in self.active_faults.values() if f.is_active]
