import React, { useState } from 'react';
import {
  BarChart3,
  Play,
  Download,
  CheckCircle2,
  TrendingUp,
  Clock,
  ShieldCheck,
  Award,
  Layers,
} from 'lucide-react';
import { BenchmarkReport, BenchmarkSummaryItem } from '../types';

interface BenchmarksViewProps {
  benchmarkReport: BenchmarkReport | null;
  onRunBenchmark: (sampleSize: number) => void;
  loading: boolean;
}

export const BenchmarksView: React.FC<BenchmarksViewProps> = ({
  benchmarkReport,
  onRunBenchmark,
  loading,
}) => {
  const [sampleSize, setSampleSize] = useState<number>(10);

  const handleDownloadJson = () => {
    if (!benchmarkReport) return;
    const blob = new Blob([JSON.stringify(benchmarkReport, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aegis-benchmark-${benchmarkReport.experiment_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <span>Research Benchmarking & Baseline Evaluation</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical comparative analysis evaluating Baselines (B1–B4), Full AEGIS, and Ablation studies (PRD Section 15).
          </p>
        </div>

        {/* Run Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400">Scenarios:</span>
            <select
              value={sampleSize}
              onChange={(e) => setSampleSize(Number(e.target.value))}
              className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
            >
              <option value={5}>5 scenarios (Fast)</option>
              <option value={10}>10 scenarios (Standard)</option>
              <option value={20}>20 scenarios (Deep)</option>
              <option value={36}>All 36 scenarios (Full)</option>
            </select>
          </div>

          <button
            onClick={() => onRunBenchmark(sampleSize)}
            disabled={loading}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 transition"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Evaluating...' : 'Run Benchmark'}</span>
          </button>

          {benchmarkReport && (
            <button
              onClick={handleDownloadJson}
              className="flex items-center space-x-1 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
          )}
        </div>
      </div>

      {/* Research Hypotheses Card */}
      <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-blue-400 mb-2">
          Research Hypotheses (PRD Section 15.1)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="font-mono font-bold text-slate-100 block mb-1">
              H1: Topological Evidence Grounding
            </span>
            <span>
              Evidence-grounded RCA combining dependency graph structure with multimodal telemetry achieves superior localization accuracy (Top-1, Top-3, MRR) over telemetry-only LLM prompting.
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="font-mono font-bold text-slate-100 block mb-1">
              H2: Safe Policy-Gated Remediation
            </span>
            <span>
              Human-in-the-loop approval barriers and allowlisted sandboxed execution prevent 100% of unsafe arbitrary remediation actions while maintaining high verified recovery rates.
            </span>
          </div>
        </div>
      </div>

      {/* Benchmark Summary Results Table */}
      {benchmarkReport ? (
        <div className="space-y-6">
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  Experiment ID: {benchmarkReport.experiment_id}
                </span>
                <h3 className="text-sm font-bold text-white">Comparative Evaluation Across Baselines</h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {benchmarkReport.sample_size} Scenarios Tested
              </span>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono text-left">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">System Variant</th>
                    <th className="p-3">Top-1 Accuracy</th>
                    <th className="p-3">Top-3 Accuracy</th>
                    <th className="p-3">MRR Score</th>
                    <th className="p-3">Avg Latency</th>
                    <th className="p-3 text-right">Safety Barrier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {benchmarkReport.summary.map((row) => {
                    const isFullAegis = row.system_variant === 'FULL_AEGIS';

                    return (
                      <tr
                        key={row.system_variant}
                        className={`transition ${
                          isFullAegis
                            ? 'bg-blue-950/30 font-semibold text-blue-200'
                            : 'hover:bg-slate-950/40 text-slate-300'
                        }`}
                      >
                        <td className="p-3 flex items-center space-x-2">
                          {isFullAegis && <Award className="w-4 h-4 text-amber-400" />}
                          <span>{row.system_variant}</span>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center space-x-2">
                            <span>{row.top_1_accuracy_percent}%</span>
                            <div className="w-16 bg-slate-950 rounded-full h-1.5 overflow-hidden">
                              <div
                                style={{ width: `${row.top_1_accuracy_percent}%` }}
                                className={`h-full rounded-full ${
                                  isFullAegis ? 'bg-blue-500' : 'bg-slate-600'
                                }`}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="p-3">{row.top_3_accuracy_percent}%</td>
                        <td className="p-3 font-bold">{row.mrr.toFixed(3)}</td>
                        <td className="p-3 text-slate-400">{row.avg_diagnosis_time_ms} ms</td>
                        <td className="p-3 text-right">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              row.unsafe_actions_prevented_percent === 100
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : 'bg-rose-500/20 text-rose-400'
                            }`}
                          >
                            {row.unsafe_actions_prevented_percent}% Prevented
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-24 rounded-xl bg-slate-900/60 border border-slate-800">
          <BarChart3 className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <p className="text-sm text-slate-300 font-medium">No benchmark evaluation loaded</p>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Click "Run Benchmark" above to evaluate AEGIS against baselines B1–B4 and ablation models.
          </p>
        </div>
      )}
    </div>
  );
};
