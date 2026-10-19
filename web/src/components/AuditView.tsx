import React, { useState, useEffect } from 'react';
import {
  FileText,
  Search,
  Filter,
  RefreshCw,
  Clock,
  Shield,
  User,
  Zap,
} from 'lucide-react';
import { api } from '../api';
import { AuditEvent } from '../types';

export const AuditView: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const filter = eventTypeFilter === 'ALL' ? undefined : eventTypeFilter;
      const data = await api.getAuditTrail(100, filter);
      setEvents(data.reverse()); // most recent first
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchAudit();
  }, [eventTypeFilter]);

  const filteredEvents = events.filter((e) => {
    return (
      e.actor.toLowerCase().includes(search.toLowerCase()) ||
      e.event_type.toLowerCase().includes(search.toLowerCase()) ||
      e.entity_id.toLowerCase().includes(search.toLowerCase()) ||
      JSON.stringify(e.details).toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <FileText className="w-5 h-5 text-blue-400" />
            <span>Immutable Audit Trail & Operator Decisions</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Append-only record of actor proposals, approvals, tool invocations, and state transitions (PRD FR-024).
          </p>
        </div>

        <button
          onClick={fetchAudit}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Audit</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-slate-400 font-medium">Event Type:</span>
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">ALL EVENTS</option>
            <option value="FAULT_INJECTED">FAULT_INJECTED</option>
            <option value="INCIDENT_TRIGGERED">INCIDENT_TRIGGERED</option>
            <option value="INVESTIGATION_CONCLUDED">INVESTIGATION_CONCLUDED</option>
            <option value="ACTION_PROPOSED">ACTION_PROPOSED</option>
            <option value="ACTION_APPROVED">ACTION_APPROVED</option>
            <option value="ACTION_REJECTED">ACTION_REJECTED</option>
            <option value="ACTION_EXECUTING">ACTION_EXECUTING</option>
            <option value="RECOVERY_VERIFIED">RECOVERY_VERIFIED</option>
          </select>
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search actor or details..."
            className="pl-8 pr-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl overflow-x-auto">
        <table className="w-full text-xs font-mono text-left">
          <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="p-3">Timestamp</th>
              <th className="p-3">Actor / Source</th>
              <th className="p-3">Event Type</th>
              <th className="p-3">Entity ID</th>
              <th className="p-3">Details / Context</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-slate-500">
                  No audit events recorded yet.
                </td>
              </tr>
            ) : (
              filteredEvents.map((e) => (
                <tr key={e.event_id} className="hover:bg-slate-950/40 transition">
                  <td className="p-3 text-slate-500 text-[11px] whitespace-nowrap">
                    {new Date(e.timestamp * 1000).toLocaleTimeString()}
                  </td>
                  <td className="p-3 font-semibold text-slate-200">{e.actor}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        e.event_type.includes('APPROVED') || e.event_type.includes('VERIFIED')
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : e.event_type.includes('REJECTED') || e.event_type.includes('FAULT')
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {e.event_type}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400 font-mono text-[11px]">{e.entity_id}</td>
                  <td className="p-3 text-slate-300 text-[11px] max-w-md truncate">
                    {JSON.stringify(e.details)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
