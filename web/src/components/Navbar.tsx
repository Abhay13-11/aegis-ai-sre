import React from 'react';
import {
  ShieldAlert,
  Activity,
  Layers,
  Search,
  Wrench,
  Flame,
  BarChart3,
  FileText,
  Play,
  Square,
  RefreshCw,
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  systemStatus: string;
  trafficRunning: boolean;
  onToggleTraffic: () => void;
  openIncidentsCount: number;
  activeFaultsCount: number;
  onRefresh: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  systemStatus,
  trafficRunning,
  onToggleTraffic,
  openIncidentsCount,
  activeFaultsCount,
  onRefresh,
}) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'topology', label: 'Topology', icon: Layers },
    { id: 'incidents', label: 'Incidents', icon: ShieldAlert, badge: openIncidentsCount > 0 ? openIncidentsCount : undefined },
    { id: 'evidence', label: 'Evidence', icon: Search },
    { id: 'investigation', label: 'AI Investigation', icon: FileText },
    { id: 'remediation', label: 'Safe Remediation', icon: Wrench },
    { id: 'chaos', label: 'Chaos Lab', icon: Flame, badge: activeFaultsCount > 0 ? activeFaultsCount : undefined },
    { id: 'benchmarks', label: 'Research Benchmarks', icon: BarChart3 },
    { id: 'audit', label: 'Audit Trail', icon: FileText },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-blue-400/30">
              <ShieldAlert className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-300">
                  AEGIS
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                  v1.0.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono tracking-tight hidden sm:block">
                Adaptive Evidence-Grounded Incident Intelligence
              </p>
            </div>
          </div>

          {/* Quick Controls & Status */}
          <div className="flex items-center space-x-3">
            {/* System Health Pill */}
            <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-medium">
              <span
                className={`w-2 h-2 rounded-full ${
                  systemStatus === 'HEALTHY'
                    ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50 animate-pulse'
                    : 'bg-rose-500 shadow-sm shadow-rose-500/50 animate-ping'
                }`}
              />
              <span className={systemStatus === 'HEALTHY' ? 'text-emerald-400' : 'text-rose-400'}>
                {systemStatus}
              </span>
            </div>

            {/* Synthetic Traffic Generator Button */}
            <button
              onClick={onToggleTraffic}
              title={trafficRunning ? 'Stop synthetic traffic' : 'Start synthetic traffic'}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                trafficRunning
                  ? 'bg-amber-950/40 text-amber-300 border-amber-700/60 hover:bg-amber-900/50'
                  : 'bg-emerald-950/40 text-emerald-300 border-emerald-700/60 hover:bg-emerald-900/50'
              }`}
            >
              {trafficRunning ? <Square className="w-3.5 h-3.5 fill-amber-300" /> : <Play className="w-3.5 h-3.5 fill-emerald-300" />}
              <span>{trafficRunning ? 'Traffic: ON' : 'Traffic: OFF'}</span>
            </button>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              title="Refresh telemetry"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto py-2 scrollbar-none border-t border-slate-800/60">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm shadow-blue-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
                {tab.badge !== undefined && (
                  <span
                    className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      tab.id === 'incidents'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
