import React, { useState } from 'react';
import {
  Flame,
  Zap,
  RotateCcw,
  AlertTriangle,
  Database,
  Cpu,
  Wifi,
  Layers,
  CheckCircle2,
  Play,
  Clock,
} from 'lucide-react';
import { ChaosScenario, ActiveFault } from '../types';

interface ChaosLabViewProps {
  scenarios: ChaosScenario[];
  activeFaults: ActiveFault[];
  onInject: (scenario: ChaosScenario) => void;
  onRecover: (faultId: string) => void;
  onResetAll: () => void;
  loading: boolean;
}

export const ChaosLabView: React.FC<ChaosLabViewProps> = ({
  scenarios,
  activeFaults,
  onInject,
  onRecover,
  onResetAll,
  loading,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const categories = ['ALL', 'DATABASE', 'CACHE', 'COMPUTE', 'NETWORK', 'CASCADING'];

  const filteredScenarios = scenarios.filter((s) => {
    if (selectedCategory === 'ALL') return true;
    return s.category === selectedCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <Flame className="w-5 h-5 text-amber-500" />
            <span>Chaos Engineering Lab & Scenarios</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Controlled fault injection suite featuring 35+ reproducible microservice incident scenarios with explicit ground truth.
          </p>
        </div>

        <button
          onClick={onResetAll}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition shadow"
        >
          <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
          <span>Reset All Chaos to Baseline</span>
        </button>
      </div>

      {/* Active Faults Banner (if any) */}
      {activeFaults.length > 0 && (
        <div className="rounded-xl bg-amber-950/20 border border-amber-800/60 p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-amber-300 flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400 animate-bounce" />
              <span>Active Chaos Faults ({activeFaults.length})</span>
            </h2>
            <span className="text-xs text-slate-400 font-mono">Simulating real-time failure state</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {activeFaults.map((f) => (
              <div
                key={f.fault_id}
                className="p-3.5 rounded-lg bg-slate-900 border border-amber-700/50 flex items-center justify-between shadow"
              >
                <div>
                  <span className="text-[10px] font-mono font-bold text-amber-400 block">
                    {f.fault_type}
                  </span>
                  <span className="text-xs font-bold text-slate-100 font-mono">
                    Target: {f.target_service}
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">
                    Elapsed: {Math.max(1, Math.round(Date.now() / 1000 - f.injected_at))}s
                  </span>
                </div>

                <button
                  onClick={() => onRecover(f.fault_id)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition"
                >
                  Recover
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex items-center space-x-1 overflow-x-auto pb-1 text-xs scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition ${
              selectedCategory === cat
                ? 'bg-blue-600 text-white shadow'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {cat} {cat === 'ALL' ? `(${scenarios.length})` : ''}
          </button>
        ))}
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredScenarios.map((scn) => {
          const isDB = scn.category === 'DATABASE';
          const isCache = scn.category === 'CACHE';

          return (
            <div
              key={scn.scenario_id}
              className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-sm hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono text-[10px] font-bold text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/40">
                    {scn.scenario_id}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">
                    {scn.category}
                  </span>
                </div>

                <h3 className="font-semibold text-sm text-slate-100">{scn.name}</h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{scn.description}</p>

                {/* Ground Truth Pill Box */}
                <div className="mt-3 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-1 text-[11px] font-mono">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Root Cause:</span>
                    <span className="text-emerald-400 font-bold">{scn.root_service}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Expected Remediation:</span>
                    <span className="text-amber-400">{scn.ground_truth_remediation}</span>
                  </div>
                </div>
              </div>

              {/* Inject Button */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-500">
                  Radius: {scn.expected_blast_radius.length} services
                </span>

                <button
                  onClick={() => onInject(scn)}
                  disabled={loading}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow transition"
                >
                  <Play className="w-3 h-3" />
                  <span>Inject Scenario</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
