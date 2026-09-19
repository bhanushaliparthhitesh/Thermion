import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ApiDecision, DecisionDispatch, ChatMessage } from '../types';
import { askAgent, getDecision, getDecisions, runPipeline } from '../api/client';

interface OperatorConsoleProps {
  onNavigateToInitial: () => void;
}

export const OperatorConsole: React.FC<OperatorConsoleProps> = ({ onNavigateToInitial }) => {
  const [decisions, setDecisions] = useState<DecisionDispatch[]>([]);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [isRunningPipeline, setIsRunningPipeline] = useState<boolean>(false);
  const [activeTopology, setActiveTopology] = useState<'pod' | 'manifold' | 'distribution'>('pod');
  const [inputQuery, setInputQuery] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  const activeDecision = decisions.find((d) => d.step === selectedStep) || decisions[0];

  const toDispatch = (decision: ApiDecision): DecisionDispatch => ({
    step: decision.step_id,
    timeUTC: new Date(decision.timestamp).toLocaleTimeString(),
    action: decision.action_label as DecisionDispatch['action'],
    status: decision.cedar_verdict.allowed ? 'APPROVED' : 'BLOCKED',
    riskLevel: decision.safety_filter_verdict.risk_level as DecisionDispatch['riskLevel'],
    cedarReason: decision.cedar_verdict.reason,
    strategyReason: decision.strategy_reason || '—',
    safetyFilterReason: decision.safety_filter_verdict.reason,
    telemetryVectors: {
      temperature_deviation: String(decision.state.temperature_deviation),
      water_usage: String(decision.state.water_usage),
      liquid_outlet_temp: String(decision.state.liquid_outlet_temp),
      cooling_efficiency: String(decision.state.cooling_efficiency),
    },
    cedarSafetyVerdict: {
      risk_score: String(decision.safety_filter_verdict.risk_score),
      intervention_applied: decision.safety_filter_verdict.intervention_applied ? 'Yes' : 'No',
      reason: decision.safety_filter_verdict.reason,
    },
    rewardBreakdown: {
      thermal_stability: String(decision.reward_breakdown.thermal_stability ?? '—'),
      energy_penalty: String(decision.reward_breakdown.energy_penalty ?? '—'),
      water_conservation: String(decision.reward_breakdown.water_conservation ?? '—'),
      equipment_strain: String(decision.reward_breakdown.equipment_strain ?? '—'),
    },
  });

  const loadDecisions = useCallback(async () => {
    try {
      setError(null);
      const received = (await getDecisions()).map(toDispatch);
      setDecisions(received);
      setSelectedStep((current) => current ?? received[0]?.step ?? null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load decisions.');
    }
  }, []);

  useEffect(() => { void loadDecisions(); }, [loadDecisions]);

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleExecuteRun = async () => {
    if (isRunningPipeline) return;
    setIsRunningPipeline(true);
    try {
      setError(null);
      await runPipeline();
      await loadDecisions();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to run the pipeline.');
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const selectDecision = async (stepId: number) => {
    try {
      setError(null);
      const detail = toDispatch(await getDecision(stepId));
      setDecisions((current) => current.map((item) => item.step === stepId ? detail : item));
      setSelectedStep(stepId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load that decision.');
    }
  };

  // Keyboard shortcut listener for Cmd+Enter / Ctrl+Enter to execute run
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleExecuteRun();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isRunningPipeline, decisions]);

  // Handle chat submission
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputQuery.trim();
    if (!query) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setInputQuery('');

    try {
      const reply = await askAgent(query);
      setChatMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'agent',
          text: reply,
          timestamp: 'Explanation Log',
        },
      ]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to get an agent response.');
    }
  };

  if (!activeDecision) {
    return (
      <div className="bg-surface-canvas text-text-primary min-h-screen p-gutter">
        <div className="max-w-7xl mx-auto">
          <header className="h-16 flex items-center justify-between border-b border-border-subtle mb-space-xl">
            <div className="flex items-center gap-space-sm"><span className="w-9 h-9 rounded-lg bg-primary-container/15 text-primary-container flex items-center justify-center material-symbols-outlined">device_thermostat</span><div><div className="font-headline-sm text-headline-sm uppercase">Thermion</div><div className="font-label-code text-label-code text-text-tertiary">THERMAL CONTROL CORE</div></div></div>
            <button className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-body-sm font-semibold flex gap-2 items-center" onClick={() => void loadDecisions()}><span className="material-symbols-outlined text-base">refresh</span>Retry connection</button>
          </header>
          <section className="rounded-xl bg-surface-base border border-border-subtle p-space-xl mb-space-md relative overflow-hidden"><div className="absolute -right-24 -top-24 w-64 h-64 rounded-full bg-primary-container/10 blur-3xl"/><div className="relative"><div className="font-label-code text-label-code text-tertiary-fixed-dim mb-space-sm">LIVE CONNECTION PENDING</div><h1 className="font-headline-lg text-headline-lg mb-space-sm">Operations Console</h1><p className="text-text-secondary max-w-2xl">Your control surface is ready. Live decision history, safety verdicts, and agent explanations will appear when the local API connects.</p><p className="font-label-code text-label-code text-text-tertiary mt-space-md">{error || 'Waiting for decision service at 127.0.0.1:3000'}</p></div></section>
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
            <div className="lg:col-span-3 rounded-xl bg-surface-base border border-border-subtle p-space-md min-h-72"><div className="font-label-caps text-label-caps text-text-tertiary">DECISION FEED</div><h2 className="font-headline-sm text-headline-sm mt-1">History</h2><div className="h-48 flex flex-col items-center justify-center text-center text-text-tertiary gap-space-sm"><span className="material-symbols-outlined text-3xl">history</span><span className="font-body-sm">Live decisions will appear here.</span></div></div>
            <div className="lg:col-span-6 rounded-xl bg-surface-base border border-border-subtle p-space-lg min-h-72"><div className="flex justify-between border-b border-border-subtle pb-space-md"><div><div className="font-label-caps text-label-caps text-text-tertiary">DECISION INSPECTOR</div><h2 className="font-headline-md text-headline-md mt-1">Awaiting live telemetry</h2></div><span className="material-symbols-outlined text-primary-container">monitoring</span></div><div className="grid grid-cols-2 md:grid-cols-4 gap-space-sm py-space-lg">{['Temperature deviation', 'Water usage', 'Liquid outlet', 'Cooling efficiency'].map((label) => <div key={label} className="bg-surface-canvas border border-border-subtle rounded-lg p-space-sm"><div className="font-label-code text-label-code text-text-tertiary">{label}</div><div className="h-5 w-12 bg-surface-elevated rounded mt-space-sm animate-pulse"/></div>)}</div><p className="font-body-sm text-text-secondary">Select a decision when records become available to inspect the exact logged fields.</p></div>
            <div className="lg:col-span-3 rounded-xl bg-surface-base border border-border-subtle p-space-md min-h-72 flex flex-col"><div className="font-label-caps text-label-caps text-text-tertiary">EXPLAINABILITY</div><h2 className="font-headline-sm text-headline-sm mt-1">Operations Copilot</h2><div className="flex-1 flex flex-col items-center justify-center text-center text-text-tertiary gap-space-sm"><span className="material-symbols-outlined text-3xl text-primary-container">smart_toy</span><span className="font-body-sm">Agent questions will be available when connected.</span></div><div className="bg-surface-canvas border border-border-subtle rounded-lg px-space-sm py-2 font-body-sm text-text-tertiary">Ask why a mode was chosen…</div></div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface-canvas font-body-md text-body-md text-on-surface antialiased min-h-screen">
      {error && <div className="fixed top-16 right-4 z-[60] max-w-md rounded-lg border border-error-container bg-surface-base px-4 py-3 text-body-sm text-error shadow-lg">{error}</div>}
      {/* Fixed Header */}
      <header className="fixed top-0 inset-x-0 h-14 z-50 bg-surface-canvas/90 backdrop-blur-xl border-b border-border-subtle shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
        <div className="w-full h-full px-gutter flex items-center justify-between">
          <div className="flex items-center gap-space-lg">
            {/* Header logo & title (Xpath: //header//div[contains(@class, 'items-center')]/div[contains(@class, 'gap-space-sm')]) */}
            <div
              className="flex items-center gap-space-sm cursor-pointer group focus:outline-none"
              onClick={onNavigateToInitial}
              role="button"
              tabIndex={0}
              title="Return to Initial Overview"
            >
              <img
                alt="Thermion logo"
                className="h-8 w-auto object-contain transition-transform group-hover:scale-105"
                src="https://lh3.googleusercontent.com/aida/AEtjO1W6n53-9k4avzpW8nYEpLTR-Iv0LarbWw4kC6SDAGBPlPJfkGK1xGmJ2yQKpZKlSJ3jaDjgdrYsnPNccizfPOqDZDfRT2ShjQuH0ZpZHssV2QyXdIIrcA-FQT9-x3KPuMmCcDbWHFkLuN64Eh0vgknnLIXQcszu6FCYfFGkMjA0r6Y9NGjjDTQtRK9KMJZCn1ME_40FArfi5Wfd9BTLHAuLeMy1afZORHcJXdeZSxFIpASht8MWKBqsmEw"
              />
              <div className="flex flex-col">
                <span className="font-headline-sm text-headline-sm font-semibold tracking-tight text-text-primary uppercase group-hover:text-primary-container transition-colors">
                  Thermion
                </span>
                <span className="font-label-code text-label-code text-text-tertiary tracking-wider uppercase leading-none">
                  Thermal Control Core
                </span>
              </div>
            </div>

            {/* Nav: Home (xpath: //nav//a[@data-path='home']) */}
            <nav
              className="hidden lg:flex items-center h-14 space-x-space-md pl-space-md"
              data-active-classes="text-primary-container shadow-[0_0_16px_-2px_rgba(0,229,255,0.2)] border-b-2 border-primary-container font-medium"
            >
              <a
                className="h-full inline-flex items-center px-space-xs font-body-sm text-body-sm text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                data-path="home"
                href="#home"
                onClick={(e) => {
                  e.preventDefault();
                  onNavigateToInitial();
                }}
              >
                Home
              </a>
              <a
                aria-current="page"
                className="h-full inline-flex items-center px-space-xs transition-colors text-primary-container shadow-[0_0_16px_-2px_rgba(0,229,255,0.2)] border-b-2 border-primary-container font-medium cursor-pointer"
                data-path="dashboard"
                href="#dashboard"
                onClick={(e) => e.preventDefault()}
              >
                Dashboard
              </a>
              <a
                className="h-full inline-flex items-center px-space-xs font-body-sm text-body-sm text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                data-path="safety-logs"
                href="#safety-logs"
                onClick={(e) => {
                  e.preventDefault();
                  void selectDecision(9277);
                }}
              >
                Safety Logs
              </a>
              <a
                className="h-full inline-flex items-center px-space-xs font-body-sm text-body-sm text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                data-path="docs"
                href="#docs"
                onClick={(e) => {
                  e.preventDefault();
                  onNavigateToInitial();
                }}
              >
                Docs
              </a>
            </nav>
          </div>

          <div className="flex items-center gap-space-md">
            <div className="flex items-center gap-space-xs h-7 px-space-sm rounded-full bg-surface-elevated border border-border-subtle">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-thermal-lime opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-status-thermal-lime"></span>
              </span>
              <span className="font-label-code text-label-code text-text-secondary">
                Connected (cluster-iad04-node9)
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Fixed Left Sidebar */}
      <aside className="fixed left-0 top-14 bottom-0 w-64 bg-surface-base border-r border-border-subtle z-40 flex flex-col justify-between p-space-md hidden md:flex">
        <div className="space-y-space-lg">
          <div>
            <div className="px-space-xs pb-space-xs font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider">
              System State
            </div>
            <div className="space-y-space-xs mt-space-xs">
              <div className="p-space-sm rounded-lg bg-surface-canvas border border-border-subtle space-y-space-xs font-label-code text-label-code">
                <div className="flex items-center justify-between">
                  <span className="text-text-tertiary">Node</span>
                  <span className="text-text-secondary">cluster-iad04</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-tertiary">Sync Status</span>
                  <span className="text-status-thermal-lime">Synchronized</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-tertiary">Cluster Gateway</span>
                  <span className="text-primary-container">Online</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-tertiary">Transport</span>
                  <span className="text-text-secondary">gRPC TLS</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-tertiary">Buffer</span>
                  <span className="text-text-secondary">Nominal</span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="px-space-xs pb-space-xs font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider">
              Topology Scope
            </div>
            <nav className="space-y-space-xs mt-space-xs">
              <button
                onClick={() => setActiveTopology('pod')}
                className={`w-full text-left flex items-center justify-between px-space-sm py-space-xs rounded-lg font-label-code text-label-code transition-all cursor-pointer ${
                  activeTopology === 'pod'
                    ? 'bg-surface-canvas border border-border-subtle text-text-primary'
                    : 'text-on-surface-variant hover:bg-surface-elevated hover:text-on-surface'
                }`}
              >
                <span className="flex items-center gap-space-sm">
                  <span className="material-symbols-outlined text-[16px] text-primary-container">
                    dns
                  </span>
                  Active Pod Array
                </span>
              </button>

              <button
                onClick={() => setActiveTopology('manifold')}
                className={`w-full text-left flex items-center justify-between px-space-sm py-space-xs rounded-lg font-label-code text-label-code transition-all cursor-pointer ${
                  activeTopology === 'manifold'
                    ? 'bg-surface-canvas border border-border-subtle text-text-primary'
                    : 'text-on-surface-variant hover:bg-surface-elevated hover:text-on-surface'
                }`}
              >
                <span className="flex items-center gap-space-sm">
                  <span className="material-symbols-outlined text-[16px]">device_hub</span>
                  Manifold Subsystem
                </span>
              </button>

              <button
                onClick={() => setActiveTopology('distribution')}
                className={`w-full text-left flex items-center justify-between px-space-sm py-space-xs rounded-lg font-label-code text-label-code transition-all cursor-pointer ${
                  activeTopology === 'distribution'
                    ? 'bg-surface-canvas border border-border-subtle text-text-primary'
                    : 'text-on-surface-variant hover:bg-surface-elevated hover:text-on-surface'
                }`}
              >
                <span className="flex items-center gap-space-sm">
                  <span className="material-symbols-outlined text-[16px]">tune</span>
                  Distribution Loops
                </span>
              </button>
            </nav>
          </div>
        </div>

        <div className="pt-space-md border-t border-border-subtle flex items-center justify-between font-label-code text-label-code text-text-tertiary">
          <span>NODE: cluster-iad04</span>
          <span className="text-primary-container">SYNCD</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="md:pl-64">
        <main className="relative pt-14 w-full px-gutter min-h-screen bg-surface-canvas">
          <div className="flex flex-col w-full pb-space-xl pt-4">
            {/* Top Predictive Pipeline Controller */}
            <section className="w-full mb-space-md">
              <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-space-md">
                  {/* Left: Pipeline Context */}
                  <div className="flex items-start gap-space-md">
                    <div className="w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center text-primary-container shrink-0 shadow-[0_0_16px_-2px_rgba(0,229,255,0.15)]">
                      <span className="material-symbols-outlined text-[22px]">hub</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-space-xs">
                        <h2 className="font-headline-sm text-headline-sm text-text-primary tracking-tight font-semibold">
                          Run Pipeline
                        </h2>
                        <span className="px-space-xs py-0.5 rounded-full bg-primary-container/10 text-primary-container font-label-code text-label-code">
                          v4.1.8-edge
                        </span>
                      </div>
                      <p className="font-body-sm text-body-sm text-text-secondary mt-0.5">
                        Trigger predictive modeling across active node thermistors and Cedar guardrails.
                      </p>
                    </div>
                  </div>

                  {/* Right: Primary Action */}
                  <div className="flex items-center">
                    <button
                      className="flex items-center gap-space-xs px-space-md py-2 bg-primary-container text-on-primary-container font-body-sm text-body-sm font-semibold rounded-lg hover:shadow-[0_0_20px_rgba(0,229,255,0.45)] active:scale-[0.98] transition-all cursor-pointer"
                      id="btn-execute-run"
                      onClick={handleExecuteRun}
                      disabled={isRunningPipeline}
                    >
                      {isRunningPipeline ? (
                        <>
                          <span className="material-symbols-outlined text-[16px] animate-spin">
                            refresh
                          </span>
                          <span>Running...</span>
                        </>
                      ) : (
                        <>
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-on-primary-container opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-on-primary-container"></span>
                          </span>
                          <span>Execute Run</span>
                          <span className="font-label-code text-label-code opacity-75 ml-1">⌘↵</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Quiet Inline Status Banner */}
                <div
                  className="mt-space-sm bg-surface-canvas/80 px-space-md py-2 rounded-r-lg flex items-center justify-between gap-space-xs"
                  style={{ boxShadow: 'inset 2px 0 0 0 #f3bf26' }}
                >
                  <div className="flex items-center gap-space-xs">
                    <span className="material-symbols-outlined text-tertiary-fixed-dim text-[18px]">
                      verified_user
                    </span>
                    <span className="font-label-code text-label-code text-text-secondary">
                      Cedar guardrail evaluation active. Dispatches verified against safety constraints.
                    </span>
                  </div>
                  <span className="font-label-code text-label-code text-text-tertiary">Enforced</span>
                </div>
              </div>
            </section>

            {/* 3-Column Operator Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
              {/* ============================================== */}
              {/* LEFT COLUMN: DECISION FEED (3 cols)            */}
              {/* ============================================== */}
              <section className="lg:col-span-3 flex flex-col gap-space-sm">
                <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col h-[calc(100vh-14rem)]">
                  {/* Column Header */}
                  <div className="flex items-center justify-between pb-space-sm border-b border-border-subtle">
                    <div>
                      <div className="flex items-center gap-space-xs">
                        <span className="font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider font-semibold">
                          Decision Feed
                        </span>
                      </div>
                      <h3 className="font-headline-sm text-headline-sm text-text-primary font-semibold mt-0.5">
                        History
                      </h3>
                    </div>
                    <span className="font-label-code text-label-code text-text-tertiary">Latest first</span>
                  </div>

                  {/* Scrollable Feed of Decision Cards */}
                  <div
                    className="flex-1 overflow-y-auto space-y-space-xs pr-1 mt-space-sm"
                    id="decision-feed-list"
                  >
                    {decisions.map((decision) => {
                      const isSelected = decision.step === selectedStep;
                      const isBlocked = decision.status === 'BLOCKED';

                      return (
                        <div
                          key={decision.step}
                          onClick={() => void selectDecision(decision.step)}
                          className={`decision-card cursor-pointer rounded-lg p-space-sm bg-surface-canvas transition-all relative overflow-hidden border ${
                            isSelected
                              ? 'border-primary-container/40'
                              : 'border-border-subtle hover:bg-surface-elevated'
                          }`}
                          data-step={decision.step}
                          style={{
                            boxShadow: isSelected ? 'inset 3px 0 0 0 #00e5ff' : undefined,
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <span
                              className={`font-label-code text-label-code font-medium ${
                                isSelected ? 'text-text-primary' : 'text-text-secondary'
                              }`}
                            >
                              #{decision.step}
                            </span>
                            <span className="font-label-code text-label-code text-text-tertiary">
                              {decision.timeUTC}
                            </span>
                          </div>

                          <div className="mt-1">
                            <span
                              className={`font-label-code text-headline-md font-bold tracking-tight leading-none ${
                                isSelected ? 'text-primary-container' : 'text-text-primary'
                              }`}
                            >
                              {decision.action}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 mt-2">
                            {isBlocked ? (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded font-label-code text-label-code bg-error-container/20 text-error border border-error/30">
                                Blocked
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded font-label-code text-label-code bg-status-thermal-lime/10 text-status-thermal-lime border border-status-thermal-lime/20">
                                Approved
                              </span>
                            )}

                            <span
                              className={`inline-flex items-center px-1.5 py-0.5 rounded font-label-code text-label-code ${
                                decision.riskLevel === 'High'
                                  ? 'bg-error-container/20 text-error border border-error/30'
                                  : decision.riskLevel === 'Medium'
                                  ? 'bg-tertiary-container/10 text-tertiary-container border border-tertiary-container/20'
                                  : 'bg-status-thermal-lime/10 text-status-thermal-lime border border-status-thermal-lime/20'
                              }`}
                            >
                              Risk: {decision.riskLevel}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </section>

              {/* ============================================== */}
              {/* CENTER COLUMN: DECISION DETAIL & METRICS (6 cols) */}
              {/* ============================================== */}
              <section className="lg:col-span-6 flex flex-col gap-space-md">
                {/* Active Decision Panel */}
                <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
                  <div className="flex items-center justify-between pb-space-xs border-b border-border-subtle mb-space-md">
                    <span className="font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider font-semibold">
                      Active Decision Dispatch
                    </span>
                    <span className="font-label-code text-label-code text-text-tertiary">
                      Step #{activeDecision.step}
                    </span>
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md">
                    <div>
                      <span className="font-label-caps text-label-caps uppercase text-text-tertiary block mb-1">
                        Selected Action
                      </span>
                      <div className="font-label-code text-display font-extrabold tracking-tight text-text-primary leading-none">
                        {activeDecision.action}
                      </div>
                    </div>

                    {/* Approved / Blocked Ring Indicator */}
                    <div className="flex items-center gap-space-sm bg-surface-canvas px-space-md py-2 rounded-lg border border-border-subtle self-start sm:self-auto">
                      <div
                        className={`relative flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                          activeDecision.status === 'APPROVED'
                            ? 'border-status-thermal-lime shadow-[0_0_12px_rgba(228,242,34,0.3)]'
                            : 'border-error shadow-[0_0_12px_rgba(255,180,171,0.3)]'
                        }`}
                      >
                        <div
                          className={`w-2.5 h-2.5 rounded-full ${
                            activeDecision.status === 'APPROVED'
                              ? 'bg-status-thermal-lime'
                              : 'bg-error'
                          }`}
                        ></div>
                      </div>
                      <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase text-text-tertiary leading-none">
                          Cedar Verdict
                        </span>
                        <span
                          className={`font-label-code text-headline-sm font-bold leading-tight ${
                            activeDecision.status === 'APPROVED'
                              ? 'text-status-thermal-lime'
                              : 'text-error'
                          }`}
                        >
                          {activeDecision.status}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Cedar Verdict Reason */}
                  <div className="mt-space-md pt-space-sm border-t border-border-subtle">
                    <p className="font-label-code text-body-sm text-text-secondary">
                      {activeDecision.cedarReason}
                    </p>
                  </div>
                </div>

                {/* Deterministic Rationale Panel */}
                <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
                  <div className="flex items-center gap-space-xs pb-space-xs border-b border-border-subtle mb-space-sm">
                    <span className="material-symbols-outlined text-primary-container text-[18px]">
                      terminal
                    </span>
                    <h4 className="font-headline-sm text-headline-sm text-text-primary font-semibold">
                      Deterministic Rationale
                    </h4>
                  </div>
                  <div className="space-y-space-sm">
                    <div>
                      <span className="font-label-caps text-label-caps uppercase text-text-tertiary block mb-1">
                        Strategy Reason
                      </span>
                      <p className="font-body-md text-body-md text-text-secondary bg-surface-canvas p-space-sm rounded-lg border border-border-subtle font-label-code">
                        {activeDecision.strategyReason}
                      </p>
                    </div>
                    <div>
                      <span className="font-label-caps text-label-caps uppercase text-text-tertiary block mb-1">
                        Safety Filter Reason
                      </span>
                      <p className="font-body-md text-body-md text-text-secondary bg-surface-canvas p-space-sm rounded-lg border border-border-subtle font-label-code">
                        {activeDecision.safetyFilterReason}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Diagnostic Pair: Telemetry Vectors & Cedar Safety Verdict */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                  {/* Card 1: Telemetry Vectors (Strictly 4 fields) */}
                  <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
                    <div className="flex items-center justify-between pb-space-xs border-b border-border-subtle mb-space-sm">
                      <span className="font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider font-semibold">
                        Telemetry Vectors
                      </span>
                      <span className="material-symbols-outlined text-text-tertiary text-[16px]">
                        sensors
                      </span>
                    </div>
                    <div className="space-y-space-xs font-label-code">
                      <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">temperature_deviation</span>
                        <span className="text-status-thermal-lime font-medium">
                          {activeDecision.telemetryVectors.temperature_deviation}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">water_usage</span>
                        <span className="text-primary-container font-medium">
                          {activeDecision.telemetryVectors.water_usage}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">liquid_outlet_temp</span>
                        <span className="text-text-primary font-medium">
                          {activeDecision.telemetryVectors.liquid_outlet_temp}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">cooling_efficiency</span>
                        <span className="text-status-thermal-lime font-medium">
                          {activeDecision.telemetryVectors.cooling_efficiency}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Cedar Safety Verdict (Strictly 3 fields) */}
                  <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
                    <div className="flex items-center justify-between pb-space-xs border-b border-border-subtle mb-space-sm">
                      <span className="font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider font-semibold">
                        Cedar Safety Verdict
                      </span>
                      <span className="material-symbols-outlined text-text-tertiary text-[16px]">
                        shield
                      </span>
                    </div>
                    <div className="space-y-space-xs font-label-code">
                      <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">risk_score</span>
                        <span
                          className={`font-medium ${
                            parseFloat(activeDecision.cedarSafetyVerdict.risk_score) > 0.5
                              ? 'text-error'
                              : 'text-status-thermal-lime'
                          }`}
                        >
                          {activeDecision.cedarSafetyVerdict.risk_score}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">intervention_applied</span>
                        <span
                          className={`font-medium ${
                            activeDecision.cedarSafetyVerdict.intervention_applied === 'Yes'
                              ? 'text-error'
                              : 'text-text-primary'
                          }`}
                        >
                          {activeDecision.cedarSafetyVerdict.intervention_applied}
                        </span>
                      </div>
                      <div className="flex flex-col py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                        <span className="text-body-sm text-text-secondary">reason</span>
                        <span className="text-text-primary text-body-sm mt-0.5">
                          {activeDecision.cedarSafetyVerdict.reason}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card 3: Reward Breakdown Card */}
                <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
                  <div className="flex items-center justify-between pb-space-xs border-b border-border-subtle mb-space-sm">
                    <span className="font-label-caps text-label-caps uppercase text-text-tertiary tracking-wider font-semibold">
                      Reward Breakdown
                    </span>
                    <span className="font-label-code text-label-code text-text-tertiary">
                      reward_breakdown
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-xs font-label-code">
                    <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                      <span className="text-body-sm text-text-secondary">thermal_stability</span>
                      <span className="text-status-thermal-lime font-medium">
                        {activeDecision.rewardBreakdown.thermal_stability}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                      <span className="text-body-sm text-text-secondary">energy_penalty</span>
                      <span className="text-error font-medium">
                        {activeDecision.rewardBreakdown.energy_penalty}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                      <span className="text-body-sm text-text-secondary">water_conservation</span>
                      <span className="text-primary-container font-medium">
                        {activeDecision.rewardBreakdown.water_conservation}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1.5 bg-surface-canvas px-space-sm rounded border border-border-subtle">
                      <span className="text-body-sm text-text-secondary">equipment_strain</span>
                      <span className="text-text-primary font-medium">
                        {activeDecision.rewardBreakdown.equipment_strain}
                      </span>
                    </div>
                  </div>
                </div>
              </section>

              {/* ============================================== */}
              {/* RIGHT COLUMN: ASK THERMION PANEL (3 cols)      */}
              {/* ============================================== */}
              <section className="lg:col-span-3 flex flex-col gap-space-sm">
                <div className="bg-surface-base rounded-xl p-space-md shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col h-[calc(100vh-14rem)]">
                  {/* Header */}
                  <div className="flex items-center justify-between pb-space-sm border-b border-border-subtle">
                    <div>
                      <h3 className="font-headline-sm text-headline-sm text-text-primary font-semibold">
                        Ask Thermion
                      </h3>
                      <div className="font-label-code text-label-code text-text-tertiary mt-0.5">
                        Explanation Agent Interface
                      </div>
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-surface-canvas flex items-center justify-center text-primary-container border border-border-subtle">
                      <span className="material-symbols-outlined text-[18px]">chat</span>
                    </div>
                  </div>

                  {/* Chat History Area */}
                  <div
                    ref={chatContainerRef}
                    className="flex-1 overflow-y-auto space-y-space-sm pr-1 my-space-sm"
                    id="agent-chat-flow"
                  >
                    {chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex flex-col ${
                          msg.sender === 'user' ? 'items-end' : 'items-start'
                        }`}
                      >
                        <div
                          className={`p-space-sm rounded-lg max-w-[95%] border border-border-subtle ${
                            msg.sender === 'user'
                              ? 'bg-surface-elevated text-text-primary max-w-[90%]'
                              : 'bg-surface-canvas text-text-secondary'
                          }`}
                        >
                          {msg.sender === 'agent' && (
                            <div className="flex items-center gap-1 mb-1">
                              <span className="material-symbols-outlined text-primary-container text-[14px]">
                                smart_toy
                              </span>
                              <span className="font-label-caps text-label-caps uppercase text-primary-container font-semibold">
                                Thermion
                              </span>
                            </div>
                          )}
                          <p className="font-body-sm text-body-sm leading-relaxed">{msg.text}</p>
                        </div>
                        <span className="font-label-code text-label-code text-text-tertiary mt-1">
                          {msg.timestamp}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Quick query chips */}
                  <div className="py-1 flex gap-1 overflow-x-auto no-scrollbar">
                    <button
                      type="button"
                      onClick={() => setInputQuery('Why did you switch modes in this step?')}
                      className="text-[11px] whitespace-nowrap px-2 py-1 rounded bg-surface-canvas border border-border-subtle text-text-tertiary hover:text-text-primary hover:border-primary-container/40 transition-colors"
                    >
                      Why switch modes?
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputQuery('Explain Cedar rule #104 verification')}
                      className="text-[11px] whitespace-nowrap px-2 py-1 rounded bg-surface-canvas border border-border-subtle text-text-tertiary hover:text-text-primary hover:border-primary-container/40 transition-colors"
                    >
                      Cedar rule #104
                    </button>
                  </div>

                  {/* Chat Input Bar */}
                  <div className="mt-auto pt-space-xs border-t border-border-subtle">
                    <form className="relative flex items-center" id="chat-form" onSubmit={handleChatSubmit}>
                      <input
                        className="w-full bg-surface-canvas text-text-primary placeholder:text-text-tertiary font-body-sm text-body-sm pl-space-sm pr-10 py-2.5 rounded-lg border border-border-subtle focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
                        id="chat-input"
                        placeholder="Ask why you picked a certain action..."
                        type="text"
                        value={inputQuery}
                        onChange={(e) => setInputQuery(e.target.value)}
                      />
                      <div className="absolute right-1.5 flex items-center">
                        <button
                          className="w-7 h-7 rounded bg-primary-container text-on-primary-container flex items-center justify-center hover:shadow-[0_0_10px_rgba(0,229,255,0.4)] transition-all cursor-pointer"
                          type="submit"
                          aria-label="Send message"
                        >
                          <span className="material-symbols-outlined text-[16px]">arrow_upward</span>
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
