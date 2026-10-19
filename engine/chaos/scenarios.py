"""
AEGIS Benchmark Chaos Scenarios
Defines 35+ controlled incident scenarios with explicit ground truth for scientific evaluation.
"""

from typing import Dict, Any, List
from engine.models.schemas import FaultType

CHAOS_BENCHMARK_SCENARIOS: List[Dict[str, Any]] = [
    # --- Category 1: Database Incidents (Scenarios 1-6) ---
    {
        "scenario_id": "SCN-DB-01",
        "name": "PostgreSQL Connection Pool Exhaustion",
        "fault_type": FaultType.DB_POOL_EXHAUSTION,
        "root_service": "inventory_service",
        "params": {"pool_size": 15},
        "expected_blast_radius": ["inventory_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "tune_connection_pool_limit",
        "category": "DATABASE",
        "description": "Inventory DB pool saturates, causing query timeouts and cascading failures to Order and Gateway."
    },
    {
        "scenario_id": "SCN-DB-02",
        "name": "PostgreSQL Unindexed Table Scan Latency",
        "fault_type": FaultType.DB_LATENCY,
        "root_service": "inventory_service",
        "params": {"latency_ms": 1400.0},
        "expected_blast_radius": ["inventory_service", "order_service"],
        "ground_truth_remediation": "inspect_connection_pool",
        "category": "DATABASE",
        "description": "Heavy sequential scan spikes DB latency to 1.4s, degrading checkout throughput."
    },
    {
        "scenario_id": "SCN-DB-03",
        "name": "PostgreSQL Lock Contention on Inventory SKU",
        "fault_type": FaultType.DB_LATENCY,
        "root_service": "inventory_service",
        "params": {"latency_ms": 2200.0},
        "expected_blast_radius": ["inventory_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "restart_service",
        "category": "DATABASE",
        "description": "Row-level lock contention on hot product causes severe latency spike across downstream calls."
    },
    {
        "scenario_id": "SCN-DB-04",
        "name": "PostgreSQL Sudden Latency Burst",
        "fault_type": FaultType.DB_LATENCY,
        "root_service": "inventory_service",
        "params": {"latency_ms": 950.0},
        "expected_blast_radius": ["inventory_service", "order_service"],
        "ground_truth_remediation": "inspect_connection_pool",
        "category": "DATABASE",
        "description": "Background vacuuming/checkpoint latency burst degrades inventory response times."
    },
    {
        "scenario_id": "SCN-DB-05",
        "name": "PostgreSQL Severe Pool Starvation",
        "fault_type": FaultType.DB_POOL_EXHAUSTION,
        "root_service": "inventory_service",
        "params": {"stall_timeout": 2.5},
        "expected_blast_radius": ["inventory_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "tune_connection_pool_limit",
        "category": "DATABASE",
        "description": "Connection pool leak leaves zero free connections, triggering immediate 500 errors."
    },
    {
        "scenario_id": "SCN-DB-06",
        "name": "Inventory DB Replica Lag Simulation",
        "fault_type": FaultType.DB_LATENCY,
        "root_service": "inventory_service",
        "params": {"latency_ms": 750.0},
        "expected_blast_radius": ["inventory_service"],
        "ground_truth_remediation": "inspect_connection_pool",
        "category": "DATABASE",
        "description": "Replication delay stalls consistency checks during inventory reservation."
    },

    # --- Category 2: Cache & In-Memory Store Incidents (Scenarios 7-12) ---
    {
        "scenario_id": "SCN-CACHE-01",
        "name": "Payment Redis Server Outage",
        "fault_type": FaultType.REDIS_FAILURE,
        "root_service": "payment_service",
        "params": {},
        "expected_blast_radius": ["payment_service", "order_service"],
        "ground_truth_remediation": "clear_redis_cache",
        "category": "CACHE",
        "description": "Redis connection drops, causing payment idempotency checks to fail."
    },
    {
        "scenario_id": "SCN-CACHE-02",
        "name": "Payment Redis Timeout Cascade",
        "fault_type": FaultType.REDIS_FAILURE,
        "root_service": "payment_service",
        "params": {"timeout_ms": 5000},
        "expected_blast_radius": ["payment_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "clear_redis_cache",
        "category": "CACHE",
        "description": "Redis hangs without terminating, blocking worker threads in payment service."
    },
    {
        "scenario_id": "SCN-CACHE-03",
        "name": "Redis Memory Fragmentation / Thrashing",
        "fault_type": FaultType.REDIS_FAILURE,
        "root_service": "payment_service",
        "params": {},
        "expected_blast_radius": ["payment_service"],
        "ground_truth_remediation": "clear_redis_cache",
        "category": "CACHE",
        "description": "Cache thrashing degrades idempotency verification in payment flow."
    },
    {
        "scenario_id": "SCN-CACHE-04",
        "name": "Payment Idempotency Cache Eviction Storm",
        "fault_type": FaultType.REDIS_FAILURE,
        "root_service": "payment_service",
        "params": {},
        "expected_blast_radius": ["payment_service", "order_service"],
        "ground_truth_remediation": "clear_redis_cache",
        "category": "CACHE",
        "description": "Key eviction storm causes duplicate charge validation errors."
    },
    {
        "scenario_id": "SCN-CACHE-05",
        "name": "Redis Connection Spike Rejection",
        "fault_type": FaultType.REDIS_FAILURE,
        "root_service": "payment_service",
        "params": {},
        "expected_blast_radius": ["payment_service"],
        "ground_truth_remediation": "restart_service",
        "category": "CACHE",
        "description": "Max clients limit reached on Redis, denying new connections."
    },
    {
        "scenario_id": "SCN-CACHE-06",
        "name": "Payment Service Redis Latency Spike",
        "fault_type": FaultType.REDIS_FAILURE,
        "root_service": "payment_service",
        "params": {},
        "expected_blast_radius": ["payment_service", "order_service"],
        "ground_truth_remediation": "clear_redis_cache",
        "category": "CACHE",
        "description": "Redis slowlog commands trigger downstream timeout errors in order orchestration."
    },

    # --- Category 3: CPU & Compute Saturation (Scenarios 13-18) ---
    {
        "scenario_id": "SCN-CPU-01",
        "name": "Order Service CPU Starvation (JSON Parsing)",
        "fault_type": FaultType.CPU_SPIKE,
        "root_service": "order_service",
        "params": {"cpu_percent": 98.5},
        "expected_blast_radius": ["order_service", "api_gateway"],
        "ground_truth_remediation": "scale_replicas",
        "category": "COMPUTE",
        "description": "ReDoS or heavy serialization drives CPU to 99%, stalling order processing loop."
    },
    {
        "scenario_id": "SCN-CPU-02",
        "name": "User Service Crypto/Hashing CPU Spike",
        "fault_type": FaultType.CPU_SPIKE,
        "root_service": "user_service",
        "params": {"cpu_percent": 95.0},
        "expected_blast_radius": ["user_service", "api_gateway"],
        "ground_truth_remediation": "scale_replicas",
        "category": "COMPUTE",
        "description": "Excessive bcrypt salt cost during login spikes user_service CPU."
    },
    {
        "scenario_id": "SCN-CPU-03",
        "name": "Payment Service Encryption CPU Throttling",
        "fault_type": FaultType.CPU_SPIKE,
        "root_service": "payment_service",
        "params": {"cpu_percent": 97.0},
        "expected_blast_radius": ["payment_service"],
        "ground_truth_remediation": "scale_replicas",
        "category": "COMPUTE",
        "description": "RSA signature generation causes severe CPU throttling under load."
    },
    {
        "scenario_id": "SCN-CPU-04",
        "name": "API Gateway Regex Route Matching Spike",
        "fault_type": FaultType.CPU_SPIKE,
        "root_service": "api_gateway",
        "params": {"cpu_percent": 99.0},
        "expected_blast_radius": ["api_gateway", "order_service", "user_service"],
        "ground_truth_remediation": "scale_replicas",
        "category": "COMPUTE",
        "description": "Ingress reverse-proxy CPU saturation delays all incoming traffic."
    },
    {
        "scenario_id": "SCN-CPU-05",
        "name": "Inventory Compression CPU Exhaustion",
        "fault_type": FaultType.CPU_SPIKE,
        "root_service": "inventory_service",
        "params": {"cpu_percent": 94.0},
        "expected_blast_radius": ["inventory_service"],
        "ground_truth_remediation": "scale_replicas",
        "category": "COMPUTE",
        "description": "Payload gzip compression consumes all CPU shares in inventory container."
    },
    {
        "scenario_id": "SCN-CPU-06",
        "name": "Order Service Thread Spin Lock",
        "fault_type": FaultType.CPU_SPIKE,
        "root_service": "order_service",
        "params": {"cpu_percent": 99.9},
        "expected_blast_radius": ["order_service", "api_gateway"],
        "ground_truth_remediation": "restart_service",
        "category": "COMPUTE",
        "description": "Worker thread enters infinite loop, driving CPU to 100% until restarted."
    },

    # --- Category 4: Memory Leak & Heap Pressure (Scenarios 19-24) ---
    {
        "scenario_id": "SCN-MEM-01",
        "name": "Order Service Unbounded Memory Leak",
        "fault_type": FaultType.MEMORY_LEAK,
        "root_service": "order_service",
        "params": {"memory_percent": 97.5},
        "expected_blast_radius": ["order_service"],
        "ground_truth_remediation": "restart_service",
        "category": "MEMORY",
        "description": "Unbounded cache in memory triggers GC pauses and impending OOM kill."
    },
    {
        "scenario_id": "SCN-MEM-02",
        "name": "Payment Service Buffer Accumulation Leak",
        "fault_type": FaultType.MEMORY_LEAK,
        "root_service": "payment_service",
        "params": {"memory_percent": 95.0},
        "expected_blast_radius": ["payment_service"],
        "ground_truth_remediation": "restart_service",
        "category": "MEMORY",
        "description": "Failed transaction logs retain memory references, ballooning RSS memory."
    },
    {
        "scenario_id": "SCN-MEM-03",
        "name": "User Service Session Map Memory Leak",
        "fault_type": FaultType.MEMORY_LEAK,
        "root_service": "user_service",
        "params": {"memory_percent": 96.0},
        "expected_blast_radius": ["user_service"],
        "ground_truth_remediation": "restart_service",
        "category": "MEMORY",
        "description": "Abandoned user JWT tokens not evicted from memory store."
    },
    {
        "scenario_id": "SCN-MEM-04",
        "name": "Inventory Service Large Result Set OOM Risk",
        "fault_type": FaultType.MEMORY_LEAK,
        "root_service": "inventory_service",
        "params": {"memory_percent": 98.0},
        "expected_blast_radius": ["inventory_service"],
        "ground_truth_remediation": "restart_service",
        "category": "MEMORY",
        "description": "Full-table catalog queries loaded in memory consume 98% heap."
    },
    {
        "scenario_id": "SCN-MEM-05",
        "name": "API Gateway Connection State Leak",
        "fault_type": FaultType.MEMORY_LEAK,
        "root_service": "api_gateway",
        "params": {"memory_percent": 93.0},
        "expected_blast_radius": ["api_gateway"],
        "ground_truth_remediation": "restart_service",
        "category": "MEMORY",
        "description": "HTTP Keep-Alive sockets leak memory descriptors in proxy layer."
    },
    {
        "scenario_id": "SCN-MEM-06",
        "name": "Payment Service OpenSSL Context Leak",
        "fault_type": FaultType.MEMORY_LEAK,
        "root_service": "payment_service",
        "params": {"memory_percent": 99.0},
        "expected_blast_radius": ["payment_service", "order_service"],
        "ground_truth_remediation": "restart_service",
        "category": "MEMORY",
        "description": "TLS context memory allocation leaks during payment provider handshakes."
    },

    # --- Category 5: Network Partition & Delays (Scenarios 25-30) ---
    {
        "scenario_id": "SCN-NET-01",
        "name": "Cross-AZ Latency Between Order & Payment",
        "fault_type": FaultType.NETWORK_DELAY,
        "root_service": "payment_service",
        "params": {"delay_ms": 750.0},
        "expected_blast_radius": ["payment_service", "order_service"],
        "ground_truth_remediation": "inspect_connection_pool",
        "category": "NETWORK",
        "description": "Network packet loss / cross-AZ link degradation adds 750ms latency."
    },
    {
        "scenario_id": "SCN-NET-02",
        "name": "Order to Inventory Network Packet Jitter",
        "fault_type": FaultType.NETWORK_DELAY,
        "root_service": "inventory_service",
        "params": {"delay_ms": 600.0},
        "expected_blast_radius": ["inventory_service", "order_service"],
        "ground_truth_remediation": "inspect_connection_pool",
        "category": "NETWORK",
        "description": "Network hop jitter between order and inventory service degrades SLA."
    },
    {
        "scenario_id": "SCN-NET-03",
        "name": "Gateway to Order Service Congestion",
        "fault_type": FaultType.NETWORK_DELAY,
        "root_service": "order_service",
        "params": {"delay_ms": 850.0},
        "expected_blast_radius": ["order_service", "api_gateway"],
        "ground_truth_remediation": "restart_service",
        "category": "NETWORK",
        "description": "TCP window exhaustion creates 850ms latency between Gateway and Order."
    },
    {
        "scenario_id": "SCN-NET-04",
        "name": "Payment External Provider Gateway Latency",
        "fault_type": FaultType.NETWORK_DELAY,
        "root_service": "payment_service",
        "params": {"delay_ms": 1100.0},
        "expected_blast_radius": ["payment_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "inspect_connection_pool",
        "category": "NETWORK",
        "description": "Third-party payment banking partner responds with high transmission delay."
    },
    {
        "scenario_id": "SCN-NET-05",
        "name": "Inventory Subnet Routing Stall",
        "fault_type": FaultType.NETWORK_DELAY,
        "root_service": "inventory_service",
        "params": {"delay_ms": 900.0},
        "expected_blast_radius": ["inventory_service", "order_service"],
        "ground_truth_remediation": "restart_service",
        "category": "NETWORK",
        "description": "VPC route table MTU black hole causes retransmissions and high latency."
    },
    {
        "scenario_id": "SCN-NET-06",
        "name": "Order Service Egress Bandwidth Throttling",
        "fault_type": FaultType.NETWORK_DELAY,
        "root_service": "order_service",
        "params": {"delay_ms": 550.0},
        "expected_blast_radius": ["order_service"],
        "ground_truth_remediation": "scale_replicas",
        "category": "NETWORK",
        "description": "Container network interface bandwidth throttled by hypervisor limits."
    },

    # --- Category 6: Bad Config, Service Crash & Cascading Failures (Scenarios 31-36) ---
    {
        "scenario_id": "SCN-CFG-01",
        "name": "Inventory Service Process Crash (SIGSEGV)",
        "fault_type": FaultType.SERVICE_CRASH,
        "root_service": "inventory_service",
        "params": {},
        "expected_blast_radius": ["inventory_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "restart_service",
        "category": "CRASH",
        "description": "Inventory process crashes; upstream services receive 503 Service Unavailable."
    },
    {
        "scenario_id": "SCN-CFG-02",
        "name": "Payment Service Process Crash",
        "fault_type": FaultType.SERVICE_CRASH,
        "root_service": "payment_service",
        "params": {},
        "expected_blast_radius": ["payment_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "restart_service",
        "category": "CRASH",
        "description": "Payment process dies unexpectedly; orders fail with 502 Bad Gateway."
    },
    {
        "scenario_id": "SCN-CFG-03",
        "name": "Bad HTTP Timeout Configuration in Order Service",
        "fault_type": FaultType.BAD_CONFIG,
        "root_service": "order_service",
        "params": {"key": "http_timeout_ms", "value": 15},
        "expected_blast_radius": ["order_service", "api_gateway"],
        "ground_truth_remediation": "rollback_deployment",
        "category": "CONFIG",
        "description": "Unrealistic 15ms timeout misconfiguration causes false client timeouts."
    },
    {
        "scenario_id": "SCN-CFG-04",
        "name": "Cascading Database Pool & Gateway Stall",
        "fault_type": FaultType.CASCADING_FAILURE,
        "root_service": "inventory_service",
        "params": {"root": "inventory_service"},
        "expected_blast_radius": ["inventory_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "tune_connection_pool_limit",
        "category": "CASCADING",
        "description": "DB saturation propagates upstream, choking order queue and crashing gateway."
    },
    {
        "scenario_id": "SCN-CFG-05",
        "name": "User Service Bad Auth Secret Deployment",
        "fault_type": FaultType.BAD_CONFIG,
        "root_service": "user_service",
        "params": {"key": "jwt_secret_version", "value": "INVALID"},
        "expected_blast_radius": ["user_service", "order_service", "api_gateway"],
        "ground_truth_remediation": "rollback_deployment",
        "category": "CONFIG",
        "description": "Corrupt secret key deployed, rejecting valid user sessions."
    },
    {
        "scenario_id": "SCN-CFG-06",
        "name": "Order Service Bad Retry Storm Configuration",
        "fault_type": FaultType.BAD_CONFIG,
        "root_service": "order_service",
        "params": {"key": "max_retries", "value": 50},
        "expected_blast_radius": ["order_service", "payment_service", "inventory_service"],
        "ground_truth_remediation": "rollback_deployment",
        "category": "CONFIG",
        "description": "Excessive retry loops create self-inflicted denial-of-service on downstream dependencies."
    }
]
