import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Clock,
  ArrowRight,
  Plus,
  Search,
  CheckCircle2,
  Cpu,
  Layers,
  ChevronRight,
  Play,
  RotateCcw,
} from 'lucide-react';
import { Incident, IncidentSeverity, IncidentStatus } from '../types';

interface IncidentsViewProps {
  incidents: Incident[];
  onSelectIncident: (incidentId: string) => void;
  onInvestigate: (incidentId: string) => void;
  onProposeRemediation: (incidentId: string) => void;
  onCreateManualIncident: (title: string, severity: string, affected: string[]) => void;
}

export const IncidentsView: React.FC<IncidentsViewProps> = ({
  incidents,
  onSelectIncident,
  onInvestigate,
  onProposeRemediation,
  onCreateManualIncident,
}) => {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(
    incidents.length > 0 ? incidents[0].incident_id : null
  );
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Manual creation form state
  const [manualTitle, setManualTitle] = useState('Manual Chaos Simulation Incident');
  const [manualSeverity, setManualSeverity] = useState('P1_CRITICAL');
  const [manualServices, setManualServices] = useState<string[]>(['inventory_service', 'order_service']);

  const filteredIncidents = incidents.filter((inc) => {
    const matchesStatus = statusFilter === 'ALL' || inc.status === statusFilter;
    const matchesSearch =
      inc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.incident_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.affected_services.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  const activeIncident = incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0];

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreateManualIncident(manualTitle, manualSeverity, manualServices);
    setShowCreateModal(false);
  };

  const toggleService = (svc: string) => {
    if (manualServices.includes(svc)) {
      setManualServices(manualServices.filter((s) => s !== svc));
    } else {
      setManualServices([...manualServices, svc]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>Incident Management & Timeline</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Correlated multi-service incidents, topological blast radius, and chronological investigation history.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/20 transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Simulate Manual Incident</span>
        </button>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident List Column */}
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl space-y-4">
          {/* Filters */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search incidents or services..."
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex items-center space-x-1 overflow-x-auto pb-1 scrollbar-none text-[11px]">
              {['ALL', 'OPEN', 'DIAGNOSED', 'REMEDIATING', 'VERIFYING', 'RESOLVED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-md font-medium whitespace-nowrap transition ${
                    statusFilter === st
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Incident Items */}
          <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
            {filteredIncidents.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs">
                No incidents match the active filters.
              </div>
            ) : (
              filteredIncidents.map((inc) => {
                const isSelected = activeIncident?.incident_id === inc.incident_id;
                const isResolved = inc.status === 'RESOLVED';

                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => {
                      setSelectedIncidentId(inc.incident_id);
                      onSelectIncident(inc.incident_id);
                    }}
                    className={`p-3 rounded-lg border cursor-pointer transition ${
                      isSelected
                        ? 'bg-blue-950/30 border-blue-600/60 ring-1 ring-blue-500/20'
                        : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                          inc.severity === 'P1_CRITICAL'
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {inc.severity}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                          isResolved
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-blue-500/20 text-blue-400'
                        }`}
                      >
                        {inc.status}
                      </span>
                    </div>

                    <h3 className="font-semibold text-xs text-slate-200 mt-2 line-clamp-1">
                      {inc.title}
                    </h3>

                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                      <span>{inc.affected_services.length} services affected</span>
                      <span>{new Date(inc.created_at * 1000).toLocaleTimeString()}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Incident Detail Column */}
        <div className="lg:col-span-2 rounded-xl bg-slate-900/90 border border-slate-800 p-6 shadow-xl space-y-6">
          {activeIncident ? (
            <>
              {/* Incident Header */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono text-slate-400">
                      Incident #{activeIncident.incident_id}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        activeIncident.severity === 'P1_CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {activeIncident.severity}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">
                      {activeIncident.status}
                    </span>
                  </div>

                  <h2 className="text-lg font-bold text-white mt-1">
                    {activeIncident.title}
                  </h2>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => onInvestigate(activeIncident.incident_id)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition shadow-md shadow-blue-600/30"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Run AI Investigation</span>
                  </button>

                  <button
                    onClick={() => onProposeRemediation(activeIncident.incident_id)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
                  >
                    <span>Propose Fix</span>
                  </button>
                </div>
              </div>

              {/* Root Cause Banner (if diagnosed) */}
              {activeIncident.root_cause_service && (
                <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/60 flex items-start space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold">
                      Diagnosed Root Cause
                    </span>
                    <p className="text-sm font-semibold text-white">
                      Isolated to: <span className="font-mono text-emerald-300 font-bold">{activeIncident.root_cause_service}</span>
                    </p>
                    {activeIncident.candidates && activeIncident.candidates[0] && (
                      <p className="text-xs text-slate-300 mt-1">
                        {activeIncident.candidates[0].root_cause_explanation} (Evidence Fusion Score: {activeIncident.candidates[0].score})
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Blast Radius & Affected Services */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5 mb-2">
                    <Cpu className="w-4 h-4 text-blue-400" />
                    <span>Affected Services ({activeIncident.affected_services.length})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeIncident.affected_services.map((s) => (
                      <span
                        key={s}
                        className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 font-mono text-[11px]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5 mb-2">
                    <Layers className="w-4 h-4 text-rose-400" />
                    <span>Topological Blast Radius</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeIncident.blast_radius.map((s) => (
                      <span
                        key={s}
                        className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono text-[11px]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Chronological Incident Timeline */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-blue-400" />
                  <span>Chronological Event Timeline</span>
                </h3>

                <div className="relative pl-6 border-l-2 border-slate-800 space-y-4">
                  {activeIncident.timeline.map((evt, idx) => (
                    <div key={idx} className="relative group">
                      {/* Timeline dot */}
                      <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-blue-500" />

                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono font-bold text-blue-400">{evt.event_type}</span>
                          <span className="text-slate-500 font-mono text-[11px]">
                            {new Date(evt.timestamp * 1000).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-1">{evt.description}</p>
                        <div className="mt-2 text-[10px] text-slate-500 font-mono flex items-center space-x-1">
                          <span>Actor:</span>
                          <span className="text-slate-400 font-semibold">{evt.actor}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-16 text-slate-500">
              No incident selected.
            </div>
          )}
        </div>
      </div>

      {/* Manual Incident Creation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Simulate Operational Incident</h3>
            <p className="text-xs text-slate-400">
              Trigger a manual incident across chosen microservices to test detection, evidence fusion, and AI investigation.
            </p>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Incident Title</label>
                <input
                  type="text"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Severity</label>
                <select
                  value={manualSeverity}
                  onChange={(e) => setManualSeverity(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                >
                  <option value="P1_CRITICAL">P1_CRITICAL</option>
                  <option value="P2_HIGH">P2_HIGH</option>
                  <option value="P3_MEDIUM">P3_MEDIUM</option>
                  <option value="P4_LOW">P4_LOW</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Affected Services</label>
                <div className="grid grid-cols-2 gap-2">
                  {['api_gateway', 'order_service', 'user_service', 'payment_service', 'inventory_service'].map((svc) => (
                    <label
                      key={svc}
                      className="flex items-center space-x-2 p-2 rounded-lg bg-slate-950 border border-slate-800 cursor-pointer hover:bg-slate-800/50"
                    >
                      <input
                        type="checkbox"
                        checked={manualServices.includes(svc)}
                        onChange={() => toggleService(svc)}
                        className="rounded border-slate-700 text-blue-600 focus:ring-0"
                      />
                      <span className="text-[11px] font-mono text-slate-300">{svc}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold shadow transition"
                >
                  Trigger Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
