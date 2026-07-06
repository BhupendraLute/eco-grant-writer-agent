"use client";

/**
 * Custom hook for managing agent state and communication.
 * Central state management for the entire application.
 */

import { useState, useCallback, useRef } from "react";
import { createSession, sendMessage } from "@/lib/api";
import type { AgentState, ChatMessage, Phase } from "@/lib/types";
import { DEFAULT_STATE } from "@/lib/types";

// Generate unique message IDs
let msgCounter = 0;
function nextMsgId(): string {
  return `msg_${Date.now()}_${++msgCounter}`;
}

export interface UseAgentReturn {
  /** All chat messages */
  messages: ChatMessage[];
  /** Current agent state */
  state: AgentState;
  /** Current workflow phase */
  phase: Phase;
  /** Whether the agent is processing */
  loading: boolean;
  /** Error message if any */
  error: string | null;
  /** Active HITL interrupt ID */
  interruptId: string | null;
  /** Send a message to the agent */
  send: (message: string, displayText?: string) => Promise<void>;
  /** Send a HITL response */
  respond: (message: string) => Promise<void>;
  /** Reset the conversation */
  reset: () => void;
}

export function useAgent(): UseAgentReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [state, setState] = useState<AgentState>(DEFAULT_STATE);
  const [phase, setPhase] = useState<Phase>("welcome");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interruptId, setInterruptId] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(null);

  const ensureSession = useCallback(async (): Promise<string> => {
    if (!sessionIdRef.current) {
      sessionIdRef.current = await createSession();
    }
    return sessionIdRef.current;
  }, []);

  const send = useCallback(
    async (message: string, displayText?: string) => {
      setError(null);
      setLoading(true);

      // Add user message to chat
      const userMsg: ChatMessage = {
        id: nextMsgId(),
        role: "user",
        content: displayText || message,
        options: [],
        option_to_val: {},
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Move from welcome to intake on first message
      setPhase((prev) => (prev === "welcome" ? "intake" : prev));

      try {
        const sessionId = await ensureSession();
        const currentInterrupt = interruptId;

        // Clear interrupt before sending
        setInterruptId(null);

        const res = await sendMessage(
          sessionId,
          message,
          currentInterrupt
        );

        // Add assistant response
        const assistantMsg: ChatMessage = {
          id: nextMsgId(),
          role: "assistant",
          content: res.message,
          options: res.options,
          option_to_val: res.option_to_val,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // Update state
        setState(res.state);
        setPhase(res.state.phase || "intake");

        // Set interrupt if HITL triggered
        if (res.interrupt_id) {
          setInterruptId(res.interrupt_id);
        }
      } catch (err) {
        const errMsg =
          err instanceof Error ? err.message : "An unexpected error occurred";
        setError(errMsg);

        // Add error message to chat
        const errorMsg: ChatMessage = {
          id: nextMsgId(),
          role: "assistant",
          content: `**Error:** ${errMsg}\n\nPlease check that the backend server is running on port 8000.`,
          options: ["Try again"],
          option_to_val: { "Try again": "Try again" },
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [ensureSession, interruptId]
  );

  const respond = useCallback(
    async (message: string) => {
      await send(message);
    },
    [send]
  );

  const reset = useCallback(() => {
    setMessages([]);
    setState(DEFAULT_STATE);
    setPhase("welcome");
    setLoading(false);
    setError(null);
    setInterruptId(null);
    sessionIdRef.current = null;
  }, []);

  return {
    messages,
    state,
    phase,
    loading,
    error,
    interruptId,
    send,
    respond,
    reset,
  };
}
