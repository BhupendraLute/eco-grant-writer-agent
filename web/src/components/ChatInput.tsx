"use client";

import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  loading,
  placeholder = "Describe your project or ask a question…",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!loading) {
      inputRef.current?.focus();
    }
  }, [loading]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setValue("");

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(
        inputRef.current.scrollHeight,
        120
      )}px`;
    }
  };

  return (
    <div className="border-t border-[var(--color-border)] p-4">
      <div className="glass-input flex items-end gap-3 p-3 max-w-full">
        <textarea
          ref={inputRef}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            handleInput();
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          rows={1}
          className="flex-1 bg-transparent text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] resize-none outline-none text-sm leading-6 max-h-[120px]"
        />

        <button
          onClick={handleSubmit}
          disabled={!value.trim() || loading}
          className="btn-primary flex items-center justify-center w-10 h-10 p-0 rounded-lg flex-shrink-0"
          aria-label="Send message"
        >
          {loading ? (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
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
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z" />
              <path d="m21.854 2.147-10.94 10.939" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
