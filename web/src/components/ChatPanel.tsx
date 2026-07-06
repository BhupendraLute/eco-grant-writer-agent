"use client";

import { useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/types";
import { markdownToHtml } from "@/utils/markdown";

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onOptionClick: (value: string, displayText: string) => void;
}

export default function ChatPanel({
  messages,
  loading,
  onOptionClick,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      {messages.map((msg, i) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
          style={{ animationDelay: `${Math.min(i * 30, 200)}ms` }}
        >
          <div className="flex flex-col gap-2 max-w-[85%]">
            {/* Bubble */}
            <div
              className={
                msg.role === "user" ? "bubble-user" : "bubble-assistant"
              }
            >
              {msg.role === "assistant" ? (
                <div
                  className="prose-sm"
                  dangerouslySetInnerHTML={{
                    __html: markdownToHtml(msg.content),
                  }}
                />
              ) : (
                <span>{msg.content}</span>
              )}
            </div>

            {/* Options (pills) */}
            {msg.role === "assistant" &&
              msg.options.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-1">
                  {msg.options.map((opt) => (
                    <button
                      key={opt}
                      onClick={() =>
                        onOptionClick(
                          msg.option_to_val[opt] || opt,
                          opt
                        )
                      }
                      className="btn-pill"
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}
          </div>
        </div>
      ))}

      {/* Typing indicator */}
      {loading && (
        <div className="flex justify-start animate-fade-in">
          <div className="bubble-assistant">
            <div className="typing-indicator flex items-center gap-1 py-1 px-1">
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
