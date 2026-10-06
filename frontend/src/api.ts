import type { ChatResponse } from "./types";

export async function sendMessage(
  message: string,
  sessionId: string | null
): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export async function resetSession(sessionId: string): Promise<void> {
  await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
}