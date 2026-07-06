"use client";

import { TEMPLATES } from "@/lib/types";

interface TemplateCardsProps {
  onSelect: (prompt: string) => void;
}

export default function TemplateCards({ onSelect }: TemplateCardsProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-3xl w-full animate-slide-up">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-accent)] flex items-center justify-center mx-auto mb-5 shadow-[var(--shadow-glow-green)]">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0f172a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 8c.7-1 1-2.2 1-3.5C18 2.5 16.6 1 14.5 1S11 2.5 11 4.5c0 1.3.3 2.5 1 3.5" />
              <path d="M6 13c-1 .7-2.2 1-3.5 1C.5 14-1 12.6-1 10.5S.5 7 2.5 7c1.3 0 2.5.3 3.5 1" />
              <path d="M12 22c-1-.7-2.2-1-3.5-1C6.5 21 5 22.4 5 24.5S6.4 28 8.5 28c1.3 0 2.5-.3 3.5-1" />
              <path d="M11 15a7 7 0 0 0 7-7" />
              <path d="M4 11a7 7 0 0 0 7 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-[var(--color-text-primary)] mb-2">
            Eco Grant Writer
          </h1>
          <p className="text-[var(--color-text-secondary)] text-base max-w-md mx-auto leading-relaxed">
            AI-powered grant proposal assistant for environmental nonprofits.
            Choose a template or describe your project below.
          </p>
        </div>

        {/* Template Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TEMPLATES.map((template, i) => (
            <button
              key={template.title}
              onClick={() => onSelect(template.prompt)}
              className="template-card text-left"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="w-10 h-10 rounded-xl bg-[var(--color-accent-muted)] flex items-center justify-center mb-4">
                <TemplateIcon name={template.icon} />
              </div>
              <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-1">
                {template.title}
              </h3>
              <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
                {template.desc}
              </p>
            </button>
          ))}
        </div>

        {/* Subtitle */}
        <p className="text-center text-xs text-[var(--color-text-muted)] mt-8">
          Powered by Google ADK 2.0 & Gemini LLM — with MCP tools, compliance auditing & security guardrails
        </p>
      </div>
    </div>
  );
}

function TemplateIcon({ name }: { name: string }) {
  switch (name) {
    case "mountain-snow":
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m8 3 4 8 5-5 5 15H2L8 3z" />
          <path d="m4.14 15.08 2.86-2.86" />
          <path d="M15 9c.64-.64 1.52-1 2.5-1s1.86.36 2.5 1" />
        </svg>
      );
    case "trees":
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 10v.2A3 3 0 0 1 8.9 16H5a3 3 0 0 1-1-5.8V10a3 3 0 0 1 6 0" />
          <path d="M7 16v6" />
          <path d="M13 19v3" />
          <path d="M18 10v.2A3 3 0 0 1 16.9 16H13a3 3 0 0 1-1-5.8V10a3 3 0 0 1 6 0" />
        </svg>
      );
    case "book-open":
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 7v14" />
          <path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z" />
        </svg>
      );
    default:
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
        </svg>
      );
  }
}
