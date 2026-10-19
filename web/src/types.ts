export type ServiceHealthStatus = 'HEALTHY' | 'DEGRADED' | 'CRITICAL' | 'UNREACHABLE';

export interface ServiceSnapshot {
  service_id: string;
  name: string;
  status: ServiceHealthStatus;
  version: string;
  cpu_percent: number;
  memory_percent: number;
  request_rate: number;
  error_rate: number;
  p95_latency_ms: number;
  active_instances: number;
  last_updated: number;
  metadata: Record<string, any>;
}

export interface DependencyEdge {
  source_service_id: string;
  target_service_id: string;
  dependency_type: string;
  weight: number;
  is_critical: boolean;
}

export interface ServiceTopology {
  nodes: string[];
  edges: DependencyEdge[];
  services?: Record<string, ServiceSnapshot>;
}

export interface BlastRadiusResult {
  root_service: string;
  impacted_services: string[];
  blast_radius_count: number;
  blast_radius_score: number;
}

export type IncidentSeverity = 'P1_CRITICAL' | 'P2_HIGH' | 'P3_MEDIUM' | 'P4_LOW';

export type IncidentStatus =
  | 'OPEN'
  | 'INVESTIGATING'
  | 'DIAGNOSED'
  | 'REMEDIATION_PROPOSED'
  | 'REMEDIATING'
  | 'VERIFYING'
  | 'RESOLVED'
  | 'INCONCLUSIVE';

export interface EvidenceItem {
  evidence_id: string;
  signal_type: 'METRIC' | 'LOG' | 'TRACE' | 'TOPOLOGY' | 'CONFIG';
  service_id: string;
  summary: string;
  timestamp: number;
  metric_ref?: string;
  log_ref?: string;
  trace_ref?: string;
  anomaly_score: number;
  provenance: string;
}

export interface ScoreBreakdown {
  dependency_relevance: number;
  temporal_correlation: number;
  anomaly_severity: number;
  trace_propagation: number;
  historical_similarity: number;
  final_score: number;
}

export interface RootCauseCandidate {
  component_id: string;
  rank: number;
  score: number;
  score_type: string;
  score_breakdown: ScoreBreakdown;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  root_cause_explanation: string;
}

export interface IncidentTimelineEvent {
  timestamp: number;
  event_type: string;
  description: string;
  actor: string;
  metadata?: Record<string, any>;
}

export interface Incident {
  incident_id: string;
  title: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  affected_services: string[];
  root_cause_service?: string;
  created_at: number;
  updated_at: number;
  resolved_at?: number;
  blast_radius: string[];
  evidence_items: EvidenceItem[];
  candidates: RootCauseCandidate[];
  timeline: IncidentTimelineEvent[];
  ground_truth_fault_id?: string;
}

export interface AgentToolCall {
  tool_name: string;
  parameters: Record<string, any>;
  output_summary: string;
  timestamp: number;
}

export interface StructuredDiagnosisOutput {
  schema_version: string;
  run_id: string;
  incident_id: string;
  status: string;
  summary: string;
  root_cause_candidates: RootCauseCandidate[];
  recommended_action_type: string;
  requires_approval: boolean;
  uncertainty_notes: string[];
  tool_calls: AgentToolCall[];
  created_at: number;
}

export type ActionRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export type ActionState =
  | 'PROPOSED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'VERIFYING'
  | 'VERIFIED_RECOVERED'
  | 'NOT_RECOVERED'
  | 'INCONCLUSIVE';

export interface RemediationActionProposal {
  action_id: string;
  incident_id: string;
  action_type: string;
  target_service: string;
  parameters: Record<string, any>;
  risk_level: ActionRiskLevel;
  requires_approval: boolean;
  state: ActionState;
  proposed_by: string;
  proposed_at: number;
  approved_by?: string;
  approved_at?: number;
  rejection_reason?: string;
  executed_at?: number;
  completed_at?: number;
  execution_output?: string;
}

export interface VerificationCheck {
  check_name: string;
  target_metric: string;
  service_id: string;
  before_value: number;
  after_value: number;
  threshold_value: number;
  passed: boolean;
}

export interface VerificationReport {
  verification_id: string;
  action_id: string;
  incident_id: string;
  status: ActionState;
  checks: VerificationCheck[];
  overall_recovery_verified: boolean;
  evaluated_at: number;
  summary: string;
}

export interface ChaosScenario {
  scenario_id: string;
  name: string;
  fault_type: string;
  root_service: string;
  params: Record<string, any>;
  expected_blast_radius: string[];
  ground_truth_remediation: string;
  category: string;
  description: string;
}

export interface ActiveFault {
  fault_id: string;
  fault_type: string;
  target_service: string;
  params: Record<string, any>;
  injected_at: number;
  duration_seconds: number;
  is_active: boolean;
}

export interface BenchmarkSummaryItem {
  system_variant: string;
  scenarios_evaluated: number;
  top_1_accuracy_percent: number;
  top_3_accuracy_percent: number;
  mrr: number;
  avg_diagnosis_time_ms: number;
  unsafe_actions_prevented_percent: number;
}

export interface BenchmarkReport {
  experiment_id: string;
  sample_size: number;
  created_at: number;
  summary: BenchmarkSummaryItem[];
  detailed_runs: Record<string, any[]>;
}

export interface AuditEvent {
  event_id: string;
  actor: string;
  event_type: string;
  entity_id: string;
  timestamp: number;
  details: Record<string, any>;
}

export interface LogEntry {
  log_id: string;
  service_id: string;
  level: string;
  message: string;
  timestamp: number;
  trace_id?: string;
  attributes: Record<string, any>;
}

export interface TraceSpanSummary {
  trace_id: string;
  endpoint: string;
  start_time: number;
  total_duration_ms: number;
  span_count: number;
  has_error: boolean;
  bottleneck_service: string;
  spans?: any[];
}
