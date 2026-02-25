import type {
  ChatHistoryResponse,
  ChatSSEEvent,
  ContentPart,
  FileUploadResponse,
  MidiDataUriResponse,
  StatusResponse,
  ToolCallInfo,
} from "./types";

// Backend URL — resolved from NEXT_PUBLIC_API_URL (set by dev.py) or
// falls back to localhost:8000. Used directly for SSE streaming since
// Next.js rewrites buffer responses, preventing real-time event delivery.
const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const API_BASE = `${BACKEND_URL}/api`;

function headers(sessionId: string): Record<string, string> {
  return {
    "X-Session-ID": sessionId,
    "Content-Type": "application/json",
  };
}

/** GET /api/status */
export async function getStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error(`Status error: ${res.status}`);
  return res.json();
}

/**
 * POST /api/chat — SSE streaming.
 *
 * Calls `onToken` for each token, `onFiles` for generated files,
 * and `onDone` when complete. Returns an AbortController for cancellation.
 */
export function streamChat(
  sessionId: string,
  message: string,
  creativity: string,
  callbacks: {
    onToken: (text: string) => void;
    onStatus?: (step: string, detail?: string) => void;
    onThinking?: (text: string) => void;
    onToolCall?: (toolCall: ToolCallInfo) => void;
    onFiles?: (files: string[]) => void;
    onPart?: (part: ContentPart) => void;
    onDone?: () => void;
    onError?: (message: string) => void;
  },
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: headers(sessionId),
        body: JSON.stringify({ message, creativity }),
        signal: controller.signal,
      });

      if (!res.ok) {
        callbacks.onError?.(`Chat request failed: ${res.status}`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError?.("No response body");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        let currentEvent = "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.slice(6).trim();
          } else if (trimmed.startsWith("data:")) {
            const rawData = trimmed.slice(5).trim();
            try {
              const parsed = JSON.parse(rawData) as ChatSSEEvent["data"];
              if (currentEvent === "token" && "text" in parsed) {
                callbacks.onToken(parsed.text);
              } else if (currentEvent === "status" && "step" in parsed) {
                callbacks.onStatus?.(
                  parsed.step as string,
                  (parsed as Record<string, unknown>).detail as string | undefined,
                );
              } else if (currentEvent === "thinking" && "text" in parsed) {
                callbacks.onThinking?.(parsed.text as string);
              } else if (currentEvent === "tool_call" && "name" in parsed) {
                callbacks.onToolCall?.(parsed as ToolCallInfo);
              } else if (currentEvent === "files" && "files" in parsed) {
                callbacks.onFiles?.(parsed.files as string[]);
              } else if (currentEvent.startsWith("part:")) {
                const partType = currentEvent.slice(5);
                if (partType === "abc" && "abc" in parsed) {
                  callbacks.onPart?.({ type: "abc", abc: parsed.abc as string });
                } else if (partType === "tab" && "tab" in parsed) {
                  callbacks.onPart?.({ type: "tab", tab: parsed.tab as string });
                } else if (partType === "midi" && "filename" in parsed) {
                  callbacks.onPart?.({ type: "midi", filename: parsed.filename as string });
                } else if (partType === "file" && "filename" in parsed) {
                  callbacks.onPart?.({ type: "file", filename: parsed.filename as string });
                }
              } else if (currentEvent === "done") {
                callbacks.onDone?.();
              } else if (currentEvent === "error" && "message" in parsed) {
                callbacks.onError?.(parsed.message as string);
              }
            } catch {
              // Skip malformed JSON lines
            }
            currentEvent = "";
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      callbacks.onError?.(err instanceof Error ? err.message : "Unknown error");
    }
  })();

  return controller;
}

/** POST /api/files/upload */
export async function uploadFile(
  sessionId: string,
  file: File,
): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/files/upload`, {
    method: "POST",
    headers: { "X-Session-ID": sessionId },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Upload failed: ${res.status}` }));
    return { analysis: null, midi_summary: null, error: err.detail ?? "Upload failed" };
  }
  return res.json();
}

/** GET /api/files/download/{filename} — returns the URL for direct download. */
export function getFileUrl(filename: string): string {
  return `${API_BASE}/files/download/${encodeURIComponent(filename)}`;
}

/** GET /api/files/midi/{filename} — returns base64 data URI. */
export async function getMidiDataUri(
  filename: string,
): Promise<MidiDataUriResponse> {
  const res = await fetch(
    `${API_BASE}/files/midi/${encodeURIComponent(filename)}`,
  );
  if (!res.ok) throw new Error(`MIDI fetch failed: ${res.status}`);
  return res.json();
}

/** POST /api/chat/reset */
export async function resetChat(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/chat/reset`, {
    method: "POST",
    headers: headers(sessionId),
  });
}

/** GET /api/chat/history */
export async function getChatHistory(
  sessionId: string,
): Promise<ChatHistoryResponse> {
  const res = await fetch(`${API_BASE}/chat/history`, {
    headers: { "X-Session-ID": sessionId },
  });
  if (!res.ok) throw new Error(`History fetch failed: ${res.status}`);
  return res.json();
}
