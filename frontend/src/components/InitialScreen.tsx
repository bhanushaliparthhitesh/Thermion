import React, { useState, useEffect } from 'react';
import { WhitepaperModal } from './WhitepaperModal';

interface InitialScreenProps {
  onNavigateToConsole: () => void;
}

export const InitialScreen: React.FC<InitialScreenProps> = ({ onNavigateToConsole }) => {
  const [isWhitepaperOpen, setIsWhitepaperOpen] = useState(false);
  const [hoveredRack, setHoveredRack] = useState<string | null>(null);
  const [livePue, setLivePue] = useState(1.08);
  const [liveTemp, setLiveTemp] = useState(38.2);

  // Keyboard shortcut listener for Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsWhitepaperOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Subtle live telemetry pulse
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveTemp((prev) => +(prev + (Math.random() * 0.4 - 0.2)).toFixed(1));
      setLivePue((prev) => +(1.08 + (Math.random() * 0.02 - 0.01)).toFixed(2));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const thermistorRacks = [
    { id: 'Rack 01', temp: '24.1°C', color: 'bg-primary-container/20 hover:bg-primary-container/40' },
    { id: 'Rack 02', temp: '26.3°C', color: 'bg-primary-container/30 hover:bg-primary-container/50' },
    { id: 'Rack 03', temp: '28.5°C', color: 'bg-primary-container/40 hover:bg-primary-container/60' },
    { id: 'Rack 04', temp: '31.0°C', color: 'bg-secondary-container/40 hover:bg-secondary-container/60' },
    { id: 'Rack 05', temp: '35.8°C', color: 'bg-status-thermal-lime/30 hover:bg-status-thermal-lime/50' },
    { id: 'Rack 06', temp: '38.2°C', color: 'bg-status-thermal-lime/50 hover:bg-status-thermal-lime/70' },
    { id: 'Rack 07', temp: '36.1°C', color: 'bg-status-thermal-lime/30 hover:bg-status-thermal-lime/50' },
    { id: 'Rack 08', temp: '25.0°C', color: 'bg-primary-container/25 hover:bg-primary-container/45' },
    { id: 'Rack 09', temp: '27.1°C', color: 'bg-primary-container/35 hover:bg-primary-container/55' },
    { id: 'Rack 10', temp: '29.4°C', color: 'bg-primary-container/45 hover:bg-primary-container/65' },
    { id: 'Rack 11', temp: '32.2°C', color: 'bg-secondary-container/50 hover:bg-secondary-container/70' },
    { id: 'Rack 12', temp: '36.4°C', color: 'bg-status-thermal-lime/40 hover:bg-status-thermal-lime/60' },
    { id: 'Rack 13', temp: '39.0°C', color: 'bg-status-thermal-lime/60 hover:bg-status-thermal-lime/80' },
    { id: 'Rack 14', temp: '37.0°C', color: 'bg-status-thermal-lime/35 hover:bg-status-thermal-lime/55' },
    { id: 'Rack 15', temp: '24.8°C', color: 'bg-primary-container/20 hover:bg-primary-container/40' },
    { id: 'Rack 16', temp: '26.9°C', color: 'bg-primary-container/30 hover:bg-primary-container/50' },
    { id: 'Rack 17', temp: '28.8°C', color: 'bg-primary-container/40 hover:bg-primary-container/60' },
    { id: 'Rack 18', temp: '30.9°C', color: 'bg-secondary-container/30 hover:bg-secondary-container/50' },
    { id: 'Rack 19', temp: '35.2°C', color: 'bg-status-thermal-lime/30 hover:bg-status-thermal-lime/50' },
    { id: 'Rack 20', temp: '37.5°C', color: 'bg-status-thermal-lime/40 hover:bg-status-thermal-lime/60' },
    { id: 'Rack 21', temp: '27.4°C', color: 'bg-primary-container/30 hover:bg-primary-container/50' },
  ];

  const handleScrollTo = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    const elem = document.getElementById(id);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-surface-canvas text-on-surface font-body-md text-body-md antialiased selection:bg-primary-container selection:text-surface-canvas">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-surface-canvas/80 backdrop-blur-md border-b border-border-subtle">
        <div className="h-16 max-w-7xl mx-auto px-gutter flex items-center justify-between gap-space-md">
          <div className="flex items-center gap-space-md shrink-0">
            <a
              className="flex items-center gap-space-sm group focus:outline-none cursor-pointer"
              data-path="overview"
              href="#"
              onClick={(e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              <img
                alt="Thermion Logo"
                className="h-8 w-auto object-contain"
                src="https://lh3.googleusercontent.com/aida/AEtjO1W6n53-9k4avzpW8nYEpLTR-Iv0LarbWw4kC6SDAGBPlPJfkGK1xGmJ2yQKpZKlSJ3jaDjgdrYsnPNccizfPOqDZDfRT2ShjQuH0ZpZHssV2QyXdIIrcA-FQT9-x3KPuMmCcDbWHFkLuN64Eh0vgknnLIXQcszu6FCYfFGkMjA0r6Y9NGjjDTQtRK9KMJZCn1ME_40FArfi5Wfd9BTLHAuLeMy1afZORHcJXdeZSxFIpASht8MWKBqsmEw"
              />
              <span className="text-text-primary font-headline-sm text-headline-sm tracking-tight">
                Thermion
              </span>
            </a>
            <span className="inline-flex items-center px-space-xs py-0.5 rounded-full bg-surface-container-high border border-border-subtle text-text-tertiary font-label-code text-label-code tracking-wide">
              v2.4 Core
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-space-lg" data-active-classes="text-text-primary">
            <a
              className="text-on-surface-variant hover:text-text-primary font-body-sm text-body-sm transition-colors duration-150"
              data-path="architecture"
              href="#architecture"
              onClick={(e) => handleScrollTo(e, 'architecture')}
            >
              Architecture
            </a>
            <a
              className="text-on-surface-variant hover:text-text-primary font-body-sm text-body-sm transition-colors duration-150"
              data-path="how-it-works"
              href="#how-it-works"
              onClick={(e) => handleScrollTo(e, 'how-it-works')}
            >
              How it Works
            </a>
            <a
              className="text-on-surface-variant hover:text-text-primary font-body-sm text-body-sm transition-colors duration-150"
              data-path="safety-layer"
              href="#safety-layer"
              onClick={(e) => handleScrollTo(e, 'safety-layer')}
            >
              Safety Layer
            </a>
            <a
              className="text-on-surface-variant hover:text-text-primary font-body-sm text-body-sm transition-colors duration-150"
              data-path="benchmarks"
              href="#benchmarks"
              onClick={(e) => handleScrollTo(e, 'benchmarks')}
            >
              Benchmarks
            </a>
            <a
              className="text-on-surface-variant hover:text-text-primary font-body-sm text-body-sm transition-colors duration-150"
              data-path="docs"
              href="#docs"
              onClick={(e) => {
                e.preventDefault();
                setIsWhitepaperOpen(true);
              }}
            >
              Docs
            </a>
          </nav>

          <div className="flex items-center gap-space-md shrink-0">
            <a
              className="hidden sm:inline-flex text-on-surface-variant hover:text-text-primary font-body-sm text-body-sm transition-colors duration-150 cursor-pointer"
              data-path="login"
              href="#login"
              onClick={(e) => {
                e.preventDefault();
                onNavigateToConsole();
              }}
            >
              Sign in
            </a>
            <a
              className="inline-flex items-center justify-center px-space-md py-1.5 rounded-lg bg-primary-container text-surface-canvas font-body-sm text-body-sm font-medium shadow-[0_0_16px_rgba(0,229,255,0.35)] hover:shadow-[0_0_20px_rgba(0,229,255,0.55)] transition-all duration-200 cursor-pointer"
              data-path="launch-demo"
              href="#console"
              onClick={(e) => {
                e.preventDefault();
                onNavigateToConsole();
              }}
            >
              Launch Demo
            </a>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full pt-16 bg-surface-canvas">
        <div className="flex flex-col w-full relative overflow-hidden bg-surface-canvas selection:bg-primary-container selection:text-surface-canvas">
          {/* Subtle ambient thermal gradients and structural background grid */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10">
            <div className="absolute -top-[280px] left-1/2 -translate-x-1/2 w-[1100px] h-[640px] rounded-full bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.075)_0%,rgba(14,20,26,0)_70%)] blur-3xl"></div>
            <div className="absolute top-[1400px] -right-[200px] w-[700px] h-[700px] rounded-full bg-[radial-gradient(circle_at_center,rgba(0,104,117,0.06)_0%,rgba(8,9,10,0)_70%)] blur-3xl"></div>
            <div className="absolute top-[2800px] left-[-150px] w-[800px] h-[800px] rounded-full bg-[radial-gradient(circle_at_center,rgba(228,242,34,0.025)_0%,rgba(8,9,10,0)_70%)] blur-3xl"></div>
            {/* Fine sub-pixel dot-matrix overlay */}
            <div className="absolute inset-0 opacity-[0.14] bg-[radial-gradient(#bac9cc_1px,transparent_1px)] [background-size:24px_24px]"></div>
          </div>

          {/* ========================================================================= */}
          {/* 1. HERO SECTION                                                          */}
          {/* ========================================================================= */}
          <section className="relative w-full max-w-7xl mx-auto px-gutter pt-12 pb-24 md:pt-20 md:pb-32 flex flex-col items-center text-center">
            {/* Announcement Pill */}
            <div
              onClick={() => onNavigateToConsole()}
              className="inline-flex items-center gap-space-sm px-3.5 py-1.5 rounded-full bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:shadow-[0_0_16px_rgba(0,229,255,0.25)] transition-all duration-300 cursor-pointer group mb-8"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-container"></span>
              </span>
              <span className="font-label-code text-label-code text-text-secondary tracking-wide flex items-center gap-1.5">
                <span className="text-text-primary font-semibold">Introducing Thermion Engine</span>
                <span className="text-text-tertiary">·</span>
                <span className="text-primary-fixed-dim">Autonomous Thermal Optimization</span>
              </span>
              <span className="material-symbols-outlined text-text-tertiary text-sm group-hover:translate-x-0.5 group-hover:text-primary-container transition-all">
                chevron_right
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="font-display text-display max-w-4xl tracking-tight text-transparent bg-clip-text bg-gradient-to-b from-white via-text-primary to-text-secondary mb-6 selection:text-surface-canvas">
              Cooling decisions your data center can trust.
            </h1>

            {/* Subheadline */}
            <p className="font-body-lg text-body-lg text-text-tertiary max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
              Thermion predicts facility thermal drift, recommends the safest and most efficient cooling
              strategy, and explains every closed-loop actuation in plain language.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
              <a
                className="relative group px-6 py-3 rounded-lg bg-text-primary text-surface-canvas font-body-sm text-body-sm font-semibold flex items-center gap-2.5 shadow-[0_0_24px_rgba(255,255,255,0.2)] hover:shadow-[0_0_32px_rgba(0,229,255,0.45)] hover:bg-primary-container transition-all duration-200 cursor-pointer"
                data-path="demo"
                href="#demo"
                onClick={(e) => {
                  e.preventDefault();
                  onNavigateToConsole();
                }}
              >
                <span>See it in action</span>
                <span className="material-symbols-outlined text-base transition-transform group-hover:translate-x-0.5">
                  arrow_forward
                </span>
              </a>
              <a
                className="px-5 py-3 rounded-lg bg-surface-base text-text-secondary hover:text-text-primary font-body-sm text-body-sm font-medium flex items-center gap-3 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-150 cursor-pointer"
                data-path="whitepaper"
                href="#whitepaper"
                onClick={(e) => {
                  e.preventDefault();
                  setIsWhitepaperOpen(true);
                }}
              >
                <span>Read Whitepaper</span>
                <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high font-label-code text-label-code text-text-tertiary tracking-tight">
                  ⌘K
                </kbd>
              </a>
            </div>

            {/* Telemetry Console Card Preview */}
            <div className="w-full max-w-5xl rounded-xl bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12),0_24px_64px_rgba(0,0,0,0.8)] p-px overflow-hidden text-left relative">
              <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-96 h-32 bg-primary-container/10 blur-3xl pointer-events-none"></div>

              {/* Console Window Chrome */}
              <div className="bg-surface-elevated px-4 py-3 flex items-center justify-between border-b border-white/[0.05]">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-surface-bright"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-surface-bright"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-surface-bright"></div>
                  <span className="font-label-code text-label-code text-text-tertiary ml-2">
                    node-cluster-iad04 / rack-row-b / closed-loop-telemetry
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-thermal-lime/10 text-status-thermal-lime font-label-code text-label-code">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-thermal-lime animate-pulse"></span>
                    ACTIVE CONTROL
                  </span>
                  <span className="font-label-code text-label-code text-text-tertiary">T+4.2ms</span>
                </div>
              </div>

              {/* Telemetry Dashboard Body */}
              <div className="p-6 md:p-8 bg-surface-base space-y-6">
                {/* Top Metrics Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-surface-canvas p-4 rounded-lg shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]">
                    <div className="font-label-code text-label-code text-text-tertiary uppercase tracking-wider mb-1 flex items-center justify-between">
                      <span>Facility PUE</span>
                      <span className="text-status-thermal-lime material-symbols-outlined text-xs">
                        trending_down
                      </span>
                    </div>
                    <div className="font-headline-lg text-headline-lg text-text-primary tracking-tight font-semibold">
                      {livePue.toFixed(2)}
                      <span className="text-primary-container text-body-sm font-normal ml-1.5">-0.14</span>
                    </div>
                    <div className="font-label-code text-[11px] text-text-tertiary mt-1">
                      Target benchmark: &lt;1.12
                    </div>
                  </div>

                  <div className="bg-surface-canvas p-4 rounded-lg shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]">
                    <div className="font-label-code text-label-code text-text-tertiary uppercase tracking-wider mb-1 flex items-center justify-between">
                      <span>42U Hot Aisle</span>
                      <span className="text-primary-container material-symbols-outlined text-xs">
                        thermostat
                      </span>
                    </div>
                    <div className="font-headline-lg text-headline-lg text-text-primary tracking-tight font-semibold">
                      {liveTemp}°C
                    </div>
                    <div className="font-label-code text-[11px] text-primary-container mt-1">
                      ΔT 13.8°C (Nominal)
                    </div>
                  </div>

                  <div className="bg-surface-canvas p-4 rounded-lg shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]">
                    <div className="font-label-code text-label-code text-text-tertiary uppercase tracking-wider mb-1 flex items-center justify-between">
                      <span>Current Mode</span>
                      <span className="text-primary-container material-symbols-outlined text-xs">
                        tune
                      </span>
                    </div>
                    <div className="font-headline-md text-headline-md text-primary-container tracking-tight font-semibold flex items-center gap-1.5">
                      HYBRID
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary-container/20 text-primary-container font-label-code">
                        APPROVED
                      </span>
                    </div>
                    <div className="font-label-code text-[11px] text-text-tertiary mt-1">
                      Liquid 65% · Air 35%
                    </div>
                  </div>

                  <div className="bg-surface-canvas p-4 rounded-lg shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]">
                    <div className="font-label-code text-label-code text-text-tertiary uppercase tracking-wider mb-1 flex items-center justify-between">
                      <span>Cedar Safety Guard</span>
                      <span className="text-status-thermal-lime material-symbols-outlined text-xs">
                        verified_user
                      </span>
                    </div>
                    <div className="font-headline-lg text-headline-lg text-text-primary tracking-tight font-semibold">
                      0 Violations
                    </div>
                    <div className="font-label-code text-[11px] text-status-thermal-lime mt-1">
                      100% Invariant Compliant
                    </div>
                  </div>
                </div>

                {/* Middle Row: Interactive Heatmap Visual & Plain-Language Explanation */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                  {/* Heatmap Rack Preview (5 Cols) */}
                  <div className="lg:col-span-5 bg-surface-canvas rounded-lg p-4 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-label-code text-label-code text-text-secondary uppercase">
                        Zone Heatmap Gradient (42U)
                      </span>
                      <span className="font-label-code text-[11px] text-text-tertiary">
                        {hoveredRack ? hoveredRack : 'Real-time Thermistors'}
                      </span>
                    </div>

                    {/* Heatmap Matrix Representation */}
                    <div className="grid grid-cols-7 gap-1.5 my-2">
                      {thermistorRacks.map((rack, idx) => (
                        <div
                          key={idx}
                          onMouseEnter={() => setHoveredRack(`${rack.id}: ${rack.temp}`)}
                          onMouseLeave={() => setHoveredRack(null)}
                          className={`h-6 rounded ${rack.color} transition-colors cursor-pointer`}
                          title={`${rack.id}: ${rack.temp}`}
                        />
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-label-code text-text-tertiary pt-2 border-t border-white/[0.04]">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded bg-primary-container"></span> Optimal (22-29°C)
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded bg-status-thermal-lime"></span> Heat Dissipation (36-40°C)
                      </span>
                    </div>
                  </div>

                  {/* Plain-Language Explanation Stream (7 Cols) */}
                  <div className="lg:col-span-7 bg-surface-canvas rounded-lg p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-label-code text-label-code text-text-secondary uppercase flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-sm text-primary-container">
                            chat_bubble
                          </span>
                          Deterministic Rationale Synthesis
                        </span>
                        <span className="font-label-code text-[11px] text-primary-container bg-primary-container/10 px-2 py-0.5 rounded">
                          LLM Transparent Log
                        </span>
                      </div>
                      <div className="space-y-2.5 font-label-code text-body-sm">
                        <div className="p-3 rounded bg-surface-base text-text-secondary leading-relaxed border-l-2 border-primary-container">
                          <span className="text-text-primary font-medium">Actuation Dispatch #9281:</span>
                          &nbsp;"Shifted 14 CRAC units to high-rate liquid manifold loop preempting peak ambient thermal surge (+3.4°C forecasted over next 12 min). Chiller pump #4 modulated to 68% PWM to maintain sub-cooling equilibrium while shaving 142 kW facility load."
                        </div>
                        <div className="flex items-center gap-4 text-[11px] text-text-tertiary pt-1">
                          <span>
                            Confidence: <strong className="text-text-primary">99.4%</strong>
                          </span>
                          <span>
                            Predicted Sav: <strong className="text-status-thermal-lime">18.6 kWh/hr</strong>
                          </span>
                          <span>
                            Latency: <strong className="text-text-primary">28ms</strong>
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between pt-3 mt-3 border-t border-white/[0.04] font-label-code text-[11px] text-text-tertiary">
                      <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-status-thermal-lime"></span> Immutable SHA-256 Ledger Verified
                      </span>
                      <a
                        className="text-primary-container hover:underline cursor-pointer"
                        href="#console"
                        onClick={(e) => {
                          e.preventDefault();
                          onNavigateToConsole();
                        }}
                      >
                        View raw telemetry vectors →
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 2. THE CHALLENGE / PROBLEM SECTION                                       */}
          {/* ========================================================================= */}
          <section id="benchmarks" className="relative w-full max-w-7xl mx-auto px-gutter py-24 border-t border-white/[0.06]">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 font-label-code text-label-code text-primary-container tracking-wider uppercase mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-container"></span>
                  The Challenge
                </div>
                <h2 className="font-headline-lg text-headline-lg text-text-primary tracking-tight font-semibold">
                  Static rules fail dynamic workloads.
                </h2>
              </div>
              <p className="font-body-md text-body-md text-text-tertiary max-w-md">
                Traditional cooling runs on rigid setpoints that don't adapt to bursting AI inference,
                shifting outdoor weather, or water conservation constraints.
              </p>
            </div>

            {/* 3 Sleek Comparative Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Card 1 */}
              <div className="p-8 rounded-xl bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:shadow-[0_0_24px_rgba(0,229,255,0.1)] transition-all duration-300 flex flex-col justify-between group">
                <div>
                  <div className="w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center mb-6 group-hover:scale-105 transition-transform">
                    <span className="material-symbols-outlined text-primary-container text-xl">bolt</span>
                  </div>
                  <div className="font-display text-[2.75rem] font-semibold text-text-primary tracking-tight mb-2">
                    34<span className="text-primary-container">%</span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Over-cooling waste
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Conservative baseline setpoints dump massive energy during transient load lulls to
                    protect against theoretical hotspots.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] font-label-code text-label-code text-text-tertiary flex items-center justify-between">
                  <span>Inefficiency Vector</span>
                  <span className="text-text-secondary">Parasitic Compressor Load</span>
                </div>
              </div>

              {/* Card 2 */}
              <div className="p-8 rounded-xl bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:shadow-[0_0_24px_rgba(0,229,255,0.1)] transition-all duration-300 flex flex-col justify-between group">
                <div>
                  <div className="w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center mb-6 group-hover:scale-105 transition-transform">
                    <span className="material-symbols-outlined text-secondary text-xl">water_drop</span>
                  </div>
                  <div className="font-display text-[2.75rem] font-semibold text-text-primary tracking-tight mb-2">
                    Millions<span className="text-secondary text-xl font-normal ml-1">gal</span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Water consumption stress
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Evaporative towers run blind without localized wet-bulb optimization, consuming
                    critical municipal resources needlessly.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] font-label-code text-label-code text-text-tertiary flex items-center justify-between">
                  <span>Resource Pressure</span>
                  <span className="text-text-secondary">Evaporative Drift &amp; Bleed</span>
                </div>
              </div>

              {/* Card 3 */}
              <div className="p-8 rounded-xl bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:shadow-[0_0_24px_rgba(0,229,255,0.1)] transition-all duration-300 flex flex-col justify-between group">
                <div>
                  <div className="w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center mb-6 group-hover:scale-105 transition-transform">
                    <span className="material-symbols-outlined text-status-thermal-lime text-xl">
                      hourglass_empty
                    </span>
                  </div>
                  <div className="font-display text-[2.75rem] font-semibold text-text-primary tracking-tight mb-2">
                    15+<span className="text-status-thermal-lime text-xl font-normal ml-1">min</span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Lagging response times
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    BMS feedback loops react only after heat builds, causing thermal throttling on accelerator
                    clusters before fans catch up.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] font-label-code text-label-code text-text-tertiary flex items-center justify-between">
                  <span>Critical Latency</span>
                  <span className="text-text-secondary">Reactive PID Oscillations</span>
                </div>
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 3. HOW IT WORKS / PIPELINE                                               */}
          {/* ========================================================================= */}
          <section id="how-it-works" className="relative w-full max-w-7xl mx-auto px-gutter py-24 border-t border-white/[0.06]">
            <div className="text-center max-w-3xl mx-auto mb-20">
              <div className="inline-flex items-center gap-2 font-label-code text-label-code text-primary-container tracking-wider uppercase mb-3">
                <span className="w-1.5 h-1.5 rounded-full bg-primary-container"></span>
                The Pipeline
              </div>
              <h2 className="font-headline-lg text-headline-lg text-text-primary tracking-tight font-semibold mb-4">
                From telemetry to equipment execution.
              </h2>
              <p className="font-body-md text-body-md text-text-tertiary">
                A strictly deterministic, mathematically audited 5-step control sequence executed
                continuously every 30 seconds.
              </p>
            </div>

            {/* 5-Step Pipeline Grid with Glowing Track */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
              {/* Connecting Track line for desktop */}
              <div className="hidden md:block absolute top-1/2 left-8 right-8 h-0.5 bg-gradient-to-r from-primary-container/20 via-primary-container/60 to-status-thermal-lime/40 -translate-y-12 z-0 pointer-events-none"></div>

              {/* Step 1 */}
              <div className="relative z-10 bg-surface-base p-6 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col justify-between h-full group hover:shadow-[0_0_20px_rgba(0,229,255,0.15)] transition-all">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="w-8 h-8 rounded-full bg-surface-elevated text-primary-container font-label-code text-label-code font-bold flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(255,255,255,0.15)]">
                      01
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-lg">
                      sensors
                    </span>
                  </div>
                  <h4 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-2">
                    Sensor data
                  </h4>
                  <p className="font-body-sm text-body-sm text-text-tertiary">
                    Multi-zone thermistors, rack delta-T, outdoor wet-bulb temp, and power draw telemetry
                    ingested via high-rate gRPC.
                  </p>
                </div>
                <div className="mt-6 font-label-code text-[11px] text-text-tertiary">
                  • 10,000+ points/sec
                </div>
              </div>

              {/* Step 2 */}
              <div className="relative z-10 bg-surface-base p-6 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col justify-between h-full group hover:shadow-[0_0_20px_rgba(0,229,255,0.15)] transition-all">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="w-8 h-8 rounded-full bg-surface-elevated text-primary-container font-label-code text-label-code font-bold flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(255,255,255,0.15)]">
                      02
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-lg">
                      analytics
                    </span>
                  </div>
                  <h4 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-2">
                    AI predicts
                  </h4>
                  <p className="font-body-sm text-body-sm text-text-tertiary">
                    High-speed predictive forward modeling of thermal drift over the next 15-minute
                    horizon using XGBoost surrogates.
                  </p>
                </div>
                <div className="mt-6 font-label-code text-[11px] text-text-tertiary">
                  • 15-min forward horizon
                </div>
              </div>

              {/* Step 3 */}
              <div className="relative z-10 bg-surface-base p-6 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col justify-between h-full group hover:shadow-[0_0_20px_rgba(0,229,255,0.15)] transition-all">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="w-8 h-8 rounded-full bg-surface-elevated text-primary-container font-label-code text-label-code font-bold flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(255,255,255,0.15)]">
                      03
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-lg">
                      psychology
                    </span>
                  </div>
                  <h4 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-2">
                    RL recommends
                  </h4>
                  <p className="font-body-sm text-body-sm text-text-tertiary">
                    PPO policy evaluates state space and selects optimal mode: AIR, LIQUID, or HYBRID with
                    targeted pump RPM &amp; flow rate.
                  </p>
                </div>
                <div className="mt-6 font-label-code text-[11px] text-text-tertiary">
                  • Multi-objective reward
                </div>
              </div>

              {/* Step 4 */}
              <div className="relative z-10 bg-surface-base p-6 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col justify-between h-full group hover:shadow-[0_0_20px_rgba(228,242,34,0.2)] transition-all border-l md:border-l-0 border-status-thermal-lime/30">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="w-8 h-8 rounded-full bg-status-thermal-lime/20 text-status-thermal-lime font-label-code text-label-code font-bold flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(228,242,34,0.3)]">
                      04
                    </span>
                    <span className="material-symbols-outlined text-status-thermal-lime text-lg">
                      gavel
                    </span>
                  </div>
                  <h4 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-2">
                    Safety verifies
                  </h4>
                  <p className="font-body-sm text-body-sm text-text-tertiary">
                    Cedar mathematical boundary checks validate thermodynamic thresholds before dispatch.
                    Unsafe commands blocked.
                  </p>
                </div>
                <div className="mt-6 font-label-code text-[11px] text-status-thermal-lime">
                  • Zero-tolerance filter
                </div>
              </div>

              {/* Step 5 */}
              <div className="relative z-10 bg-surface-base p-6 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] flex flex-col justify-between h-full group hover:shadow-[0_0_20px_rgba(0,229,255,0.15)] transition-all">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="w-8 h-8 rounded-full bg-surface-elevated text-primary-container font-label-code text-label-code font-bold flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(255,255,255,0.15)]">
                      05
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-lg">
                      description
                    </span>
                  </div>
                  <h4 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-2">
                    Logged &amp; told
                  </h4>
                  <p className="font-body-sm text-body-sm text-text-tertiary">
                    Append-only OpenSearch ledger indexed with human-readable rationale synthesized
                    automatically for operations staff.
                  </p>
                </div>
                <div className="mt-6 font-label-code text-[11px] text-text-tertiary">
                  • Full explainability
                </div>
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 4. CORE ARCHITECTURE GRID                                                */}
          {/* ========================================================================= */}
          <section id="architecture" className="relative w-full max-w-7xl mx-auto px-gutter py-24 border-t border-white/[0.06]">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
              <div>
                <div className="inline-flex items-center gap-2 font-label-code text-label-code text-primary-container tracking-wider uppercase mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-container"></span>
                  Core Architecture
                </div>
                <h2 className="font-headline-lg text-headline-lg text-text-primary tracking-tight font-semibold">
                  Engineered for zero-tolerance reliability.
                </h2>
              </div>
              <p className="font-body-md text-body-md text-text-tertiary max-w-sm">
                Independent modular systems working in tight consensus to enforce data integrity and
                thermal safety.
              </p>
            </div>

            {/* 3x2 Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Card 1 */}
              <div className="bg-surface-base p-8 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-200 flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-label-code text-label-code text-primary-container bg-primary-container/10 px-2.5 py-1 rounded">
                      SURROGATE TWIN
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-xl transition-colors">
                      model_training
                    </span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Digital Twin (XGBoost)
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Ultra-fast regression surrogate model simulating heat transfer dynamics and
                    equilibrium outcomes across 42U rack envelopes without expensive physical sensor delay.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-label-code text-text-tertiary">
                  <span>Inference Latency</span>
                  <span className="text-text-secondary">1.2ms / state</span>
                </div>
              </div>

              {/* Card 2 */}
              <div className="bg-surface-base p-8 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-200 flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-label-code text-label-code text-primary-container bg-primary-container/10 px-2.5 py-1 rounded">
                      DECISION ENGINE
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-xl transition-colors">
                      neurology
                    </span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    PPO Reinforcement-Learning
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Proximal Policy Optimization balancing energy reduction against thermal headroom.
                    Employs continuous action-space control over fan PWM and chiller coolant valves.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-label-code text-text-tertiary">
                  <span>Policy Convergence</span>
                  <span className="text-text-secondary">&gt;99.98% stability</span>
                </div>
              </div>

              {/* Card 3 */}
              <div className="bg-surface-base p-8 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-200 flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-label-code text-label-code text-status-thermal-lime bg-status-thermal-lime/10 px-2.5 py-1 rounded">
                      FORMAL AUDIT
                    </span>
                    <span className="material-symbols-outlined text-status-thermal-lime text-xl">
                      security
                    </span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Cedar Safety Layer
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Non-probabilistic policy guardrails written in Cedar. Deterministically verifies that
                    all suggested actions remain within physical hardware limits and ASHRAE guidelines.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-label-code text-status-thermal-lime">
                  <span>Hard Rejection Speed</span>
                  <span>&lt;0.4ms</span>
                </div>
              </div>

              {/* Card 4 */}
              <div className="bg-surface-base p-8 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-200 flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-label-code text-label-code text-primary-container bg-primary-container/10 px-2.5 py-1 rounded">
                      DATASTORE
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-xl transition-colors">
                      database
                    </span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    OpenSearch Telemetry
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    High-throughput immutable logging cluster capturing every raw thermistor frame,
                    policy tensor output, environmental condition, and safety evaluation record.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-label-code text-text-tertiary">
                  <span>Audit Durability</span>
                  <span className="text-text-secondary">Cryptographic Hash Chain</span>
                </div>
              </div>

              {/* Card 5 */}
              <div className="bg-surface-base p-8 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-200 flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-label-code text-label-code text-primary-container bg-primary-container/10 px-2.5 py-1 rounded">
                      TRANSPARENCY
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-xl transition-colors">
                      quick_phrases
                    </span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Plain-Language Explanations
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Specialized LLM translation layer converting multi-dimensional numerical state changes
                    into clear, conversational rationales for operations engineering reviews.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-label-code text-text-tertiary">
                  <span>Readability Index</span>
                  <span className="text-text-secondary">Standard Ops English</span>
                </div>
              </div>

              {/* Card 6 */}
              <div className="bg-surface-base p-8 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-200 flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-label-code text-label-code text-primary-container bg-primary-container/10 px-2.5 py-1 rounded">
                      MISSION CONTROL
                    </span>
                    <span className="material-symbols-outlined text-text-tertiary group-hover:text-primary-container text-xl transition-colors">
                      dashboard
                    </span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-text-primary font-medium mb-3">
                    Live Operator Interface
                  </h3>
                  <p className="font-body-sm text-body-sm text-text-tertiary leading-relaxed">
                    Real-time operations terminal providing sub-second facility telemetry, dynamic
                    thermal topology maps, manual overrides, and instant safety envelope calibration.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-label-code text-text-tertiary">
                  <span>Client Refresh Rate</span>
                  <span className="text-text-secondary">60 Hz Canvas Stream</span>
                </div>
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 5. TRUST & VERIFICATION CALLOUT CARD                                     */}
          {/* ========================================================================= */}
          <section id="safety-layer" className="relative w-full max-w-7xl mx-auto px-gutter py-24 border-t border-white/[0.06]">
            <div className="relative rounded-2xl bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12),0_0_40px_rgba(0,229,255,0.08)] p-8 md:p-14 overflow-hidden border border-white/[0.08]">
              {/* Cyan ambient focal wash behind card */}
              <div className="absolute -right-32 -bottom-32 w-96 h-96 rounded-full bg-primary-container/10 blur-3xl pointer-events-none"></div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center relative z-10">
                <div className="lg:col-span-7">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-status-thermal-lime/10 text-status-thermal-lime font-label-code text-label-code mb-6">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-thermal-lime"></span>
                    HARD-CONSTRAINED ACTUATION
                  </div>
                  <h2 className="font-headline-lg text-headline-lg text-text-primary font-semibold tracking-tight mb-4">
                    AI recommends. Safety decides.
                  </h2>
                  <p className="font-body-lg text-body-lg text-text-secondary leading-relaxed mb-6 font-normal">
                    The machine learning model is strictly sandboxed. Every single proposal is passed to
                    a non-probabilistic rule engine. Unsafe proposals are dropped in microseconds before
                    reaching physical chillers, valves, or variable frequency drives.
                  </p>
                  <div className="flex items-center gap-6 font-label-code text-body-sm text-text-tertiary">
                    <span className="flex items-center gap-1.5 text-text-primary">
                      <span className="material-symbols-outlined text-primary-container text-base">
                        check_circle
                      </span>{' '}
                      Zero Autonomous Drift
                    </span>
                    <span className="flex items-center gap-1.5 text-text-primary">
                      <span className="material-symbols-outlined text-primary-container text-base">
                        check_circle
                      </span>{' '}
                      Hardware Interlocks
                    </span>
                  </div>
                </div>

                {/* Verification Badge Matrix */}
                <div className="lg:col-span-5 grid grid-cols-2 gap-4">
                  <div className="p-5 rounded-lg bg-surface-canvas shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] flex flex-col justify-between">
                    <span className="material-symbols-outlined text-primary-container text-2xl mb-2">
                      policy
                    </span>
                    <div>
                      <div className="font-headline-sm text-sm text-text-primary font-medium">
                        Deterministic Cedar Policies
                      </div>
                      <div className="font-label-code text-[11px] text-text-tertiary mt-1">
                        Formal verification rules
                      </div>
                    </div>
                  </div>

                  <div className="p-5 rounded-lg bg-surface-canvas shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] flex flex-col justify-between">
                    <span className="material-symbols-outlined text-status-thermal-lime text-2xl mb-2">
                      speed
                    </span>
                    <div>
                      <div className="font-headline-sm text-sm text-text-primary font-medium">
                        Physical Envelope Invariants
                      </div>
                      <div className="font-label-code text-[11px] text-text-tertiary mt-1">
                        Pressure &amp; ΔT guardrails
                      </div>
                    </div>
                  </div>

                  <div className="p-5 rounded-lg bg-surface-canvas shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] flex flex-col justify-between">
                    <span className="material-symbols-outlined text-secondary text-2xl mb-2">
                      shield_lock
                    </span>
                    <div>
                      <div className="font-headline-sm text-sm text-text-primary font-medium">
                        Fail-Safe Default Fallback
                      </div>
                      <div className="font-label-code text-[11px] text-text-tertiary mt-1">
                        Bypass to BMS defaults
                      </div>
                    </div>
                  </div>

                  <div className="p-5 rounded-lg bg-surface-canvas shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] flex flex-col justify-between">
                    <span className="material-symbols-outlined text-primary text-2xl mb-2">
                      history_edu
                    </span>
                    <div>
                      <div className="font-headline-sm text-sm text-text-primary font-medium">
                        100% Auditable Log
                      </div>
                      <div className="font-label-code text-[11px] text-text-tertiary mt-1">
                        Immutable decision trace
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 6. CLOSING CTA BANNER                                                    */}
          {/* ========================================================================= */}
          <section className="relative w-full max-w-7xl mx-auto px-gutter py-28 text-center border-t border-white/[0.06]">
            <div className="max-w-3xl mx-auto flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-surface-base shadow-[inset_0_1px_0_0_rgba(255,255,255,0.15)] flex items-center justify-center mb-6">
                <span className="material-symbols-outlined text-primary-container text-2xl">
                  device_thermostat
                </span>
              </div>
              <h2 className="font-display text-display max-w-2xl tracking-tight text-text-primary mb-6">
                Ready to optimize your facility's thermal efficiency?
              </h2>
              <p className="font-body-lg text-body-lg text-text-tertiary max-w-xl mx-auto mb-10 leading-relaxed">
                Join hyper-scale operators cutting up to 34% in cooling parasitic power while
                strengthening thermal SLA guarantees.
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <a
                  className="px-7 py-3.5 rounded-lg bg-text-primary text-surface-canvas font-body-sm text-body-sm font-semibold flex items-center gap-2 shadow-[0_0_24px_rgba(255,255,255,0.2)] hover:shadow-[0_0_32px_rgba(0,229,255,0.5)] hover:bg-primary-container transition-all duration-200 cursor-pointer"
                  data-path="demo"
                  href="#demo"
                  onClick={(e) => {
                    e.preventDefault();
                    onNavigateToConsole();
                  }}
                >
                  <span>See it in action</span>
                  <span className="material-symbols-outlined text-base">arrow_forward</span>
                </a>
                <a
                  className="px-6 py-3.5 rounded-lg bg-surface-base text-text-secondary hover:text-text-primary font-body-sm text-body-sm font-medium shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] hover:bg-surface-elevated transition-colors duration-150 cursor-pointer"
                  data-path="contact"
                  href="#contact"
                  onClick={(e) => {
                    e.preventDefault();
                    setIsWhitepaperOpen(true);
                  }}
                >
                  Schedule an Architecture Walkthrough
                </a>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full bg-surface-base border-t border-border-subtle">
        <div className="max-w-7xl mx-auto px-gutter py-space-xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-space-lg pb-space-lg border-b border-border-subtle">
            <div className="flex items-center gap-space-md">
              <div className="inline-flex items-center gap-2 px-space-sm py-1 rounded-full bg-surface-canvas border border-border-subtle font-label-code text-label-code text-text-secondary">
                <span className="w-2 h-2 rounded-full bg-status-thermal-lime animate-pulse"></span>
                <span>Operational · 99.99%</span>
              </div>
              <span className="inline-flex items-center px-space-xs py-0.5 rounded-full bg-surface-container border border-border-subtle text-text-tertiary font-label-code text-label-code">
                Hackathon Edition
              </span>
            </div>
            <div className="flex items-center gap-space-lg font-body-sm text-body-sm text-text-secondary">
              <a
                className="hover:text-text-primary transition-colors duration-150 cursor-pointer"
                data-path="github"
                href="#github"
                onClick={(e) => {
                  e.preventDefault();
                  alert('Thermion Core GitHub repository reference is private enterprise code.');
                }}
              >
                GitHub Repository
              </a>
              <a
                className="hover:text-text-primary transition-colors duration-150 cursor-pointer"
                data-path="docs"
                href="#docs"
                onClick={(e) => {
                  e.preventDefault();
                  setIsWhitepaperOpen(true);
                }}
              >
                Documentation
              </a>
              <a
                className="hover:text-text-primary transition-colors duration-150 cursor-pointer"
                data-path="team"
                href="#team"
                onClick={(e) => {
                  e.preventDefault();
                  alert('Thermion Distributed Systems Group: yashpan720@gmail.com');
                }}
              >
                Engineering Team
              </a>
            </div>
          </div>
          <div className="pt-space-md flex flex-col sm:flex-row items-center justify-between gap-space-sm text-text-tertiary font-body-sm text-body-sm">
            <div>Engineered by Thermion Distributed Systems Group</div>
            <div>© 2025 Thermion Technologies Inc. All rights reserved.</div>
          </div>
        </div>
      </footer>

      {/* Whitepaper technical modal */}
      <WhitepaperModal
        isOpen={isWhitepaperOpen}
        onClose={() => setIsWhitepaperOpen(false)}
        onLaunchConsole={onNavigateToConsole}
      />
    </div>
  );
};
