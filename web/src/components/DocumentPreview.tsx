"use client";

import { markdownToHtml } from "@/utils/markdown";

interface DocumentPreviewProps {
  proposal: string;
  isCompliant: boolean;
  securityApproved: boolean;
  targetGrant: string;
}

export default function DocumentPreview({
  proposal,
  isCompliant,
  securityApproved,
  targetGrant,
}: DocumentPreviewProps) {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(proposal);
    } catch {
      // fallback
      const textarea = document.createElement("textarea");
      textarea.value = proposal;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
  };

  if (!proposal) {
    return (
      <aside className="w-[380px] min-w-[340px] h-full flex flex-col border-l border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-[var(--color-bg-surface)] flex items-center justify-center mx-auto mb-4">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
                <path d="M14 2v4a2 2 0 0 0 2 2h4" />
                <path d="M10 9H8" />
                <path d="M16 13H8" />
                <path d="M16 17H8" />
              </svg>
            </div>
            <h3 className="text-sm font-medium text-[var(--color-text-muted)] mb-1">
              Document Preview
            </h3>
            <p className="text-xs text-[var(--color-text-muted)]">
              Your proposal will appear here once drafted
            </p>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-[380px] min-w-[340px] h-full flex flex-col border-l border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
            <path d="M14 2v4a2 2 0 0 0 2 2h4" />
          </svg>
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
            Final Proposal
          </h3>
        </div>
        <button
          onClick={handleCopy}
          className="btn-ghost text-xs py-1.5 px-3"
          title="Copy proposal to clipboard"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline mr-1">
            <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
          </svg>
          Copy
        </button>
      </div>

      {/* Compliance status strip */}
      {(isCompliant || securityApproved) && (
        <div className="px-5 py-3 border-b border-[var(--color-border)] flex items-center gap-4">
          {isCompliant && (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--color-accent)] bg-[var(--color-accent-muted)] px-2.5 py-1 rounded-full">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
              Compliant
            </span>
          )}
          {securityApproved && (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--color-accent)] bg-[var(--color-accent-muted)] px-2.5 py-1 rounded-full">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
              </svg>
              Secured
            </span>
          )}
          {targetGrant && (
            <span className="text-xs text-[var(--color-text-muted)] truncate">
              {targetGrant}
            </span>
          )}
        </div>
      )}

      {/* Compliance Audit Checklist (Matches mockup) */}
      {isCompliant && securityApproved && (
        <div className="m-4 p-4 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border-accent)] shadow-[var(--shadow-glow-green)] animate-fade-in">
          <div className="flex items-center gap-2 mb-2 text-[var(--color-accent)] font-semibold text-xs uppercase tracking-wider">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            Passed Compliance & Security
          </div>
          <ul className="space-y-1.5 text-xs text-[var(--color-text-secondary)]">
            <li className="flex items-center gap-2">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
              Grant Eligibility Met
            </li>
            <li className="flex items-center gap-2">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
              Standard Terms Accepted
            </li>
            <li className="flex items-center gap-2">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
              PII / Privacy Audit Passed
            </li>
            <li className="flex items-center gap-2">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
              Ecological Metrics Verified
            </li>
          </ul>
        </div>
      )}

      {/* Document body */}
      <div className="flex-1 overflow-y-auto px-5 py-5 border-b border-[var(--color-border)]">
        <div
          className="proposal-content text-sm"
          dangerouslySetInnerHTML={{ __html: markdownToHtml(proposal) }}
        />
      </div>

      {/* Bottom Button Panel (Matches mockup layout) */}
      <div className="p-4 bg-[var(--color-bg-secondary)] flex gap-2">
        <button
          onClick={() => {
            const blob = new Blob([proposal], { type: "text/markdown" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${(targetGrant || "grant").toLowerCase().replace(/[^a-z0-9]+/g, "_")}_proposal.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          }}
          className="btn-ghost flex-1 py-2 px-3 text-xs flex items-center justify-center gap-1.5 cursor-pointer"
          title="Download proposal as Markdown"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download (.md)
        </button>

        <button
          onClick={() => {
            alert("🎉 Proposal submitted successfully to the funding agency database!");
          }}
          className="btn-primary flex-1 py-2 px-3 text-xs flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 2 15 22 11 13 2 9 22 2" />
            <line x1="22" y1="2" x2="11" y2="13" />
          </svg>
          Submit Proposal
        </button>
      </div>
    </aside>
  );
}
