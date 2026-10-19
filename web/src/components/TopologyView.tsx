import React, { useState } from 'react';
import {
  Layers,
  Server,
  Database,
  Zap,
  ArrowRight,
  ShieldAlert,
  Info,
  Clock,
  Cpu,
  TrendingUp,
} from 'lucide-react';
import { ServiceSnapshot, ServiceTopology, BlastRadiusResult } from '../types';

interface TopologyViewProps {
  services: Record<string, ServiceSnapshot>;
  topology: ServiceTopology | null;
  onQuickChaos: (faultType: string, targetService: string) => void;
  onInspectEvidence: (serviceId: string) => void;
}

export const TopologyView: React.FC<TopologyViewProps> = ({
  services,
  topology,
  onQuickChaos,
  onInspectEvidence,
}) => {
  const [selectedNode, setSelectedNode] = useState<string>('inventory_service');
  const [blastRadiusData, setBlastRadiusData] = useState<BlastRadiusResult | null>({
    root_service: 'inventory_service',
    impacted_services: ['order_service', 'api_gateway'],
    blast_radius_count: 3,
    blast_radius_score: 0.6,
  });

  // Fixed visual layout coordinates for clean directed graph display
  const nodePositions: Record<string, { x: number; y: number; label: string; type: string }> = {
    api_gateway: { x: 100, y: 160, label: 'API Gateway', type: 'GATEWAY' },
    user_service: { x: 340, y: 70, label: 'User Service', type: 'SERVICE' },
    order_service: { x: 340, y: 250, label: 'Order Service', type: 'SERVICE' },
    payment_service: { x: 580, y: 170, label: 'Payment Service', type: 'SERVICE' },
    inventory_service: { x: 580, y: 310, label: 'Inventory Service', type: 'SERVICE' },
    redis: { x: 780, y: 170, label: 'Redis Cache', type: 'CACHE' },
    postgres: { x: 780, y: 310, label: 'PostgreSQL DB', type: 'DATABASE' },
  };

  const handleSelectNode = async (nodeId: string) => {
    setSelectedNode(nodeId);
    try {
      const res = await fetch(`/api/services/${nodeId}/blast_radius`);
      if (res.ok) {
        const data = await res.json();
        setBlastRadiusData(data);
      }
    } catch (_) {}
  };

  const activeService = services[selectedNode];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <Layers className="w-5 h-5 text-blue-400" />
            <span>Service Dependency Topology</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Interactive directed acyclic dependency graph (BFS/DFS traversal & blast radius impact analysis).
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Healthy</span>
          </span>
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Degraded</span>
          </span>
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>Critical</span>
          </span>
        </div>
      </div>

      {/* Main Grid: SVG Graph + Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SVG Graph Canvas */}
        <div className="lg:col-span-2 rounded-xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl overflow-hidden relative min-h-[440px] flex items-center justify-center">
          <svg className="w-full h-[400px]" viewBox="0 0 920 400">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
              </marker>
              <marker
                id="arrow-active"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
              </marker>
            </defs>

            {/* Dependency Edges */}
            {topology?.edges.map((edge, idx) => {
              const src = nodePositions[edge.source_service_id];
              const tgt = nodePositions[edge.target_service_id];
              if (!src || !tgt) return null;

              const isConnected =
                edge.source_service_id === selectedNode || edge.target_service_id === selectedNode;

              return (
                <g key={`edge-${idx}`}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={isConnected ? '#3b82f6' : '#334155'}
                    strokeWidth={isConnected ? 2.5 : 1.5}
                    strokeDasharray={edge.dependency_type === 'CACHE_LOOKUP' ? '4 3' : 'none'}
                    markerEnd={isConnected ? 'url(#arrow-active)' : 'url(#arrow)'}
                    className="transition-colors duration-300"
                  />
                  {/* Edge Type Label */}
                  <text
                    x={(src.x + tgt.x) / 2}
                    y={(src.y + tgt.y) / 2 - 8}
                    fill="#64748b"
                    fontSize="9"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {edge.dependency_type}
                  </text>
                </g>
              );
            })}

            {/* Nodes */}
            {Object.entries(nodePositions).map(([id, pos]) => {
              const snap = services[id];
              const isSelected = selectedNode === id;
              const isImpacted = blastRadiusData?.impacted_services.includes(id);

              let statusColor = '#10b981'; // Healthy green
              if (snap) {
                if (snap.status === 'CRITICAL' || snap.status === 'UNREACHABLE') statusColor = '#f43f5e';
                else if (snap.status === 'DEGRADED') statusColor = '#f59e0b';
              }

              return (
                <g
                  key={id}
                  onClick={() => handleSelectNode(id)}
                  className="cursor-pointer group select-none"
                >
                  {/* Blast radius ripple effect */}
                  {isImpacted && (
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r="40"
                      fill="none"
                      stroke="#f43f5e"
                      strokeWidth="1.5"
                      strokeDasharray="3 3"
                      className="animate-spin"
                    />
                  )}

                  {/* Outer selection ring */}
                  {isSelected && (
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r="36"
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="2.5"
                      className="animate-pulse"
                    />
                  )}

                  {/* Node Circle */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="28"
                    fill="#0f172a"
                    stroke={statusColor}
                    strokeWidth={isSelected ? 3 : 2}
                    className="transition-all duration-200 group-hover:scale-105"
                  />

                  {/* Node Center Dot */}
                  <circle cx={pos.x} cy={pos.y} r="8" fill={statusColor} />

                  {/* Node Text Label */}
                  <text
                    x={pos.x}
                    y={pos.y + 44}
                    fill={isSelected ? '#60a5fa' : '#cbd5e1'}
                    fontSize="11"
                    fontWeight={isSelected ? 'bold' : 'normal'}
                    fontFamily="sans-serif"
                    textAnchor="middle"
                  >
                    {pos.label}
                  </text>

                  {/* Node Type Pill */}
                  <text
                    x={pos.x}
                    y={pos.y + 56}
                    fill="#64748b"
                    fontSize="8"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {pos.type}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Selected Node Inspector Sidepanel */}
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-5">
          <div className="flex items-start justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-blue-400">
                Node Inspector
              </span>
              <h2 className="text-lg font-bold text-white capitalize">
                {selectedNode.replace(/_/g, ' ')}
              </h2>
            </div>
            {activeService && (
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                  activeService.status === 'HEALTHY'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : activeService.status === 'DEGRADED'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                }`}
              >
                {activeService.status}
              </span>
            )}
          </div>

          {/* Real-time telemetry metrics */}
          {activeService ? (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-300">Operational Signals</h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-400 text-[11px] block flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>p95 Latency</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-slate-100">
                    {activeService.p95_latency_ms} ms
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-400 text-[11px] block flex items-center space-x-1">
                    <TrendingUp className="w-3 h-3 text-slate-500" />
                    <span>Error Rate</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-slate-100">
                    {activeService.error_rate}%
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-400 text-[11px] block flex items-center space-x-1">
                    <Cpu className="w-3 h-3 text-slate-500" />
                    <span>CPU Usage</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-slate-100">
                    {activeService.cpu_percent}%
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-400 text-[11px] block flex items-center space-x-1">
                    <Server className="w-3 h-3 text-slate-500" />
                    <span>Replicas</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-slate-100">
                    {activeService.active_instances} instance
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400">
              Infrastructure node ({selectedNode}). Metrics mapped to owning service.
            </p>
          )}

          {/* Blast Radius Section */}
          {blastRadiusData && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                  <span>Upstream Blast Radius</span>
                </span>
                <span className="text-xs font-mono font-bold text-rose-400">
                  {(blastRadiusData.blast_radius_score * 100).toFixed(0)}% Impact
                </span>
              </div>

              <p className="text-[11px] text-slate-400">
                If <span className="font-mono text-slate-200">{selectedNode}</span> fails, the following upstream dependencies will cascade:
              </p>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {blastRadiusData.impacted_services.length === 0 ? (
                  <span className="text-[11px] text-slate-500 italic">No upstream services impacted (Edge node).</span>
                ) : (
                  blastRadiusData.impacted_services.map((svc) => (
                    <span
                      key={svc}
                      className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono text-[10px]"
                    >
                      {svc}
                    </span>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="space-y-2 pt-3 border-t border-slate-800">
            <button
              onClick={() => onInspectEvidence(selectedNode)}
              className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition shadow"
            >
              <span>Inspect Telemetry Evidence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            {selectedNode in services && (
              <button
                onClick={() => onQuickChaos('CPU_SPIKE', selectedNode)}
                className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
              >
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Simulate Fault on this Service</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
