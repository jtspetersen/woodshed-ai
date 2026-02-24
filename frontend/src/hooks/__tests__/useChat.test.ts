import { renderHook, act } from "@testing-library/react";
import { useChat } from "../useChat";

import type { ToolCallInfo } from "@/lib/types";

// Capture streamChat callbacks for manual invocation
let capturedCallbacks: {
  onToken: (text: string) => void;
  onStatus?: (step: string) => void;
  onToolCall?: (toolCall: ToolCallInfo) => void;
  onFiles?: (files: string[]) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
};
const mockAbort = jest.fn();

jest.mock("@/lib/api", () => ({
  streamChat: jest.fn(
    (
      _sid: string,
      _msg: string,
      _creativity: string,
      callbacks: typeof capturedCallbacks,
    ) => {
      capturedCallbacks = callbacks;
      return { abort: mockAbort };
    },
  ),
  resetChat: jest.fn(() => Promise.resolve()),
}));

jest.mock("@/lib/session", () => ({
  getSessionId: () => "test-session-id",
  resetSessionId: () => "new-session-id",
}));

// Mock requestAnimationFrame: collect callbacks for manual flushing
let rafCallbacks: Array<FrameRequestCallback> = [];
let rafCounter = 1;
global.requestAnimationFrame = jest.fn((cb) => {
  rafCallbacks.push(cb);
  return rafCounter++;
});
global.cancelAnimationFrame = jest.fn();

function flushRAF() {
  const cbs = rafCallbacks;
  rafCallbacks = [];
  cbs.forEach((cb) => cb(0));
}

// Mock crypto.randomUUID
let uuidCounter = 0;
Object.defineProperty(globalThis, "crypto", {
  value: { randomUUID: () => `uuid-${++uuidCounter}` },
});

beforeEach(() => {
  uuidCounter = 0;
  rafCallbacks = [];
  rafCounter = 1;
  mockAbort.mockClear();
  jest.clearAllMocks();
});

describe("useChat", () => {
  it("starts with empty state", () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toHaveLength(0);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("appends user and assistant messages on sendMessage", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("Hello");
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("");
    expect(result.current.isStreaming).toBe(true);
  });

  it("accumulates tokens into assistant message", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      capturedCallbacks.onToken("Hi ");
      capturedCallbacks.onToken("there!");
      flushRAF();
    });

    const lastMsg = result.current.messages[result.current.messages.length - 1];
    // Both tokens should be accumulated in a single rAF flush
    expect(lastMsg.content).toBe("Hi there!");
  });

  it("attaches files on files event", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Generate MIDI", "Balanced");
    });

    act(() => {
      capturedCallbacks.onFiles?.(["progression.mid"]);
    });

    const lastMsg = result.current.messages[result.current.messages.length - 1];
    expect(lastMsg.files).toEqual(["progression.mid"]);
  });

  it("sets isStreaming false on done", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    expect(result.current.isStreaming).toBe(true);

    act(() => {
      capturedCallbacks.onDone?.();
    });

    expect(result.current.isStreaming).toBe(false);
  });

  it("sets error on error event", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      capturedCallbacks.onError?.("Ollama offline");
    });

    expect(result.current.error).toBe("Ollama offline");
    expect(result.current.isStreaming).toBe(false);
  });

  it("aborts stream on cancel", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      result.current.cancel();
    });

    expect(mockAbort).toHaveBeenCalled();
    expect(result.current.isStreaming).toBe(false);
  });

  it("tracks statusStep from status events", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      capturedCallbacks.onStatus?.("Searching knowledge base...");
    });

    expect(result.current.statusStep).toBe("Searching knowledge base...");
  });

  it("clears statusStep when first token arrives", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      capturedCallbacks.onStatus?.("Thinking...");
    });
    expect(result.current.statusStep).toBe("Thinking...");

    act(() => {
      capturedCallbacks.onToken("Hi");
      flushRAF();
    });
    expect(result.current.statusStep).toBeNull();
  });

  it("attaches tool calls to assistant message", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Analyze Dm7", "Balanced");
    });

    const toolCall: ToolCallInfo = {
      name: "analyze_chord",
      arguments: { chord_symbol: "Dm7" },
      result: { root: "D", quality: "minor seventh" },
    };

    act(() => {
      capturedCallbacks.onToolCall?.(toolCall);
    });

    const lastMsg = result.current.messages[result.current.messages.length - 1];
    expect(lastMsg.toolCalls).toHaveLength(1);
    expect(lastMsg.toolCalls![0].name).toBe("analyze_chord");
  });

  it("clears statusStep on done", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      capturedCallbacks.onStatus?.("Thinking...");
    });

    act(() => {
      capturedCallbacks.onDone?.();
    });

    expect(result.current.statusStep).toBeNull();
  });

  it("clears messages on reset", async () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("Hello", "Balanced");
    });

    act(() => {
      capturedCallbacks.onDone?.();
    });

    await act(async () => {
      await result.current.reset();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBeNull();
  });
});
