"""
AEGIS Microservices Testbed Engine
Simulates the 5 microservices with realistic distributed tracing,
connection pooling, caches, and asynchronous synthetic traffic generation.
"""

import asyncio
import time
import uuid
import random
from typing import Dict, Any, List, Optional
from engine.models.schemas import (
    ServiceHealthStatus,
    ServiceSnapshot,
    Span,
    LogEntry,
    LogLevel,
    MetricSample,
    FaultType
)

class PostgresPoolSimulator:
    """Simulates PostgreSQL Connection Pool and query execution."""
    def __init__(self, max_connections: int = 15):
        self.max_connections = max_connections
        self.active_connections = 0
        self.waiting_queries = 0
        self.base_latency_ms = 12.0
        self.injected_latency_ms = 0.0
        self.exhaustion_mode = False
        self.failure_mode = False

    async def execute_query(self, query: str, timeout_ms: float = 3000.0) -> float:
        if self.exhaustion_mode:
            self.waiting_queries += 1
            # Simulate pool saturation wait
            await asyncio.sleep(min(timeout_ms / 1000.0, 1.2))
            self.waiting_queries = max(0, self.waiting_queries - 1)
            raise TimeoutError("FATAL: PostgreSQL connection pool exhausted (timeout waiting for free connection)")

        if self.failure_mode:
            await asyncio.sleep(0.05)
            raise ConnectionRefusedError("PostgreSQL connection refused: database unavailable")

        if self.active_connections >= self.max_connections:
            self.waiting_queries += 1
            wait_time = random.uniform(0.1, 0.4)
            await asyncio.sleep(wait_time)
            self.waiting_queries = max(0, self.waiting_queries - 1)

        self.active_connections += 1
        latency = (self.base_latency_ms + self.injected_latency_ms + random.uniform(-2, 5)) / 1000.0
        latency = max(0.002, latency)
        await asyncio.sleep(latency)
        self.active_connections = max(0, self.active_connections - 1)
        return latency * 1000.0

class RedisSimulator:
    """Simulates Redis Cache with latency, memory, and failure states."""
    def __init__(self):
        self.base_latency_ms = 2.0
        self.injected_latency_ms = 0.0
        self.failure_mode = False
        self.cache_store: Dict[str, Any] = {}
        self.hit_count = 0
        self.miss_count = 0

    async def get_or_set(self, key: str, value: Any) -> float:
        if self.failure_mode:
            await asyncio.sleep(0.02)
            raise ConnectionError("Redis server connection timed out: ECONNREFUSED")

        latency = (self.base_latency_ms + self.injected_latency_ms + random.uniform(-0.5, 1.0)) / 1000.0
        latency = max(0.001, latency)
        await asyncio.sleep(latency)
        if key in self.cache_store:
            self.hit_count += 1
        else:
            self.miss_count += 1
            self.cache_store[key] = value
        return latency * 1000.0

class MicroservicesTestbed:
    """
    Manages the 5 demo services:
    1. api_gateway
    2. user_service
    3. order_service
    4. payment_service (uses Redis)
    5. inventory_service (uses PostgreSQL)
    """
    def __init__(self, telemetry_pipeline=None):
        self.telemetry = telemetry_pipeline
        self.postgres = PostgresPoolSimulator()
        self.redis = RedisSimulator()
        
        # Service snapshots & operational state
        self.services: Dict[str, ServiceSnapshot] = {
            "api_gateway": ServiceSnapshot(service_id="api_gateway", name="API Gateway", status=ServiceHealthStatus.HEALTHY, version="v1.2.0"),
            "user_service": ServiceSnapshot(service_id="user_service", name="User Service", status=ServiceHealthStatus.HEALTHY, version="v1.1.0"),
            "order_service": ServiceSnapshot(service_id="order_service", name="Order Service", status=ServiceHealthStatus.HEALTHY, version="v2.0.1"),
            "payment_service": ServiceSnapshot(service_id="payment_service", name="Payment Service", status=ServiceHealthStatus.HEALTHY, version="v1.4.0"),
            "inventory_service": ServiceSnapshot(service_id="inventory_service", name="Inventory Service", status=ServiceHealthStatus.HEALTHY, version="v1.3.2"),
        }

        # Fault state overrides
        self.injected_cpu_spikes: Dict[str, float] = {}
        self.injected_memory_leaks: Dict[str, float] = {}
        self.injected_network_delays: Dict[str, float] = {}
        self.killed_services: set = set()
        self.bad_configs: Dict[str, Dict[str, Any]] = {}

        # Metric accumulators
        self.request_counts: Dict[str, int] = {s: 0 for s in self.services}
        self.error_counts: Dict[str, int] = {s: 0 for s in self.services}
        self.latency_samples: Dict[str, List[float]] = {s: [] for s in self.services}

        self.traffic_running = False
        self._traffic_task = None

    def set_telemetry_pipeline(self, pipeline):
        self.telemetry = pipeline

    def record_span(self, trace_id: str, span_id: str, parent_span_id: Optional[str],
                    service_id: str, operation: str, start_time: float, end_time: float,
                    status_code: int = 200, tags: Dict[str, Any] = None):
        duration_ms = (end_time - start_time) * 1000.0
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            service_id=service_id,
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status_code=status_code,
            tags=tags or {}
        )
        if self.telemetry:
            self.telemetry.record_span(span)
        
        # Track metric sample
        self.latency_samples[service_id].append(duration_ms)
        if len(self.latency_samples[service_id]) > 100:
            self.latency_samples[service_id].pop(0)

    def log(self, service_id: str, level: LogLevel, message: str, trace_id: Optional[str] = None, attributes: Dict[str, Any] = None):
        entry = LogEntry(
            service_id=service_id,
            level=level,
            message=message,
            timestamp=time.time(),
            trace_id=trace_id,
            attributes=attributes or {}
        )
        if self.telemetry:
            self.telemetry.record_log(entry)

    # --- Core Service Logic with Call Propagation ---

    async def handle_user_request(self, trace_id: str, parent_span_id: str, user_id: str = "usr_1001") -> Dict[str, Any]:
        span_id = f"sp_{uuid.uuid4().hex[:8]}"
        t_start = time.time()
        self.request_counts["user_service"] += 1

        if "user_service" in self.killed_services:
            self.error_counts["user_service"] += 1
            t_end = time.time()
            self.record_span(trace_id, span_id, parent_span_id, "user_service", "validate_token", t_start, t_end, 503)
            self.log("user_service", LogLevel.ERROR, "Service instance crashed: 503 Service Unavailable", trace_id)
            raise ConnectionError("user_service unreachable")

        # Simulate work
        base_delay = 0.010 + random.uniform(0.002, 0.008)
        if "user_service" in self.injected_cpu_spikes:
            base_delay += 0.250
        await asyncio.sleep(base_delay)

        t_end = time.time()
        self.record_span(trace_id, span_id, parent_span_id, "user_service", "validate_token", t_start, t_end, 200)
        self.log("user_service", LogLevel.INFO, f"Validated authentication token for user {user_id}", trace_id)
        return {"authenticated": True, "user_id": user_id, "tier": "premium"}

    async def handle_inventory_request(self, trace_id: str, parent_span_id: str, item_id: str = "prod_99", qty: int = 1) -> Dict[str, Any]:
        span_id = f"sp_{uuid.uuid4().hex[:8]}"
        t_start = time.time()
        self.request_counts["inventory_service"] += 1

        if "inventory_service" in self.killed_services:
            self.error_counts["inventory_service"] += 1
            t_end = time.time()
            self.record_span(trace_id, span_id, parent_span_id, "inventory_service", "reserve_inventory", t_start, t_end, 503)
            self.log("inventory_service", LogLevel.ERROR, "inventory_service process unavailable", trace_id)
            raise ConnectionError("inventory_service unreachable")

        # Database call
        db_span_id = f"sp_db_{uuid.uuid4().hex[:8]}"
        t_db_start = time.time()
        try:
            db_latency = await self.postgres.execute_query(f"SELECT * FROM inventory WHERE item_id='{item_id}' FOR UPDATE")
            t_db_end = time.time()
            self.record_span(trace_id, db_span_id, span_id, "inventory_service", "postgres_query_stock", t_db_start, t_db_end, 200, {"db.latency_ms": db_latency})
            self.log("inventory_service", LogLevel.INFO, f"Reserved {qty} units for {item_id} (postgres {db_latency:.1f}ms)", trace_id)
        except Exception as e:
            t_db_end = time.time()
            self.error_counts["inventory_service"] += 1
            self.record_span(trace_id, db_span_id, span_id, "inventory_service", "postgres_query_stock", t_db_start, t_db_end, 500, {"error": str(e)})
            self.log("inventory_service", LogLevel.ERROR, f"PostgreSQL query error: {str(e)}", trace_id)
            self.record_span(trace_id, span_id, parent_span_id, "inventory_service", "reserve_inventory", t_start, time.time(), 500)
            raise

        t_end = time.time()
        self.record_span(trace_id, span_id, parent_span_id, "inventory_service", "reserve_inventory", t_start, t_end, 200)
        return {"reserved": True, "item_id": item_id, "available_stock": 42}

    async def handle_payment_request(self, trace_id: str, parent_span_id: str, amount: float = 129.50) -> Dict[str, Any]:
        span_id = f"sp_{uuid.uuid4().hex[:8]}"
        t_start = time.time()
        self.request_counts["payment_service"] += 1

        if "payment_service" in self.killed_services:
            self.error_counts["payment_service"] += 1
            t_end = time.time()
            self.record_span(trace_id, span_id, parent_span_id, "payment_service", "process_charge", t_start, t_end, 503)
            self.log("payment_service", LogLevel.ERROR, "payment_service process killed", trace_id)
            raise ConnectionError("payment_service unreachable")

        # Redis cache check for idempotency & rate limits
        redis_span_id = f"sp_redis_{uuid.uuid4().hex[:8]}"
        t_redis_start = time.time()
        try:
            redis_latency = await self.redis.get_or_set(f"idemp_{trace_id}", "PROCESSED")
            t_redis_end = time.time()
            self.record_span(trace_id, redis_span_id, span_id, "payment_service", "redis_check_token", t_redis_start, t_redis_end, 200, {"redis.latency_ms": redis_latency})
        except Exception as e:
            t_redis_end = time.time()
            self.error_counts["payment_service"] += 1
            self.record_span(trace_id, redis_span_id, span_id, "payment_service", "redis_check_token", t_redis_start, t_redis_end, 500, {"error": str(e)})
            self.log("payment_service", LogLevel.ERROR, f"Redis cache failed: {str(e)}", trace_id)
            self.record_span(trace_id, span_id, parent_span_id, "payment_service", "process_charge", t_start, time.time(), 502)
            raise

        # Simulate payment gateway call
        net_delay = self.injected_network_delays.get("payment_service", 0.0)
        await asyncio.sleep(0.025 + net_delay / 1000.0)

        t_end = time.time()
        self.record_span(trace_id, span_id, parent_span_id, "payment_service", "process_charge", t_start, t_end, 200)
        self.log("payment_service", LogLevel.INFO, f"Payment of ${amount:.2f} processed successfully", trace_id)
        return {"status": "SUCCESS", "tx_id": f"tx_{uuid.uuid4().hex[:8]}", "amount": amount}

    async def handle_order_request(self, trace_id: str, parent_span_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        span_id = f"sp_{uuid.uuid4().hex[:8]}"
        t_start = time.time()
        self.request_counts["order_service"] += 1

        if "order_service" in self.killed_services:
            self.error_counts["order_service"] += 1
            t_end = time.time()
            self.record_span(trace_id, span_id, parent_span_id, "order_service", "create_order", t_start, t_end, 503)
            self.log("order_service", LogLevel.ERROR, "order_service crashed", trace_id)
            raise ConnectionError("order_service unreachable")

        # Network delay injection
        net_delay = self.injected_network_delays.get("order_service", 0.0)
        if net_delay > 0:
            await asyncio.sleep(net_delay / 1000.0)

        # 1. Call User Service
        await self.handle_user_request(trace_id, span_id, order_data.get("user_id", "usr_1001"))

        # 2. Call Inventory Service (Can propagate DB bottleneck!)
        try:
            await self.handle_inventory_request(trace_id, span_id, order_data.get("item_id", "prod_99"), order_data.get("qty", 1))
        except Exception as e:
            self.error_counts["order_service"] += 1
            t_end = time.time()
            self.record_span(trace_id, span_id, parent_span_id, "order_service", "create_order", t_start, t_end, 500, {"downstream_error": "inventory_service failed"})
            self.log("order_service", LogLevel.ERROR, f"Order creation failed due to downstream Inventory error: {str(e)}", trace_id)
            raise

        # 3. Call Payment Service
        try:
            await self.handle_payment_request(trace_id, span_id, order_data.get("amount", 129.50))
        except Exception as e:
            self.error_counts["order_service"] += 1
            t_end = time.time()
            self.record_span(trace_id, span_id, parent_span_id, "order_service", "create_order", t_start, t_end, 502, {"downstream_error": "payment_service failed"})
            self.log("order_service", LogLevel.ERROR, f"Order creation failed due to downstream Payment error: {str(e)}", trace_id)
            raise

        t_end = time.time()
        self.record_span(trace_id, span_id, parent_span_id, "order_service", "create_order", t_start, t_end, 200)
        self.log("order_service", LogLevel.INFO, f"Order {order_data.get('order_id', 'ord_1')} completed successfully", trace_id)
        return {"status": "COMPLETED", "order_id": order_data.get("order_id", f"ord_{uuid.uuid4().hex[:6]}")}

    async def execute_gateway_transaction(self, endpoint: str = "/api/checkout", payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Entry point: API Gateway orchestrates incoming client traffic."""
        trace_id = f"tr_{uuid.uuid4().hex[:12]}"
        gateway_span_id = f"sp_gw_{uuid.uuid4().hex[:8]}"
        t_start = time.time()
        self.request_counts["api_gateway"] += 1

        payload = payload or {"user_id": "usr_99", "item_id": "laptop_pro", "qty": 1, "amount": 1299.0}

        try:
            if "api_gateway" in self.killed_services:
                raise ConnectionError("API Gateway connection refused (502 Bad Gateway)")

            if endpoint == "/api/checkout":
                result = await self.handle_order_request(trace_id, gateway_span_id, payload)
            elif endpoint == "/api/user/profile":
                result = await self.handle_user_request(trace_id, gateway_span_id, payload.get("user_id", "usr_99"))
            elif endpoint == "/api/inventory":
                result = await self.handle_inventory_request(trace_id, gateway_span_id, payload.get("item_id", "item_1"))
            else:
                result = {"message": "ok"}

            t_end = time.time()
            self.record_span(trace_id, gateway_span_id, None, "api_gateway", f"POST {endpoint}", t_start, t_end, 200)
            return {"trace_id": trace_id, "status": "success", "data": result}
        except Exception as e:
            t_end = time.time()
            self.error_counts["api_gateway"] += 1
            self.record_span(trace_id, gateway_span_id, None, "api_gateway", f"POST {endpoint}", t_start, t_end, 500, {"error": str(e)})
            self.log("api_gateway", LogLevel.ERROR, f"Gateway request {endpoint} failed: {str(e)}", trace_id)
            return {"trace_id": trace_id, "status": "error", "error": str(e)}

    # --- Metrics Snapshot Generation ---

    def collect_service_metrics(self) -> Dict[str, ServiceSnapshot]:
        now = time.time()
        for sid, svc in self.services.items():
            req_count = self.request_counts[sid]
            err_count = self.error_counts[sid]
            latencies = self.latency_samples[sid]

            # Calculate p95 latency
            if latencies:
                sorted_lat = sorted(latencies)
                p95_idx = int(0.95 * len(sorted_lat))
                p95 = sorted_lat[min(p95_idx, len(sorted_lat) - 1)]
            else:
                p95 = 15.0

            error_rate = (err_count / max(1, req_count)) if req_count > 0 else 0.0
            
            # Base simulated metrics + faults
            cpu = random.uniform(15.0, 30.0)
            if sid in self.injected_cpu_spikes:
                cpu = self.injected_cpu_spikes[sid]
            
            mem = random.uniform(35.0, 50.0)
            if sid in self.injected_memory_leaks:
                mem = self.injected_memory_leaks[sid]

            # Determine health status
            if sid in self.killed_services:
                status = ServiceHealthStatus.UNREACHABLE
            elif error_rate > 0.20 or p95 > 800.0 or cpu > 90.0:
                status = ServiceHealthStatus.CRITICAL
            elif error_rate > 0.05 or p95 > 250.0 or cpu > 70.0:
                status = ServiceHealthStatus.DEGRADED
            else:
                status = ServiceHealthStatus.HEALTHY

            svc.status = status
            svc.cpu_percent = round(cpu, 1)
            svc.memory_percent = round(mem, 1)
            svc.request_rate = round(req_count / 10.0, 1)  # 10s window approx
            svc.error_rate = round(error_rate * 100.0, 2)
            svc.p95_latency_ms = round(p95, 1)
            svc.last_updated = now
            svc.metadata = {
                "active_connections": self.postgres.active_connections if sid == "inventory_service" else None,
                "waiting_queries": self.postgres.waiting_queries if sid == "inventory_service" else None,
                "redis_cache_hits": self.redis.hit_count if sid == "payment_service" else None,
            }

            # Emit metric samples to pipeline
            if self.telemetry:
                self.telemetry.record_metric(MetricSample(service_id=sid, metric_name="cpu_utilization", value=cpu, unit="%"))
                self.telemetry.record_metric(MetricSample(service_id=sid, metric_name="memory_utilization", value=mem, unit="%"))
                self.telemetry.record_metric(MetricSample(service_id=sid, metric_name="error_rate", value=error_rate * 100.0, unit="%"))
                self.telemetry.record_metric(MetricSample(service_id=sid, metric_name="p95_latency", value=p95, unit="ms"))
                if sid == "inventory_service":
                    self.telemetry.record_metric(MetricSample(service_id=sid, metric_name="db_pool_active", value=float(self.postgres.active_connections), unit="conn"))
                    self.telemetry.record_metric(MetricSample(service_id=sid, metric_name="db_pool_waiting", value=float(self.postgres.waiting_queries), unit="conn"))

        return self.services

    # --- Synthetic Traffic Generator ---

    async def _traffic_loop(self):
        while self.traffic_running:
            try:
                # Interleave checkout, user profile, and inventory calls
                r = random.random()
                if r < 0.70:
                    await self.execute_gateway_transaction("/api/checkout")
                elif r < 0.90:
                    await self.execute_gateway_transaction("/api/user/profile")
                else:
                    await self.execute_gateway_transaction("/api/inventory")
            except Exception:
                pass
            await asyncio.sleep(random.uniform(0.1, 0.4))

    def start_traffic(self):
        if not self.traffic_running:
            self.traffic_running = True
            self._traffic_task = asyncio.create_task(self._traffic_loop())

    def stop_traffic(self):
        self.traffic_running = False
        if self._traffic_task:
            self._traffic_task.cancel()
            self._traffic_task = None
