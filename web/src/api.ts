import {
  ServiceSnapshot,
  ServiceTopology,
  Incident,
  StructuredDiagnosisOutput,
  RemediationActionProposal,
  VerificationReport,
  ChaosScenario,
  ActiveFault,
  BenchmarkReport,
  AuditEvent,
  LogEntry,
  TraceSpanSummary,
  BlastRadiusResult
} from './types';

const BASE_URL = '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errMsg = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch (_) {}
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  // Health & Overview
  getHealth: () => fetchJson<{
    status: string;
    system: string;
    version: string;
    traffic_running: boolean;
    active_faults_count: number;
    open_incidents_count: number;
  }>('/api/health'),

  // Services & Topology
  getServices: () => fetchJson<Record<string, ServiceSnapshot>>('/api/services'),
  getTopology: () => fetchJson<ServiceTopology>('/api/topology'),
  getServiceTopology: (serviceId: string) =>
    fetchJson<{
      service_id: string;
      dependencies: string[];
      dependents: string[];
      all_downstream: string[];
      all_upstream_impacted: string[];
      blast_radius: BlastRadiusResult;
    }>(`/api/services/${serviceId}/topology`),
  getBlastRadius: (serviceId: string) => fetchJson<BlastRadiusResult>(`/api/services/${serviceId}/blast_radius`),

  // Telemetry
  getMetrics: (serviceId: string, metricName: string, window: number = 60) =>
    fetchJson<Record<string, number>>(`/api/telemetry/metrics?service_id=${serviceId}&metric_name=${metricName}&window=${window}`),
  getLogs: (serviceId?: string, level?: string, keyword?: string, limit: number = 50) => {
    const params = new URLSearchParams();
    if (serviceId) params.append('service_id', serviceId);
    if (level) params.append('level', level);
    if (keyword) params.append('keyword', keyword);
    params.append('limit', limit.toString());
    return fetchJson<LogEntry[]>(`/api/telemetry/logs?${params.toString()}`);
  },
  getTraces: (limit: number = 25, errorOnly: boolean = false) =>
    fetchJson<TraceSpanSummary[]>(`/api/telemetry/traces?limit=${limit}&error_only=${errorOnly}`),
  getTraceDetail: (traceId: string) => fetchJson<any>(`/api/telemetry/traces/${traceId}`),

  // Incidents
  getIncidents: (limit: number = 50) => fetchJson<Incident[]>(`/api/incidents?limit=${limit}`),
  getIncident: (incidentId: string) => fetchJson<Incident>(`/api/incidents/${incidentId}`),
  createManualIncident: (payload: { title: string; severity: string; affected_services: string[]; description?: string }) =>
    fetchJson<Incident>('/api/incidents', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getIncidentEvidence: (incidentId: string) => fetchJson<any>(`/api/incidents/${incidentId}/evidence`),

  // Investigation
  investigateIncident: (incidentId: string) =>
    fetchJson<StructuredDiagnosisOutput>(`/api/incidents/${incidentId}/investigate`, { method: 'POST' }),
  getInvestigationRun: (runId: string) => fetchJson<StructuredDiagnosisOutput>(`/api/investigations/${runId}`),

  // Remediation
  proposeAction: (incidentId: string, actionType: string, targetService: string, parameters: Record<string, any> = {}) =>
    fetchJson<RemediationActionProposal>(`/api/incidents/${incidentId}/actions`, {
      method: 'POST',
      body: JSON.stringify({
        action_type: actionType,
        target_service: targetService,
        parameters,
      }),
    }),
  approveAction: (actionId: string, approver: string = 'Lead SRE Operator') =>
    fetchJson<RemediationActionProposal>(`/api/actions/${actionId}/approve?approver=${encodeURIComponent(approver)}`, {
      method: 'POST',
    }),
  rejectAction: (actionId: string, reason: string = 'Operator rejected proposal') =>
    fetchJson<RemediationActionProposal>(`/api/actions/${actionId}/reject?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    }),
  executeAction: (actionId: string) =>
    fetchJson<{ action: RemediationActionProposal; verification_report: VerificationReport }>(
      `/api/actions/${actionId}/execute`,
      { method: 'POST' }
    ),
  getVerificationReport: (actionId: string) => fetchJson<VerificationReport>(`/api/actions/${actionId}/verification`),

  // Chaos Lab
  getChaosScenarios: () => fetchJson<ChaosScenario[]>('/api/chaos/scenarios'),
  getActiveFaults: () => fetchJson<ActiveFault[]>('/api/chaos/active'),
  injectFault: (payload: { fault_type: string; target_service: string; params: Record<string, any>; description?: string }) =>
    fetchJson<{ fault: ActiveFault; incident?: Incident }>('/api/chaos/inject', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  recoverFault: (faultId: string) => fetchJson<{ recovered: boolean; fault_id: string }>(`/api/chaos/recover/${faultId}`, { method: 'POST' }),
  resetAllChaos: () => fetchJson<{ message: string }>('/api/chaos/reset', { method: 'POST' }),

  // Research Benchmarks
  runBenchmark: (sampleSize: number = 10) =>
    fetchJson<BenchmarkReport>(`/api/benchmarks/run?sample_size=${sampleSize}`, { method: 'POST' }),
  getExperiments: () => fetchJson<BenchmarkReport[]>('/api/experiments'),
  getExperimentResults: (experimentId: string) => fetchJson<BenchmarkReport>(`/api/experiments/${experimentId}/results`),

  // Audit
  getAuditTrail: (limit: number = 100, eventType?: string) => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (eventType) params.append('event_type', eventType);
    return fetchJson<AuditEvent[]>(`/api/audit?${params.toString()}`);
  },

  // Traffic
  toggleTraffic: () => fetchJson<{ traffic_status: string }>('/api/traffic/toggle', { method: 'POST' }),
};
