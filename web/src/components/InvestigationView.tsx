import React, { useState } from 'react';
import {
  FileText,
  Play,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Terminal,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Cpu,
  HelpCircle,
} from 'lucide-react';
import { Incident, StructuredDiagnosisOutput, RootCauseCandidate } from '../types';

interface InvestigationViewProps {
  incidents: Incident[];
  activeIncidentId: string | null;
  onSelectIncident: (id: string) => void;
  diagnosis: StructuredDiagnosisOutput | null;
  onRunInvestigation: (incidentId: string) => void;
  loading: boolean;
  onProposeRemediation: (incidentId: string, actionType: string, targetService: string) => void;
}

export const InvestigationView: React.FC<InvestigationViewProps> = ({
  incidents,
  activeIncidentId,
  onSelectIncident,
  diagnosis,
  onRunInvestigation,
  loading,
  onProposeRemediation,
}) => {
  const [showJson, setShowJson] = useState<boolean>(false);
  const [expandedCandidate, setExpandedCandidate] = useState<number | null>(0);

  const selectedIncident = incidents.find((i) => i.incident_id === activeIncidentId) || incidents[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <FileText className="w-5 h-5 text-blue-400" />
            <span>AI Investigation & Evidence-Grounded RCA</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Bounded read-only tool inspection with schema-validated candidate ranking and uncertainty quantification.
          </p>
        </div>

        {/* Incident Select & Action */}
        <div className="flex items-center space-x-3">
          <select
            value={selectedIncident?.incident_id || ''}
            onChange={(e) => onSelectIncident(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
          >
            {incidents.map((inc) => (
              <option key={inc.incident_id} value={inc.incident_id}>
                {inc.incident_id} — {inc.title.slice(0, 30)}
              </option>
            ))}
          </select>

          <button
            onClick={() => selectedIncident && onRunInvestigation(selectedIncident.incident_id)}
            disabled={loading || !selectedIncident}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 transition"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Investigating...' : 'Run Investigation'}</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      {diagnosis ? (
        <div className="space-y-6">
          {/* Diagnostic Summary Card */}
          <div className="rounded-xl bg-gradient-to-r from-slate-900 via-blue-950/30 to-slate-900 border border-slate-800 p-5 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                  Run ID: {diagnosis.run_id}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    diagnosis.status === 'diagnosed'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  Status: {diagnosis.status}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowJson(!showJson)}
                  className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition"
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>{showJson ? 'Hide JSON' : 'View Raw Schema JSON'}</span>
                </button>
              </div>
            </div>

            <div className="mt-4">
              <h2 className="text-base font-semibold text-white">Investigation Synthesis</h2>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">{diagnosis.summary}</p>
            </div>

            {/* Recommended Action Pill */}
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400">Agent Recommendation:</span>
                <span className="font-mono font-bold text-amber-300 bg-amber-950/40 px-2.5 py-0.5 rounded border border-amber-700/50">
                  {diagnosis.recommended_action_type}
                </span>
                <span className="text-[11px] text-slate-500 font-mono">
                  (Requires Human Approval: {diagnosis.requires_approval ? 'YES' : 'NO'})
                </span>
              </div>

              <button
                onClick={() =>
                  onProposeRemediation(
                    diagnosis.incident_id,
                    diagnosis.recommended_action_type,
                    diagnosis.root_cause_candidates[0]?.component_id || 'inventory_service'
                  )
                }
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition"
              >
                <span>Propose Action to Policy Gate</span>
              </button>
            </div>
          </div>

          {/* Raw JSON viewer modal / accordion */}
          {showJson && (
            <div className="rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs overflow-x-auto text-emerald-400 shadow-inner">
              <pre>{JSON.stringify(diagnosis, null, 2)}</pre>
            </div>
          )}

          {/* Root Cause Candidates Table */}
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                <span>Deterministic Evidence Fusion Ranking</span>
              </h3>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Formula: 0.30·Dep + 0.25·Temporal + 0.20·Severity + 0.15·Trace + 0.10·History
              </p>
            </div>

            <div className="space-y-3">
              {diagnosis.root_cause_candidates.map((cand, idx) => {
                const isExpanded = expandedCandidate === idx;
                const b = cand.score_breakdown;

                return (
                  <div
                    key={cand.component_id}
                    className={`rounded-xl border transition ${
                      idx === 0
                        ? 'bg-blue-950/20 border-blue-600/40 ring-1 ring-blue-500/20'
                        : 'bg-slate-950/60 border-slate-800'
                    }`}
                  >
                    <div
                      onClick={() => setExpandedCandidate(isExpanded ? null : idx)}
                      className="p-4 flex items-center justify-between cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono ${
                            idx === 0 ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          #{cand.rank}
                        </span>
                        <div>
                          <span className="font-mono font-bold text-sm text-slate-100">
                            {cand.component_id}
                          </span>
                          <span className="text-[11px] text-slate-400 block sm:inline sm:ml-2">
                            {cand.root_cause_explanation}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <span className="text-xs text-slate-400 block font-mono">Score</span>
                          <span className="text-base font-bold font-mono text-blue-400">
                            {cand.score.toFixed(3)}
                          </span>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Expanded Evidence Breakdown */}
                    {isExpanded && (
                      <div className="px-4 pb-4 pt-2 border-t border-slate-800/80 space-y-3 text-xs">
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center font-mono">
                          <div className="p-2 rounded bg-slate-900 border border-slate-800">
                            <span className="text-[10px] text-slate-400 block">Dep (30%)</span>
                            <span className="font-bold text-slate-200">{b.dependency_relevance}</span>
                          </div>
                          <div className="p-2 rounded bg-slate-900 border border-slate-800">
                            <span className="text-[10px] text-slate-400 block">Temporal (25%)</span>
                            <span className="font-bold text-slate-200">{b.temporal_correlation}</span>
                          </div>
                          <div className="p-2 rounded bg-slate-900 border border-slate-800">
                            <span className="text-[10px] text-slate-400 block">Severity (20%)</span>
                            <span className="font-bold text-slate-200">{b.anomaly_severity}</span>
                          </div>
                          <div className="p-2 rounded bg-slate-900 border border-slate-800">
                            <span className="text-[10px] text-slate-400 block">Trace (15%)</span>
                            <span className="font-bold text-slate-200">{b.trace_propagation}</span>
                          </div>
                          <div className="p-2 rounded bg-slate-900 border border-slate-800">
                            <span className="text-[10px] text-slate-400 block">History (10%)</span>
                            <span className="font-bold text-slate-200">{b.historical_similarity}</span>
                          </div>
                        </div>

                        {/* Evidence References */}
                        <div className="flex flex-wrap gap-2 pt-1 text-[11px]">
                          <span className="text-slate-400 font-medium">Supporting Evidence:</span>
                          {cand.supporting_evidence_ids.length > 0 ? (
                            cand.supporting_evidence_ids.map((id) => (
                              <span
                                key={id}
                                className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono"
                              >
                                {id}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-500 italic">None logged</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bounded Tool Calls Audit Trail */}
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span>Bounded Read-Only Tool Invocations</span>
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {diagnosis.tool_calls.length} / 10 calls used
              </span>
            </div>

            <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
              {diagnosis.tool_calls.map((call, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs font-mono"
                >
                  <div className="flex items-center justify-between text-blue-400 font-bold">
                    <span>
                      #{idx + 1} call: {call.tool_name}()
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(call.timestamp * 1000).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Params: {JSON.stringify(call.parameters)}
                  </div>
                  <div className="text-slate-300 text-[11px] mt-1 bg-slate-900/60 p-1.5 rounded">
                    Result: {call.output_summary}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Uncertainty & Guardrail Notes */}
          {diagnosis.uncertainty_notes.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/50 space-y-1">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold">
                <AlertTriangle className="w-4 h-4" />
                <span>Investigation Guardrails & Uncertainty Notes</span>
              </div>
              <ul className="list-disc list-inside text-xs text-slate-300 space-y-1 pt-1">
                {diagnosis.uncertainty_notes.map((note, idx) => (
                  <li key={idx}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-24 rounded-xl bg-slate-900/60 border border-slate-800">
          <HelpCircle className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <p className="text-sm text-slate-300 font-medium">No investigation result loaded</p>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Select an incident above and click "Run Investigation" to inspect evidence using the bounded AI-SRE agent.
          </p>
        </div>
      )}
    </div>
  );
};
