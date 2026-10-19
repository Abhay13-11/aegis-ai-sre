import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewView } from './components/OverviewView';
import { TopologyView } from './components/TopologyView';
import { IncidentsView } from './components/IncidentsView';
import { EvidenceView } from './components/EvidenceView';
import { InvestigationView } from './components/InvestigationView';
import { RemediationView } from './components/RemediationView';
import { ChaosLabView } from './components/ChaosLabView';
import { BenchmarksView } from './components/BenchmarksView';
import { AuditView } from './components/AuditView';
import { api } from './api';
import {
  ServiceSnapshot,
  ServiceTopology,
  Incident,
  StructuredDiagnosisOutput,
  RemediationActionProposal,
  VerificationReport,
  ChaosScenario,
  ActiveFault,
  BenchmarkReport,
} from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');

  // Core System State
  const [systemStatus, setSystemStatus] = useState<string>('HEALTHY');
  const [trafficRunning, setTrafficRunning] = useState<boolean>(true);
  const [services, setServices] = useState<Record<string, ServiceSnapshot>>({});
  const [topology, setTopology] = useState<ServiceTopology | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [activeFaults, setActiveFaults] = useState<ActiveFault[]>([]);
  const [scenarios, setScenarios] = useState<ChaosScenario[]>([]);

  // Investigation & Remediation State
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [diagnosis, setDiagnosis] = useState<StructuredDiagnosisOutput | null>(null);
  const [currentAction, setCurrentAction] = useState<RemediationActionProposal | null>(null);
  const [verificationReport, setVerificationReport] = useState<VerificationReport | null>(null);

  // Benchmarks State
  const [benchmarkReport, setBenchmarkReport] = useState<BenchmarkReport | null>(null);

  // Loading indicator & toast
  const [loading, setLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // 1. Initial Load: Scenarios & Topology
  useEffect(() => {
    const initData = async () => {
      try {
        const [scns, topo] = await Promise.all([
          api.getChaosScenarios(),
          api.getTopology(),
        ]);
        setScenarios(scns);
        setTopology(topo);
      } catch (err) {
        console.error('Initial load failed:', err);
      }
    };
    initData();
  }, []);

  // 2. Real-Time Telemetry & Incident Poller (every 2.5s)
  const pollTelemetry = async () => {
    try {
      const [health, svcMap, incList, faults] = await Promise.all([
        api.getHealth(),
        api.getServices(),
        api.getIncidents(30),
        api.getActiveFaults(),
      ]);

      setSystemStatus(health.status);
      setTrafficRunning(health.traffic_running);
      setServices(svcMap);
      setIncidents(incList);
      setActiveFaults(faults);

      // Default active incident if none selected
      if (!activeIncidentId && incList.length > 0) {
        const openOne = incList.find((i) => i.status !== 'RESOLVED');
        setActiveIncidentId(openOne ? openOne.incident_id : incList[0].incident_id);
      }
    } catch (_) {}
  };

  useEffect(() => {
    pollTelemetry();
    const interval = setInterval(pollTelemetry, 2500);
    return () => clearInterval(interval);
  }, [activeIncidentId]);

  // Traffic Toggle
  const handleToggleTraffic = async () => {
    try {
      const res = await api.toggleTraffic();
      setTrafficRunning(res.traffic_status === 'RUNNING');
      showToast(`Synthetic traffic generator ${res.traffic_status}`);
    } catch (err: any) {
      showToast(`Error toggling traffic: ${err.message}`);
    }
  };

  // Trigger AI Investigation
  const handleRunInvestigation = async (incidentId: string) => {
    setLoading(true);
    try {
      const diag = await api.investigateIncident(incidentId);
      setDiagnosis(diag);
      setActiveIncidentId(incidentId);
      setCurrentTab('investigation');
      showToast(`AI Investigation complete for ${incidentId}`);
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Investigation error: ${err.message}`);
    }
    setLoading(false);
  };

  // Propose Remediation
  const handleProposeRemediation = async (
    incidentId: string,
    actionType: string = 'tune_connection_pool_limit',
    targetService: string = 'inventory_service'
  ) => {
    setLoading(true);
    try {
      const proposal = await api.proposeAction(incidentId, actionType, targetService, {});
      setCurrentAction(proposal);
      setVerificationReport(null);
      setCurrentTab('remediation');
      showToast(`Remediation proposed: ${actionType} on ${targetService}`);
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Proposal error: ${err.message}`);
    }
    setLoading(false);
  };

  // Approve Action
  const handleApproveAction = async (actionId: string, approver: string) => {
    setLoading(true);
    try {
      const approved = await api.approveAction(actionId, approver);
      setCurrentAction(approved);
      showToast(`Action ${actionId} approved by ${approver}`);
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Approval error: ${err.message}`);
    }
    setLoading(false);
  };

  // Reject Action
  const handleRejectAction = async (actionId: string, reason: string) => {
    setLoading(true);
    try {
      const rejected = await api.rejectAction(actionId, reason);
      setCurrentAction(rejected);
      showToast(`Action ${actionId} rejected: ${reason}`);
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Rejection error: ${err.message}`);
    }
    setLoading(false);
  };

  // Execute Action & Verify
  const handleExecuteAction = async (actionId: string) => {
    setLoading(true);
    try {
      const result = await api.executeAction(actionId);
      setCurrentAction(result.action);
      setVerificationReport(result.verification_report);
      showToast(
        result.verification_report.overall_recovery_verified
          ? 'Recovery Verified! Target service recovered.'
          : 'Executed, but post-action checks did not recover target.'
      );
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Execution error: ${err.message}`);
    }
    setLoading(false);
  };

  // Quick Chaos Injection
  const handleQuickChaos = async (faultType: string, targetService: string) => {
    setLoading(true);
    try {
      const res = await api.injectFault({
        fault_type: faultType,
        target_service: targetService,
        params: {},
        description: `Simulated ${faultType} on ${targetService}`,
      });
      showToast(`Chaos fault injected: ${faultType} on ${targetService}`);
      await pollTelemetry();
      if (res.incident) {
        setActiveIncidentId(res.incident.incident_id);
      }
    } catch (err: any) {
      showToast(`Chaos injection error: ${err.message}`);
    }
    setLoading(false);
  };

  // Recover Fault
  const handleRecoverFault = async (faultId: string) => {
    try {
      await api.recoverFault(faultId);
      showToast(`Fault ${faultId} recovered.`);
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Recovery error: ${err.message}`);
    }
  };

  // Reset All Chaos
  const handleResetAllChaos = async () => {
    setLoading(true);
    try {
      await api.resetAllChaos();
      showToast('All chaos faults cleared. Testbed baseline reset.');
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Reset error: ${err.message}`);
    }
    setLoading(false);
  };

  // Manual Incident Create
  const handleCreateManualIncident = async (title: string, severity: string, affected: string[]) => {
    setLoading(true);
    try {
      const inc = await api.createManualIncident({
        title,
        severity,
        affected_services: affected,
      });
      setActiveIncidentId(inc.incident_id);
      showToast(`Manual incident ${inc.incident_id} created.`);
      await pollTelemetry();
    } catch (err: any) {
      showToast(`Creation error: ${err.message}`);
    }
    setLoading(false);
  };

  // Run Scientific Benchmark
  const handleRunBenchmark = async (sampleSize: number) => {
    setLoading(true);
    try {
      const report = await api.runBenchmark(sampleSize);
      setBenchmarkReport(report);
      showToast(`Benchmark complete: ${sampleSize} scenarios evaluated.`);
    } catch (err: any) {
      showToast(`Benchmark error: ${err.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Global Navbar */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        systemStatus={systemStatus}
        trafficRunning={trafficRunning}
        onToggleTraffic={handleToggleTraffic}
        openIncidentsCount={incidents.filter((i) => i.status !== 'RESOLVED').length}
        activeFaultsCount={activeFaults.length}
        onRefresh={pollTelemetry}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 px-4 py-2.5 rounded-xl bg-slate-900 border border-blue-500/50 text-slate-100 text-xs font-medium shadow-2xl animate-fade-in flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'overview' && (
          <OverviewView
            services={services}
            incidents={incidents}
            activeFaultsCount={activeFaults.length}
            onNavigate={setCurrentTab}
            onQuickChaos={handleQuickChaos}
            onInvestigate={handleRunInvestigation}
          />
        )}

        {currentTab === 'topology' && (
          <TopologyView
            services={services}
            topology={topology}
            onQuickChaos={handleQuickChaos}
            onInspectEvidence={(sid) => {
              setCurrentTab('evidence');
            }}
          />
        )}

        {currentTab === 'incidents' && (
          <IncidentsView
            incidents={incidents}
            onSelectIncident={(id) => setActiveIncidentId(id)}
            onInvestigate={handleRunInvestigation}
            onProposeRemediation={(id) => handleProposeRemediation(id)}
            onCreateManualIncident={handleCreateManualIncident}
          />
        )}

        {currentTab === 'evidence' && <EvidenceView />}

        {currentTab === 'investigation' && (
          <InvestigationView
            incidents={incidents}
            activeIncidentId={activeIncidentId}
            onSelectIncident={(id) => setActiveIncidentId(id)}
            diagnosis={diagnosis}
            onRunInvestigation={handleRunInvestigation}
            loading={loading}
            onProposeRemediation={handleProposeRemediation}
          />
        )}

        {currentTab === 'remediation' && (
          <RemediationView
            currentAction={currentAction}
            verificationReport={verificationReport}
            onApprove={handleApproveAction}
            onReject={handleRejectAction}
            onExecute={handleExecuteAction}
            loading={loading}
          />
        )}

        {currentTab === 'chaos' && (
          <ChaosLabView
            scenarios={scenarios}
            activeFaults={activeFaults}
            onInject={(scn) => handleQuickChaos(scn.fault_type, scn.root_service)}
            onRecover={handleRecoverFault}
            onResetAll={handleResetAllChaos}
            loading={loading}
          />
        )}

        {currentTab === 'benchmarks' && (
          <BenchmarksView
            benchmarkReport={benchmarkReport}
            onRunBenchmark={handleRunBenchmark}
            loading={loading}
          />
        )}

        {currentTab === 'audit' && <AuditView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500 font-mono">
        AEGIS — Adaptive Evidence-Grounded Incident Intelligence & Safe-Remediation System • B.Tech Final Major Project
      </footer>
    </div>
  );
};
