"use client";

import { useState } from "react";

interface CustomNotesInputProps {
  onSubmit: (notes: string) => void;
  loading: boolean;
}

export default function CustomNotesInput({ onSubmit, loading }: CustomNotesInputProps) {
  const [customNotes, setCustomNotes] = useState("");

  const handleSubmit = () => {
    const trimmed = customNotes.trim();
    if (!trimmed || loading) return;
    onSubmit(trimmed);
    setCustomNotes("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-8 mb-8 animate-slide-up" style={{ animationDelay: "300ms" }}>
      <div className="text-xs text-[var(--color-text-secondary)] font-semibold mb-2 uppercase tracking-wider text-center">
        Or start with your own project notes
      </div>
      <div className="glass-input flex items-end gap-3 p-3 w-full">
        <textarea
          value={customNotes}
          onChange={(e) => setCustomNotes(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste details about your NGO, location, target budget, number of volunteers, and registration info to begin drafting..."
          rows={3}
          disabled={loading}
          className="flex-1 bg-transparent text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] resize-none outline-none text-sm leading-6 max-h-[120px]"
        />
        <button
          onClick={handleSubmit}
          disabled={!customNotes.trim() || loading}
          className="btn-primary flex items-center justify-center w-10 h-10 !p-0 rounded-lg flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Start drafting"
        >
          {loading ? (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#0f172a"
              strokeWidth="2.5"
              className="animate-spin"
            >
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          ) : (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#0f172a"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m22 2-7 20-4-9-9-4Z" />
              <path d="M22 2 11 13" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
