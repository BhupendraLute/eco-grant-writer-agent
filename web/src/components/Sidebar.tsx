"use client";

import type { AgentState } from "@/lib/types";
import { formatCurrency } from "@/utils/markdown";

interface SidebarProps {
  state: AgentState;
}

export default function Sidebar({ state }: SidebarProps) {
  const hasData =
    state.organization_name ||
    state.location ||
    state.budget_amount > 0 ||
    state.volunteers_count > 0;

  return (
    <aside className="w-[300px] min-w-[280px] h-full flex flex-col gap-4 p-4 overflow-y-auto border-r border-[var(--color-border)]">
      {/* Project Snapshot */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
          </svg>
          Project Snapshot
        </h3>

        {hasData ? (
          <div className="space-y-3">
            <InfoRow
              icon={<OrgIcon />}
              label="Organization"
              value={state.organization_name}
            />
            <InfoRow
              icon={<LocationIcon />}
              label="Location"
              value={state.location}
            />
            <InfoRow
              icon={<BudgetIcon />}
              label="Budget"
              value={
                state.budget_amount > 0
                  ? formatCurrency(state.budget_amount, state.currency_symbol)
                  : ""
              }
            />
            <InfoRow
              icon={<VolunteersIcon />}
              label="Volunteers"
              value={
                state.volunteers_count > 0
                  ? state.volunteers_count.toString()
                  : ""
              }
            />
            <InfoRow
              icon={<DurationIcon />}
              label="Duration"
              value={state.project_duration}
            />
            <InfoRow
              icon={<IdIcon />}
              label="NGO ID"
              value={state.ngo_registration_id}
            />
          </div>
        ) : (
          <p className="text-sm text-[var(--color-text-muted)] italic">
            Start a conversation to see project details here...
          </p>
        )}
      </div>

      {/* Grant Info */}
      {state.target_grant && (
        <div className="glass-card-accent p-5 animate-fade-in">
          <h3 className="text-sm font-semibold text-[var(--color-accent)] mb-3 flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            Matched Grant
          </h3>
          <p className="text-sm text-[var(--color-text-primary)] font-medium">
            {state.target_grant}
          </p>
          {state.grant_confirmed && (
            <span className="inline-flex items-center gap-1 mt-2 text-xs text-[var(--color-accent)] bg-[var(--color-accent-muted)] px-2 py-1 rounded-full">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
              Confirmed
            </span>
          )}
        </div>
      )}

      {/* Drafting Progress */}
      {state.mandatory_sections.length > 0 && (
        <div className="glass-card p-5 animate-fade-in">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3 flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" />
              <path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z" />
            </svg>
            Drafting Progress
          </h3>
          <div className="space-y-2">
            {state.mandatory_sections.map((section) => {
              const isDrafted = !!state.sections_drafted[section];
              const isCurrent = section === state.current_section;

              return (
                <div
                  key={section}
                  className={`flex items-center gap-2 text-xs py-1.5 px-2 rounded-lg transition-colors ${
                    isCurrent
                      ? "bg-[var(--color-accent-muted)] text-[var(--color-accent)]"
                      : isDrafted
                        ? "text-[var(--color-text-secondary)]"
                        : "text-[var(--color-text-muted)]"
                  }`}
                >
                  {isDrafted ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  ) : isCurrent ? (
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-[var(--color-accent)] animate-pulse-glow" />
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-[var(--color-text-muted)]" />
                  )}
                  <span className="truncate">{section}</span>
                </div>
              );
            })}
          </div>
          {/* Progress bar */}
          <div className="mt-3">
            <div className="h-1.5 bg-[var(--color-bg-primary)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--color-accent)] rounded-full transition-all duration-500"
                style={{
                  width: `${
                    (Object.keys(state.sections_drafted).length /
                      Math.max(state.mandatory_sections.length, 1)) *
                    100
                  }%`,
                }}
              />
            </div>
            <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
              {Object.keys(state.sections_drafted).length} /{" "}
              {state.mandatory_sections.length} sections
            </p>
          </div>
        </div>
      )}

      {/* Status Badges */}
      {(state.is_compliant || state.security_approved) && (
        <div className="glass-card p-5 animate-fade-in">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">
            Compliance & Security
          </h3>
          <div className="space-y-2">
            {state.is_compliant && (
              <StatusBadge label="Compliance Passed" variant="success" />
            )}
            {state.security_approved && (
              <StatusBadge label="Security Approved" variant="success" />
            )}
          </div>
        </div>
      )}
    </aside>
  );
}

// ── Sub-components ─────────────────────────────────────

function InfoRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-8 h-8 rounded-lg bg-[var(--color-bg-surface)] flex items-center justify-center flex-shrink-0 mt-0.5">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
          {label}
        </p>
        <p className="text-sm text-[var(--color-text-primary)] font-medium truncate">
          {value}
        </p>
      </div>
    </div>
  );
}

function StatusBadge({
  label,
  variant,
}: {
  label: string;
  variant: "success" | "warning" | "danger";
}) {
  const colors = {
    success: "text-[var(--color-accent)] bg-[var(--color-accent-muted)]",
    warning: "text-[var(--color-warning)] bg-[var(--color-warning-muted)]",
    danger: "text-[var(--color-danger)] bg-[var(--color-danger-muted)]",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full ${colors[variant]}`}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 6 9 17l-5-5" />
      </svg>
      {label}
    </span>
  );
}

// ── Icons ──────────────────────────────────────────────

function OrgIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" />
      <path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" />
      <path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2" />
      <path d="M10 6h4" />
      <path d="M10 10h4" />
      <path d="M10 14h4" />
      <path d="M10 18h4" />
    </svg>
  );
}
function LocationIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}
function BudgetIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8" />
      <path d="M12 18V6" />
    </svg>
  );
}
function VolunteersIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
function DurationIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
function IdIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <path d="M2 10h20" />
    </svg>
  );
}
