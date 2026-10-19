"""
AEGIS Core Pydantic Schemas and Data Models
Defines all domain models, contracts, and state machines.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time
import uuid

# --- Telemetry & Health ---

class ServiceHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNREACHABLE = "UNREACHABLE"

class SignalType(str, Enum):
    METRIC = "METRIC"
    LOG = "LOG"
    TRACE = "TRACE"
    TOPOLOGY = "TOPOLOGY"
    CONFIG = "CONFIG"

class MetricSample(BaseModel):
    service_id: str
    metric_name: str
    value: float
    timestamp: float = Field(default_factory=time.time)
    unit: str = ""
    labels: Dict[str, str] = Field(default_factory=dict)

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

class LogEntry(BaseModel):
    log_id: str = Field(default_factory=lambda: f"log_{uuid.uuid4().hex[:8]}")
    service_id: str
    level: LogLevel
    message: str
    timestamp: float = Field(default_factory=time.time)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

class Span(BaseModel):
    span_id: str = Field(default_factory=lambda: f"span_{uuid.uuid4().hex[:8]}")
    trace_id: str
    parent_span_id: Optional[str] = None
    service_id: str
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    status_code: int = 200
    tags: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)

class ServiceSnapshot(BaseModel):
    service_id: str
    name: str
    status: ServiceHealthStatus
    version: str = "v1.0.0"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    request_rate: float = 0.0
    error_rate: float = 0.0
    p95_latency_ms: float = 0.0
    active_instances: int = 1
    last_updated: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# --- Service Dependency Graph ---

class DependencyEdge(BaseModel):
    source_service_id: str
    target_service_id: str
    dependency_type: str = "SYNC_HTTP" # SYNC_HTTP, ASYNC_QUEUE, DB_CALL, CACHE_LOOKUP
    weight: float = 1.0
    is_critical: bool = True

class ServiceTopology(BaseModel):
    services: Dict[str, ServiceSnapshot]
    dependencies: List[DependencyEdge]

# --- Chaos & Fault Injection ---

class FaultType(str, Enum):
    DB_LATENCY = "DB_LATENCY"
    DB_POOL_EXHAUSTION = "DB_POOL_EXHAUSTION"
    REDIS_FAILURE = "REDIS_FAILURE"
    CPU_SPIKE = "CPU_SPIKE"
    MEMORY_LEAK = "MEMORY_LEAK"
    NETWORK_DELAY = "NETWORK_DELAY"
    SERVICE_CRASH = "SERVICE_CRASH"
    BAD_CONFIG = "BAD_CONFIG"
    CASCADING_FAILURE = "CASCADING_FAILURE"

class FaultInjectionRequest(BaseModel):
    fault_type: FaultType
    target_service: str
    params: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: int = 120
    description: str = ""

class ActiveFault(BaseModel):
    fault_id: str = Field(default_factory=lambda: f"flt_{uuid.uuid4().hex[:8]}")
    fault_type: FaultType
    target_service: str
    params: Dict[str, Any]
    injected_at: float = Field(default_factory=time.time)
    duration_seconds: int
    is_active: bool = True

# --- Anomaly Detection ---

class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AnomalyEvent(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: f"anom_{uuid.uuid4().hex[:8]}")
    service_id: str
    detector_type: str  # RULE_BASED, Z_SCORE, MAD, EWMA, ISOLATION_FOREST
    metric_name: str
    current_value: float
    expected_value: float
    deviation_score: float
    severity: AnomalySeverity
    timestamp: float = Field(default_factory=time.time)
    summary: str

# --- Incident Lifecycle ---

class IncidentSeverity(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    DIAGNOSED = "DIAGNOSED"
    REMEDIATION_PROPOSED = "REMEDIATION_PROPOSED"
    REMEDIATING = "REMEDIATING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    INCONCLUSIVE = "INCONCLUSIVE"

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    signal_type: SignalType
    service_id: str
    summary: str
    timestamp: float
    metric_ref: Optional[str] = None
    log_ref: Optional[str] = None
    trace_ref: Optional[str] = None
    anomaly_score: float = 0.0
    provenance: str = "telemetry_collector"

class ScoreBreakdown(BaseModel):
    dependency_relevance: float = 0.0  # 30%
    temporal_correlation: float = 0.0  # 25%
    anomaly_severity: float = 0.0      # 20%
    trace_propagation: float = 0.0     # 15%
    historical_similarity: float = 0.0 # 10%
    final_score: float = 0.0

class RootCauseCandidate(BaseModel):
    component_id: str
    rank: int
    score: float  # Ranking score (0.0 - 1.0)
    score_type: str = "ranking_score"  # Not probability unless calibrated
    score_breakdown: ScoreBreakdown
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    root_cause_explanation: str = ""

class IncidentTimelineEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    event_type: str  # DETECTED, CORRELATED, INVESTIGATION_STARTED, DIAGNOSED, ACTION_PROPOSED, APPROVED, EXECUTED, VERIFIED
    description: str
    actor: str = "AEGIS_SYSTEM"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Incident(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    affected_services: List[str]
    root_cause_service: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    resolved_at: Optional[float] = None
    blast_radius: List[str] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    candidates: List[RootCauseCandidate] = Field(default_factory=list)
    timeline: List[IncidentTimelineEvent] = Field(default_factory=list)
    ground_truth_fault_id: Optional[str] = None

# --- LLM Investigation Agent ---

class AgentToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    output_summary: str
    timestamp: float = Field(default_factory=time.time)

class StructuredDiagnosisOutput(BaseModel):
    schema_version: str = "1.0"
    incident_id: str
    status: str  # diagnosed | inconclusive | needs_human_review
    summary: str
    root_cause_candidates: List[RootCauseCandidate]
    recommended_action_type: str
    requires_approval: bool = True
    uncertainty_notes: List[str] = Field(default_factory=list)

# --- Safe Remediation & Verification ---

class ActionRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ActionState(str, Enum):
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    VERIFYING = "VERIFYING"
    VERIFIED_RECOVERED = "VERIFIED_RECOVERED"
    NOT_RECOVERED = "NOT_RECOVERED"
    INCONCLUSIVE = "INCONCLUSIVE"

class RemediationActionProposal(BaseModel):
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    incident_id: str
    action_type: str  # Allowlisted: inspect_connection_pool, clear_redis_cache, restart_service, scale_replicas, tune_connection_pool_limit, rollback_deployment
    target_service: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: ActionRiskLevel
    requires_approval: bool
    state: ActionState = ActionState.PROPOSED
    proposed_by: str = "AEGIS_AI_AGENT"
    proposed_at: float = Field(default_factory=time.time)
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    rejection_reason: Optional[str] = None
    executed_at: Optional[float] = None
    completed_at: Optional[float] = None
    execution_output: str = ""

class VerificationCheck(BaseModel):
    check_name: str
    target_metric: str
    service_id: str
    before_value: float
    after_value: float
    threshold_value: float
    passed: bool

class VerificationReport(BaseModel):
    verification_id: str = Field(default_factory=lambda: f"ver_{uuid.uuid4().hex[:8]}")
    action_id: str
    incident_id: str
    status: ActionState
    checks: List[VerificationCheck]
    overall_recovery_verified: bool
    evaluated_at: float = Field(default_factory=time.time)
    summary: str
