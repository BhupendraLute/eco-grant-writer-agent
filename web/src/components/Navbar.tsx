"use client";

import { Phase, PHASES } from "@/lib/types";

interface NavbarProps {
  phase: Phase;
  onReset: () => void;
}

export default function Navbar({ phase, onReset }: NavbarProps) {
  return (
    <nav className="glass-navbar fixed top-0 left-0 right-0 z-50 px-6 py-3">
      <div className="max-w-[1600px] mx-auto flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded-lg bg-[var(--color-accent)] flex items-center justify-center group-hover:shadow-[var(--shadow-glow-green)] transition-shadow duration-200">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0f172a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 8c.7-1 1-2.2 1-3.5C18 2.5 16.6 1 14.5 1S11 2.5 11 4.5c0 1.3.3 2.5 1 3.5" />
              <path d="M6 13c-1 .7-2.2 1-3.5 1C.5 14-1 12.6-1 10.5S.5 7 2.5 7c1.3 0 2.5.3 3.5 1" />
              <path d="M12 22c-1-.7-2.2-1-3.5-1C6.5 21 5 22.4 5 24.5S6.4 28 8.5 28c1.3 0 2.5-.3 3.5-1" />
              <path d="M11 15a7 7 0 0 0 7-7" />
              <path d="M4 11a7 7 0 0 0 7 7" />
            </svg>
          </div>
          <span className="text-[var(--color-text-primary)] font-semibold text-lg tracking-tight">
            Eco <span className="text-[var(--color-accent)]">Grant Writer</span>
          </span>
        </button>

        {/* Phase Tracker */}
        <PhaseTracker currentPhase={phase} />

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onReset}
            className="btn-ghost text-sm py-2 px-4"
            title="Start new conversation"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline mr-1.5">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
            New
          </button>
        </div>
      </div>
    </nav>
  );
}

function PhaseTracker({ currentPhase }: { currentPhase: Phase }) {
  const phaseIndex = PHASES.findIndex((p) => p.key === currentPhase);

  return (
    <div className="hidden md:flex items-center gap-1">
      {PHASES.map((p, i) => {
        const isCompleted = phaseIndex > i;
        const isActive = p.key === currentPhase;
        const showConnector = i < PHASES.length - 1;

        return (
          <div key={p.key} className="flex items-center gap-1">
            <div className="flex flex-col items-center gap-1">
              <div
                className={`phase-dot ${isCompleted ? "completed" : ""} ${isActive ? "active" : ""}`}
                title={p.label}
              />
              <span
                className={`text-[10px] font-medium whitespace-nowrap ${
                  isActive
                    ? "text-[var(--color-accent)]"
                    : isCompleted
                      ? "text-[var(--color-text-secondary)]"
                      : "text-[var(--color-text-muted)]"
                }`}
              >
                {p.label}
              </span>
            </div>
            {showConnector && (
              <div
                className={`phase-connector w-8 lg:w-12 mb-4 ${isCompleted ? "completed" : ""}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
