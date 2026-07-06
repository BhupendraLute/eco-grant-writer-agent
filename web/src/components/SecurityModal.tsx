"use client";

interface SecurityModalProps {
  message: string;
  onApprove: () => void;
  onReject: () => void;
}

export default function SecurityModal({
  message,
  onApprove,
  onReject,
}: SecurityModalProps) {
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Security guardrail alert">
      <div className="modal-content">
        {/* Shield icon */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-xl bg-[var(--color-danger-muted)] flex items-center justify-center flex-shrink-0">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
              <path d="M12 8v4" />
              <path d="M12 16h.01" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
              Security Guardrail Triggered
            </h2>
            <p className="text-sm text-[var(--color-danger)] font-medium mt-0.5">
              PII Detected in Proposal
            </p>
          </div>
        </div>

        {/* Message */}
        <div className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl p-4 mb-6 max-h-[200px] overflow-y-auto">
          <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed whitespace-pre-wrap">
            {message || "A security review is required before proceeding. Personally identifiable information (PII) such as SSN, bank details, or confidential data has been detected in the proposal draft. Proceed with caution."}
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onApprove}
            className="btn-ghost flex-1 border-[var(--color-border-accent)] text-[var(--color-accent)] hover:bg-[var(--color-accent-muted)]"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline mr-1.5">
              <path d="M20 6 9 17l-5-5" />
            </svg>
            Approve (Bypass)
          </button>
          <button
            onClick={onReject}
            className="btn-danger flex-1"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline mr-1.5">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
            Reject (Abort)
          </button>
        </div>
      </div>
    </div>
  );
}
