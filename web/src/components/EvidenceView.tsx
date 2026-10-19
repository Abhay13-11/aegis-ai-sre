import React, { useState, useEffect } from 'react';
import {
  Search,
  Activity,
  FileText,
  GitCommit,
  Filter,
  Clock,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { api } from '../api';
import { LogEntry, TraceSpanSummary } from '../types';

interface EvidenceViewProps {
  initialServiceId?: string;
}

export const EvidenceView: React.FC<EvidenceViewProps> = ({ initialServiceId }) => {
  const [activeTab, setActiveTab] = useState<'metrics' | 'logs' | 'traces'>('metrics');
  const [selectedService, setSelectedService] = useState<string>(initialServiceId || 'inventory_service');

  // Metrics state
  const [metricName, setMetricName] = useState<string>('p95_latency');
  const [metricStats, setMetricStats] = useState<Record<string, number> | null>(null);

  // Logs state
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logLevel, setLogLevel] = useState<string>('ALL');
  const [logKeyword, setLogKeyword] = useState<string>('');

  // Traces state
  const [traces, setTraces] = useState<TraceSpanSummary[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<any | null>(null);
  const [errorOnlyTraces, setErrorOnlyTraces] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);

  const services = [
    'inventory_service',
    'payment_service',
    'order_service',
    'user_service',
    'api_gateway',
  ];

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const stats = await api.getMetrics(selectedService, metricName, 60);
      setMetricStats(stats);
    } catch (_) {}
    setLoading(false);
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const lvl = logLevel === 'ALL' ? undefined : logLevel;
      const data = await api.getLogs(selectedService, lvl, logKeyword || undefined, 40);
      setLogs(data);
    } catch (_) {}
    setLoading(false);
  };

  const fetchTraces = async () => {
    setLoading(true);
    try {
      const data = await api.getTraces(20, errorOnlyTraces);
      setTraces(data);
      if (data.length > 0 && !selectedTrace) {
        loadTraceDetail(data[0].trace_id);
      }
    } catch (_) {}
    setLoading(false);
  };

  const loadTraceDetail = async (traceId: string) => {
    try {
      const detail = await api.getTraceDetail(traceId);
      setSelectedTrace(detail);
    } catch (_) {}
  };

  useEffect(() => {
    if (activeTab === 'metrics') fetchMetrics();
    else if (activeTab === 'logs') fetchLogs();
    else if (activeTab === 'traces') fetchTraces();
  }, [activeTab, selectedService, metricName, logLevel, errorOnlyTraces]);

  return (
    <div className="space-y-6">
      {/* Header & Signal Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <Search className="w-5 h-5 text-blue-400" />
            <span>Multi-Signal Evidence Explorer</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Query correlated metrics, structured log streams, and distributed trace waterfalls.
          </p>
        </div>

        {/* Signal Subtabs */}
        <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'metrics'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Metrics</span>
          </button>

          <button
            onClick={() => setActiveTab('logs')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'logs'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Logs</span>
          </button>

          <button
            onClick={() => setActiveTab('traces')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'traces'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitCommit className="w-3.5 h-3.5" />
            <span>Traces</span>
          </button>
        </div>
      </div>

      {/* Target Service Selector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-slate-400 font-medium">Service Scope:</span>
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono focus:outline-none focus:border-blue-500"
          >
            {services.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => {
            if (activeTab === 'metrics') fetchMetrics();
            else if (activeTab === 'logs') fetchLogs();
            else if (activeTab === 'traces') fetchTraces();
          }}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Signal</span>
        </button>
      </div>

      {/* TAB 1: METRICS */}
      {activeTab === 'metrics' && (
        <div className="space-y-4">
          <div className="flex items-center space-x-3 text-xs">
            <span className="text-slate-400 font-medium">Metric:</span>
            {['p95_latency', 'error_rate', 'cpu_utilization', 'memory_utilization'].map((m) => (
              <button
                key={m}
                onClick={() => setMetricName(m)}
                className={`px-3 py-1 rounded-lg font-mono transition ${
                  metricName === m
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {metricStats &&
              Object.entries(metricStats).map(([key, val]) => (
                <div key={key} className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow">
                  <span className="text-[11px] font-mono uppercase text-slate-400 block">{key}</span>
                  <span className="text-xl font-bold font-mono text-white mt-1 block">
                    {typeof val === 'number' ? (key.includes('count') ? val : val.toFixed(2)) : val}
                  </span>
                </div>
              ))}
          </div>

          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow">
            <h3 className="text-sm font-semibold text-white mb-2">Signal Provenance & Statistical Semantics</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              AEGIS collects telemetry samples in rolling 60-second windows and calculates median, p95, standard deviation, and MAD (Median Absolute Deviation) to ground anomaly detection. Per PRD Section 7 (FR-014), raw scores are not presented as probabilities unless calibrated against ground-truth validation data.
            </p>
          </div>
        </div>
      )}

      {/* TAB 2: LOGS */}
      {activeTab === 'logs' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-medium">Log Level:</span>
              {['ALL', 'INFO', 'WARN', 'ERROR'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setLogLevel(lvl)}
                  className={`px-2.5 py-1 rounded-md font-mono text-[11px] transition ${
                    logLevel === lvl
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
              <input
                type="text"
                value={logKeyword}
                onChange={(e) => setLogKeyword(e.target.value)}
                placeholder="Filter message or trace ID..."
                className="pl-8 pr-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Log Stream Terminal */}
          <div className="rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs max-h-[500px] overflow-y-auto space-y-2 shadow-inner">
            {logs.length === 0 ? (
              <div className="text-center py-10 text-slate-500">No logs found matching query filters.</div>
            ) : (
              logs.map((entry) => (
                <div
                  key={entry.log_id}
                  className="flex items-start space-x-2 hover:bg-slate-900/60 p-1.5 rounded transition"
                >
                  <span className="text-slate-500 shrink-0 text-[11px]">
                    {new Date(entry.timestamp * 1000).toLocaleTimeString()}
                  </span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 ${
                      entry.level === 'ERROR' || entry.level === 'FATAL'
                        ? 'bg-rose-500/20 text-rose-400'
                        : entry.level === 'WARN'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-blue-500/20 text-blue-400'
                    }`}
                  >
                    {entry.level}
                  </span>
                  <span className="text-slate-400 shrink-0 text-[11px]">[{entry.service_id}]</span>
                  <span className="text-slate-200 flex-1 break-all">{entry.message}</span>
                  {entry.trace_id && (
                    <span className="text-[10px] text-blue-400/80 shrink-0">{entry.trace_id}</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 3: TRACES */}
      {activeTab === 'traces' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Traces List */}
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-4 shadow space-y-3">
            <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
              <span className="font-semibold text-slate-300">Distributed Traces</span>
              <label className="flex items-center space-x-1.5 text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={errorOnlyTraces}
                  onChange={(e) => setErrorOnlyTraces(e.target.checked)}
                  className="rounded border-slate-700 text-rose-600 focus:ring-0"
                />
                <span>Errors Only</span>
              </label>
            </div>

            <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
              {traces.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">No traces recorded yet.</div>
              ) : (
                traces.map((tr) => (
                  <div
                    key={tr.trace_id}
                    onClick={() => loadTraceDetail(tr.trace_id)}
                    className={`p-3 rounded-lg border cursor-pointer text-xs transition ${
                      selectedTrace?.trace_id === tr.trace_id
                        ? 'bg-blue-950/30 border-blue-600/60 ring-1 ring-blue-500/20'
                        : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-slate-400 text-[11px] truncate max-w-[140px]">
                        {tr.trace_id}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                          tr.has_error
                            ? 'bg-rose-500/20 text-rose-400'
                            : 'bg-emerald-500/20 text-emerald-400'
                        }`}
                      >
                        {tr.has_error ? 'ERROR 500' : '200 OK'}
                      </span>
                    </div>

                    <div className="mt-2 flex items-center justify-between">
                      <span className="font-medium text-slate-200">{tr.endpoint}</span>
                      <span className="font-mono text-slate-400 font-semibold">{tr.total_duration_ms.toFixed(1)} ms</span>
                    </div>

                    <div className="mt-1 text-[10px] text-slate-500 font-mono">
                      Bottleneck: <span className="text-amber-400 font-semibold">{tr.bottleneck_service}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Trace Detail & Waterfall */}
          <div className="lg:col-span-2 rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow space-y-4">
            {selectedTrace ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] font-mono text-blue-400 uppercase tracking-wider">
                      Waterfall Span View
                    </span>
                    <h2 className="text-sm font-bold text-white font-mono">{selectedTrace.trace_id}</h2>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      Total: {selectedTrace.total_duration_ms.toFixed(1)} ms
                    </span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Bottleneck: {selectedTrace.bottleneck_service}
                    </span>
                  </div>
                </div>

                {/* Waterfall Spans */}
                <div className="space-y-3 pt-2">
                  {selectedTrace.spans &&
                    selectedTrace.spans.map((sp: any, idx: number) => {
                      const maxDur = Math.max(1, selectedTrace.total_duration_ms);
                      const widthPercent = Math.min(100, Math.max(12, (sp.duration_ms / maxDur) * 100));
                      const isBottleneck = sp.service_id === selectedTrace.bottleneck_service;

                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-mono font-semibold text-slate-200 flex items-center space-x-2">
                              <span>{sp.service_id}</span>
                              <span className="text-slate-500 font-normal">→ {sp.operation}</span>
                              {isBottleneck && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] bg-rose-500/20 text-rose-400 font-bold uppercase">
                                  Bottleneck
                                </span>
                              )}
                            </span>
                            <span className="font-mono text-slate-400 text-[11px]">
                              {sp.duration_ms.toFixed(1)} ms ({sp.status_code})
                            </span>
                          </div>

                          {/* Duration bar */}
                          <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden p-0.5 border border-slate-800">
                            <div
                              style={{ width: `${widthPercent}%` }}
                              className={`h-full rounded-full transition-all duration-300 ${
                                sp.status_code >= 500
                                  ? 'bg-rose-500'
                                  : isBottleneck
                                  ? 'bg-amber-400'
                                  : 'bg-blue-500'
                              }`}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </>
            ) : (
              <div className="text-center py-16 text-slate-500 text-xs">Select a trace to view waterfall spans.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
