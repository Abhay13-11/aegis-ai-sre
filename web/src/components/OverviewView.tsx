import React from 'react';
import {
  Server,
  Zap,
  Clock,
  AlertTriangle,
  Database,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Cpu,
  Layers,
} from 'lucide-react';
import { ServiceSnapshot, Incident } from '../types';

interface OverviewViewProps {
  services: Record<string, ServiceSnapshot>;
  incidents: Incident[];
  activeFaultsCount: number;
  onNavigate: (tab: string) => void;
  onQuickChaos: (faultType: string, targetService: string) => void;
  onInvestigate: (incidentId: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  services,
  incidents,
  activeFaultsCount,
  onNavigate,
  onQuickChaos,
  onInvestigate,
}) => {
  const serviceList = Object.values(services);
  const openIncidents = incidents.filter((i) => i.status !== 'RESOLVED');
  const criticalCount = serviceList.filter((s) => s.status === 'CRITICAL' || s.status === 'UNREACHABLE').length;

  return (
    <div className="space-y-6">
      {/* Platform Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 border border-slate-800 p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-400 border border-blue-500/30">
                Core Principle
              </span>
              <span className="text-xs text-slate-400 font-mono">
                PRD Section 1.0 Baseline
              </span>
            </div>
            <h1 className="text-2xl font-bold text-white mt-1">
              The LLM is an investigator, not the source of truth.
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl">
              AEGIS grounds incident diagnosis in deterministic evidence fusion, graph reachability, policy verification, and post-action telemetry verification before resolution.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => onNavigate('topology')}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition shadow"
            >
              <Layers className="w-4 h-4 text-blue-400" />
              <span>Inspect Topology</span>
            </button>
            <button
              onClick={() => onNavigate('chaos')}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition shadow-lg shadow-blue-600/30"
            >
              <Zap className="w-4 h-4" />
              <span>Launch Chaos Lab</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Incidents */}
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Open Incidents</span>
            <span className={`p-2 rounded-lg ${openIncidents.length > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
              <AlertTriangle className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{openIncidents.length}</span>
            <span className="text-xs text-slate-400 font-mono">
              {openIncidents.length > 0 ? 'Active alerts' : 'Normal'}
            </span>
          </div>
        </div>

        {/* Degraded / Critical Services */}
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Services at Risk</span>
            <span className={`p-2 rounded-lg ${criticalCount > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'}`}>
              <Server className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{criticalCount}</span>
            <span className="text-xs text-slate-400 font-mono">
              of {serviceList.length} monitored
            </span>
          </div>
        </div>

        {/* Active Chaos Injections */}
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Chaos Faults</span>
            <span className={`p-2 rounded-lg ${activeFaultsCount > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-400'}`}>
              <Zap className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{activeFaultsCount}</span>
            <span className="text-xs text-slate-400 font-mono">
              injected in testbed
            </span>
          </div>
        </div>

        {/* Safe Remediation Gate */}
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Remediation Policy Gate</span>
            <span className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <ShieldCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">Active</span>
            <span className="text-xs text-slate-400 font-mono">
              Allowlist + Sandbox
            </span>
          </div>
        </div>
      </div>

      {/* Microservices Health Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white flex items-center space-x-2">
            <Server className="w-4 h-4 text-blue-400" />
            <span>Simulated Microservices Testbed</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Auto-refreshing every 2s
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {serviceList.map((svc) => {
            const isHealthy = svc.status === 'HEALTHY';
            const isDegraded = svc.status === 'DEGRADED';
            const isCritical = svc.status === 'CRITICAL' || svc.status === 'UNREACHABLE';

            return (
              <div
                key={svc.service_id}
                className={`rounded-xl border p-4 transition shadow-sm ${
                  isCritical
                    ? 'bg-rose-950/20 border-rose-800/60 ring-1 ring-rose-500/20'
                    : isDegraded
                    ? 'bg-amber-950/20 border-amber-800/60'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-sm text-slate-100">{svc.name}</h3>
                    <span className="text-[10px] font-mono text-slate-400">{svc.service_id}</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      isHealthy
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : isDegraded
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {svc.status}
                  </span>
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>p95 Latency</span>
                    </span>
                    <span className={`font-mono font-semibold ${svc.p95_latency_ms > 500 ? 'text-rose-400' : 'text-slate-200'}`}>
                      {svc.p95_latency_ms} ms
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center space-x-1">
                      <TrendingUp className="w-3 h-3 text-slate-500" />
                      <span>Error Rate</span>
                    </span>
                    <span className={`font-mono font-semibold ${svc.error_rate > 5 ? 'text-rose-400 font-bold' : 'text-slate-200'}`}>
                      {svc.error_rate}%
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center space-x-1">
                      <Cpu className="w-3 h-3 text-slate-500" />
                      <span>CPU</span>
                    </span>
                    <span className="font-mono text-slate-200">{svc.cpu_percent}%</span>
                  </div>
                </div>

                {/* DB / Cache specific stats */}
                {svc.metadata && svc.metadata.waiting_queries !== null && svc.metadata.waiting_queries !== undefined && (
                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center space-x-1">
                      <Database className="w-3 h-3 text-blue-400" />
                      <span>DB Queue:</span>
                    </span>
                    <span className={`font-mono font-bold ${svc.metadata.waiting_queries > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                      {svc.metadata.waiting_queries} waiting
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Active Incidents & Chaos Quick Trigger Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Open Incidents Column */}
        <div className="lg:col-span-2 rounded-xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Active Incident Queue</span>
            </h2>
            <button
              onClick={() => onNavigate('incidents')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {openIncidents.length === 0 ? (
            <div className="py-8 text-center border border-dashed border-slate-800 rounded-lg">
              <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
              <p className="text-sm text-slate-300 font-medium">All Microservices Healthy</p>
              <p className="text-xs text-slate-500 mt-1">No active incidents detected. Inject a fault from Chaos Lab to simulate detection.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {openIncidents.slice(0, 3).map((inc) => (
                <div
                  key={inc.incident_id}
                  className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-4 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                        {inc.severity}
                      </span>
                      <span className="font-semibold text-sm text-slate-100">{inc.title}</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">
                      {inc.status}
                    </span>
                  </div>

                  <div className="mt-2 text-xs text-slate-400 flex flex-wrap gap-2 items-center">
                    <span>Affected Services:</span>
                    {inc.affected_services.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                        {s}
                      </span>
                    ))}
                    {inc.root_cause_service && (
                      <span className="ml-auto font-mono text-emerald-400 text-xs font-semibold">
                        Root: {inc.root_cause_service}
                      </span>
                    )}
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                    <span className="text-[11px] text-slate-500 font-mono">ID: {inc.incident_id}</span>
                    <button
                      onClick={() => onInvestigate(inc.incident_id)}
                      className="flex items-center space-x-1.5 px-3 py-1 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition"
                    >
                      <span>Investigate</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Chaos Injector */}
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>Quick Chaos Scenarios</span>
            </h2>
            <button
              onClick={() => onNavigate('chaos')}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              All 35+
            </button>
          </div>

          <p className="text-xs text-slate-400 mb-3">
            Inject controlled faults into the testbed to evaluate the AEGIS autonomous detection and recovery loop.
          </p>

          <div className="space-y-2">
            <button
              onClick={() => onQuickChaos('DB_POOL_EXHAUSTION', 'inventory_service')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-950/80 hover:bg-slate-800 border border-slate-800 text-xs transition group"
            >
              <div className="font-semibold text-slate-200 group-hover:text-blue-400">
                PostgreSQL Pool Exhaustion
              </div>
              <div className="text-[11px] text-slate-500">Target: inventory_service (Cascades to Gateway)</div>
            </button>

            <button
              onClick={() => onQuickChaos('REDIS_FAILURE', 'payment_service')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-950/80 hover:bg-slate-800 border border-slate-800 text-xs transition group"
            >
              <div className="font-semibold text-slate-200 group-hover:text-blue-400">
                Redis Outage & Cache Timeout
              </div>
              <div className="text-[11px] text-slate-500">Target: payment_service (502 Gateway Errors)</div>
            </button>

            <button
              onClick={() => onQuickChaos('CPU_SPIKE', 'order_service')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-950/80 hover:bg-slate-800 border border-slate-800 text-xs transition group"
            >
              <div className="font-semibold text-slate-200 group-hover:text-blue-400">
                CPU Contention Spike
              </div>
              <div className="text-[11px] text-slate-500">Target: order_service (High Latency)</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
