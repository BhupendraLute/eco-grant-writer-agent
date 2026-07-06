/**
 * API client for the Eco Grant Writer FastAPI backend.
 */

import type {
  SessionResponse,
  ChatRequest,
  ChatResponse,
  AgentState,
  GrantsResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${errorBody}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

export async function createSession(): Promise<string> {
  const data = await request<SessionResponse>("/api/session", {
    method: "POST",
  });
  return data.session_id;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export async function sendMessage(
  sessionId: string,
  message: string,
  interruptId?: string | null
): Promise<ChatResponse> {
  const body: ChatRequest = {
    session_id: sessionId,
    message,
    interrupt_id: interruptId || undefined,
  };

  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

export async function getState(sessionId: string): Promise<AgentState> {
  return request<AgentState>(`/api/state/${sessionId}`);
}

// ---------------------------------------------------------------------------
// Grants
// ---------------------------------------------------------------------------

export async function listGrants(): Promise<GrantsResponse> {
  return request<GrantsResponse>("/api/grants");
}
