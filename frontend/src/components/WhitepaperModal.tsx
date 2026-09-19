import React from 'react';

interface WhitepaperModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLaunchConsole: () => void;
}

export const WhitepaperModal: React.FC<WhitepaperModalProps> = ({
  isOpen,
  onClose,
  onLaunchConsole,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-canvas/80 backdrop-blur-md">
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-surface-base rounded-2xl border border-border-highlight shadow-[0_24px_64px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.12)] p-6 md:p-8"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse"></span>
            <span className="font-label-code text-label-code text-text-tertiary">
              THERMION TECHNICAL SPEC · REV 2.4
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-text-tertiary hover:text-text-primary p-1 rounded-md hover:bg-surface-elevated transition-colors"
            aria-label="Close"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        <div className="mt-6 space-y-6 text-left">
          <div>
            <h3 className="font-headline-md text-headline-md text-text-primary font-semibold">
              Autonomous Closed-Loop Thermal Optimization with Formal Safety Guardrails
            </h3>
            <p className="font-body-md text-body-md text-text-tertiary mt-2">
              Published by the Thermion Distributed Systems &amp; Thermal Engineering Group (2025).
            </p>
          </div>

          <div className="space-y-4 font-body-sm text-body-sm text-text-secondary leading-relaxed">
            <div className="p-4 rounded-xl bg-surface-canvas border border-white/[0.06]">
              <h4 className="font-headline-sm text-sm font-semibold text-primary-container uppercase tracking-wider mb-2">
                Executive Abstract
              </h4>
              <p>
                Modern hyper-scale facilities hosting LLM training clusters experience dynamic thermal bursts that conventional PID-based Building Management Systems cannot react to without severe over-cooling margins. Thermion combines high-frequency surrogate thermal drift modeling with a mathematically verifiable Cedar policy engine to reduce parasitic cooling power by up to 34% while guaranteeing zero thermal SLA breaches.
              </p>
            </div>

            <div>
              <h4 className="font-headline-sm text-sm font-semibold text-text-primary mb-1">
                1. Continuous Surrogate Digital Twin
              </h4>
              <p className="text-text-tertiary">
                Using gradient-boosted XGBoost regressions trained on 10,000+ per-second rack thermistors, Thermion forecasts thermal equilibrium envelopes 15 minutes ahead in 1.2ms inference windows.
              </p>
            </div>

            <div>
              <h4 className="font-headline-sm text-sm font-semibold text-text-primary mb-1">
                2. PPO Multimodal Optimization
              </h4>
              <p className="text-text-tertiary">
                The continuous action policy dynamically balances liquid-to-air cooling ratios, pump PWM velocities, and external wet-bulb economizers based on multi-objective rewards: thermal stability (+0.85), energy conservation, and water consumption minimization.
              </p>
            </div>

            <div>
              <h4 className="font-headline-sm text-sm font-semibold text-status-thermal-lime mb-1">
                3. Non-Probabilistic Cedar Safety Layer
              </h4>
              <p className="text-text-tertiary">
                Crucially, machine learning models never directly actuate hardware. Every proposed state transition is formally verified against Cedar policy invariants (e.g. pressure gradients, maximum ramp-rates, and ASHRAE envelopes). Any violation drops the proposal in &lt;0.4ms and reverts to deterministic hardware interlocks.
              </p>
            </div>
          </div>

          <div className="pt-6 border-t border-white/[0.08] flex items-center justify-between">
            <span className="font-label-code text-[11px] text-text-tertiary">
              SHA-256: 8f4e2...a90b
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-surface-canvas text-text-secondary hover:text-text-primary font-body-sm text-body-sm transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  onClose();
                  onLaunchConsole();
                }}
                className="px-4 py-2 rounded-lg bg-primary-container text-surface-canvas font-body-sm text-body-sm font-semibold hover:shadow-[0_0_16px_rgba(0,229,255,0.4)] transition-all"
              >
                Launch Console
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
