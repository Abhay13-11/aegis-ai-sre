import React, { useState } from 'react';
import {
  Wrench,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  RotateCcw,
  Clock,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { RemediationActionProposal, VerificationReport, ActionRiskLevel, ActionState } from '../types';

interface RemediationViewProps {
  currentAction: RemediationActionProposal | null;
  verificationReport: VerificationReport | null;
  onApprove: (actionId: string, approver: string) => void;
  onReject: (actionId: string, reason: string) => void;
  onExecute: (actionId: string) => void;
  loading: boolean;
}

export const RemediationView: React.FC<RemediationViewProps> = ({
  currentAction,
  verificationReport,
  onApprove,
  onReject,
  onExecute,
  loading,
}) => {
  const [approverName, setApproverName] = useState('Lead SRE Operator');
  const [rejectReason, setRejectReason] = useState('Requires deeper manual review');
  const [showRejectInput, setShowRejectInput] = useState(false);

  const stateSteps: ActionState[] = [
    'PROPOSED',
    'PENDING_APPROVAL',
    'APPROVED',
    'EXECUTING',
    'VERIFYING',
    'VERIFIED_RECOVERED',
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-xl font-bold text-white flex items-center space-x-2">
          <Wrench className="w-5 h-5 text-blue-400" />
          <span>Safe Remediation Policy Gate & Verification</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Enforces allowlisted action catalog, human approval barriers, sandboxed execution, and telemetry-verified recovery.
        </p>
      </div>

      {currentAction ? (
        <div className="space-y-6">
          {/* Action State Machine Stepper */}
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Remediation Lifecycle State Machine
            </h3>

            <div className="flex flex-wrap items-center justify-between gap-2">
              {stateSteps.map((st, idx) => {
                const isCurrent = currentAction.state === st;
                const isPast =
                  stateSteps.indexOf(currentAction.state) >= idx ||
                  (currentAction.state === 'VERIFIED_RECOVERED' && st !== 'REJECTED');

                return (
                  <div key={st} className="flex items-center space-x-2">
                    <div
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
                        isCurrent
                          ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 ring-2 ring-blue-400/50'
                          : isPast
                          ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/60'
                          : 'bg-slate-950 text-slate-600 border border-slate-800'
                      }`}
                    >
                      <span>{st}</span>
                    </div>
                    {idx < stateSteps.length - 1 && (
                      <span className="text-slate-600 text-xs hidden md:inline">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Proposal Detail Card */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-4">
              <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono text-slate-400">Action ID: {currentAction.action_id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        currentAction.risk_level === 'HIGH'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : currentAction.risk_level === 'MEDIUM'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      Risk: {currentAction.risk_level}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-white font-mono mt-1">
                    {currentAction.action_type}
                  </h2>
                </div>

                <div className="text-right">
                  <span className="text-xs text-slate-400 block font-mono">Target Service</span>
                  <span className="text-sm font-bold font-mono text-blue-400">
                    {currentAction.target_service}
                  </span>
                </div>
              </div>

              {/* Parameters & Preconditions */}
              <div className="space-y-2 text-xs">
                <span className="font-semibold text-slate-300">Action Parameters:</span>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-slate-200">
                  {Object.keys(currentAction.parameters).length > 0
                    ? JSON.stringify(currentAction.parameters, null, 2)
                    : 'Default operational parameters (read-only/standard)'}
                </div>
              </div>

              {/* Execution Output (if executed) */}
              {currentAction.execution_output && (
                <div className="space-y-1 text-xs pt-2">
                  <span className="font-semibold text-slate-300">Execution Output:</span>
                  <div className="p-3 rounded-lg bg-slate-950/80 border border-emerald-800/40 text-emerald-300 font-mono">
                    {currentAction.execution_output}
                  </div>
                </div>
              )}
            </div>

            {/* Approval & Execution Control Panel */}
            <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Operator Approval Gate</span>
              </h3>

              {currentAction.state === 'PENDING_APPROVAL' || currentAction.state === 'PROPOSED' ? (
                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-800/40 text-amber-300">
                    <p className="font-semibold">Human Approval Required</p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Per safety policy NFR-002, state-changing actions require human authorization before sandbox execution.
                    </p>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Approver Name / Role</label>
                    <input
                      type="text"
                      value={approverName}
                      onChange={(e) => setApproverName(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="flex space-x-2 pt-1">
                    <button
                      onClick={() => onApprove(currentAction.action_id, approverName)}
                      disabled={loading}
                      className="flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow transition"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approve Action</span>
                    </button>

                    <button
                      onClick={() => setShowRejectInput(!showRejectInput)}
                      className="px-3 py-2 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-600/30 font-semibold transition"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>

                  {showRejectInput && (
                    <div className="pt-2 space-y-2 border-t border-slate-800">
                      <input
                        type="text"
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        placeholder="Rejection rationale..."
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                      />
                      <button
                        onClick={() => onReject(currentAction.action_id, rejectReason)}
                        className="w-full py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold transition"
                      >
                        Confirm Rejection
                      </button>
                    </div>
                  )}
                </div>
              ) : currentAction.state === 'APPROVED' ? (
                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-emerald-300">
                    <p className="font-semibold">Action Approved</p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Authorized by: <span className="text-white font-bold">{currentAction.approved_by || 'Lead SRE'}</span>
                    </p>
                  </div>

                  <button
                    onClick={() => onExecute(currentAction.action_id)}
                    disabled={loading}
                    className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold shadow-lg shadow-blue-600/30 transition"
                  >
                    <Play className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    <span>{loading ? 'Executing & Verifying...' : 'Execute in Sandbox & Verify'}</span>
                  </button>
                </div>
              ) : (
                <div className="text-xs text-slate-400 space-y-2">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                    Status: <span className="font-mono font-bold text-white">{currentAction.state}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Post-Action Telemetry Verification Card */}
          {verificationReport && (
            <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-slate-400">
                    Verification ID: {verificationReport.verification_id}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      verificationReport.overall_recovery_verified
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {verificationReport.overall_recovery_verified
                      ? 'VERIFIED_RECOVERED'
                      : 'NOT_RECOVERED'}
                  </span>
                </div>

                <span className="text-xs text-slate-400 font-mono">
                  {new Date(verificationReport.evaluated_at * 1000).toLocaleTimeString()}
                </span>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-white">Verification Summary</h4>
                <p className="text-xs text-slate-300 mt-1">{verificationReport.summary}</p>
              </div>

              {/* Verification Checks Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-left">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Check Name</th>
                      <th className="p-2.5">Service</th>
                      <th className="p-2.5">Before Value</th>
                      <th className="p-2.5">After Value</th>
                      <th className="p-2.5">Threshold</th>
                      <th className="p-2.5 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {verificationReport.checks.map((chk, idx) => (
                      <tr key={idx} className="hover:bg-slate-950/40">
                        <td className="p-2.5 text-slate-200 font-bold">{chk.check_name}</td>
                        <td className="p-2.5 text-slate-400">{chk.service_id}</td>
                        <td className="p-2.5 text-rose-400">{chk.before_value}</td>
                        <td className="p-2.5 text-emerald-400 font-bold">{chk.after_value}</td>
                        <td className="p-2.5 text-slate-400">≤ {chk.threshold_value}</td>
                        <td className="p-2.5 text-right">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              chk.passed
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : 'bg-rose-500/20 text-rose-400'
                            }`}
                          >
                            {chk.passed ? 'PASSED' : 'FAILED'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-24 rounded-xl bg-slate-900/60 border border-slate-800">
          <ShieldAlert className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <p className="text-sm text-slate-300 font-medium">No active remediation proposal</p>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Run an AI Investigation from the Incidents view to propose a policy-validated action for approval.
          </p>
        </div>
      )}
    </div>
  );
};
