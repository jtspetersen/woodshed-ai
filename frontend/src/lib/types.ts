/** Mirrors Python app/api/schemas.py */

export interface ChatRequest {
  message: string;
  creativity: "More Precise" | "Balanced" | "More Creative";
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

/** A tool call executed by the pipeline. */
export interface ToolCallInfo {
  name: string;
  arguments: Record<string, unknown> | null;
  result: Record<string, unknown> | string | null;
}

/** Chat message with UI-specific fields for rendering. */
export interface DisplayMessage extends ChatMessage {
  id: string;
  files?: string[];
  toolCalls?: ToolCallInfo[];
  thinking?: string;
}

export interface FileUploadResponse {
  analysis: string | null;
  midi_summary: string | null;
  error: string | null;
}

export interface StatusResponse {
  ollama: {
    available: boolean;
    models: string[];
  };
  knowledge_base: {
    documents: number;
    categories: Record<string, number>;
  };
  transcription: {
    available: boolean;
  };
}

export interface MidiDataUriResponse {
  data_uri: string;
  filename: string;
}

/** SSE event types emitted by POST /api/chat */
export type ChatSSEEvent =
  | { event: "token"; data: { text: string } }
  | { event: "status"; data: { step: string; detail?: string } }
  | { event: "thinking"; data: { text: string } }
  | { event: "tool_call"; data: { name: string; arguments: Record<string, unknown> | null; result: Record<string, unknown> | string | null } }
  | { event: "files"; data: { files: string[] } }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: { message: string } };
