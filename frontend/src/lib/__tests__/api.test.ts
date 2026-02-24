import { getStatus, streamChat, uploadFile, getFileUrl, getMidiDataUri, resetChat, getChatHistory } from "../api";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// The API client resolves the base URL from NEXT_PUBLIC_API_URL.
// In tests, this defaults to "http://localhost:8000".
const BASE = "http://localhost:8000/api";

beforeEach(() => {
  mockFetch.mockReset();
});

describe("getStatus", () => {
  it("fetches /api/status and returns JSON", async () => {
    const mockData = {
      ollama: { available: true, models: ["qwen2.5:32b"] },
      knowledge_base: { documents: 10, categories: {} },
      transcription: { available: false },
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const result = await getStatus();
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith(`${BASE}/status`);
  });

  it("throws on non-OK response", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });
    await expect(getStatus()).rejects.toThrow("Status error: 500");
  });
});

describe("uploadFile", () => {
  it("posts file as FormData", async () => {
    const mockResponse = {
      analysis: "C major, 120 BPM",
      midi_summary: "MIDI summary",
      error: null,
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const file = new File(["data"], "test.mid", { type: "audio/midi" });
    const result = await uploadFile("session-123", file);

    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      `${BASE}/files/upload`,
      expect.objectContaining({
        method: "POST",
        headers: { "X-Session-ID": "session-123" },
      }),
    );
  });

  it("returns error on failed upload", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "Unsupported file type" }),
    });

    const file = new File(["data"], "test.pdf", { type: "application/pdf" });
    const result = await uploadFile("session-123", file);

    expect(result.error).toBe("Unsupported file type");
  });
});

describe("getFileUrl", () => {
  it("returns correct download URL", () => {
    expect(getFileUrl("song.mid")).toBe(`${BASE}/files/download/song.mid`);
  });

  it("encodes special characters", () => {
    expect(getFileUrl("my song.mid")).toBe(
      `${BASE}/files/download/my%20song.mid`,
    );
  });
});

describe("streamChat", () => {
  /** Wait for a condition to be met, polling with microtask yields */
  async function waitForCondition(
    check: () => boolean,
    timeoutMs = 2000,
  ) {
    const start = Date.now();
    while (!check()) {
      if (Date.now() - start > timeoutMs) {
        throw new Error("Timed out waiting for condition");
      }
      await new Promise((r) => setTimeout(r, 10));
    }
  }

  /** Create a mock body with a getReader() that returns chunks as Uint8Array */
  function makeMockBody(text: string) {
    const bytes = Array.from(text).map((c) => c.charCodeAt(0));
    const chunk = new Uint8Array(bytes);
    let read = false;
    return {
      getReader: () => ({
        read: jest.fn(async () => {
          if (!read) {
            read = true;
            return { done: false as const, value: chunk };
          }
          return { done: true as const, value: undefined };
        }),
      }),
    };
  }

  it("parses SSE token events and calls onToken", async () => {
    const sseData = [
      'event: token\ndata: {"text":"Hello"}\n\n',
      'event: token\ndata: {"text":" world"}\n\n',
      'event: done\ndata: {}\n\n',
    ].join("");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: makeMockBody(sseData),
    });

    const onToken = jest.fn();
    const onDone = jest.fn();
    streamChat("sess-1", "hi", "Balanced", { onToken, onDone });

    await waitForCondition(() => onDone.mock.calls.length > 0);

    expect(onToken).toHaveBeenCalledWith("Hello");
    expect(onToken).toHaveBeenCalledWith(" world");
    expect(onDone).toHaveBeenCalled();
  });

  it("calls onFiles when files event received", async () => {
    const sseData = [
      'event: token\ndata: {"text":"Here"}\n\n',
      'event: files\ndata: {"files":["song.mid"]}\n\n',
      'event: done\ndata: {}\n\n',
    ].join("");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: makeMockBody(sseData),
    });

    const onToken = jest.fn();
    const onFiles = jest.fn();
    streamChat("sess-1", "gen midi", "Balanced", { onToken, onFiles });

    await waitForCondition(() => onFiles.mock.calls.length > 0);

    expect(onFiles).toHaveBeenCalledWith(["song.mid"]);
  });

  it("calls onError when error event received", async () => {
    const sseData = 'event: error\ndata: {"message":"Ollama down"}\n\n';

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: makeMockBody(sseData),
    });

    const onToken = jest.fn();
    const onError = jest.fn();
    streamChat("sess-1", "hi", "Balanced", { onToken, onError });

    await waitForCondition(() => onError.mock.calls.length > 0);

    expect(onError).toHaveBeenCalledWith("Ollama down");
  });

  it("calls onError on non-OK response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    const onToken = jest.fn();
    const onError = jest.fn();
    streamChat("sess-1", "hi", "Balanced", { onToken, onError });

    await waitForCondition(() => onError.mock.calls.length > 0);

    expect(onError).toHaveBeenCalledWith("Chat request failed: 500");
  });

  it("calls onError when no response body", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: null,
    });

    const onToken = jest.fn();
    const onError = jest.fn();
    streamChat("sess-1", "hi", "Balanced", { onToken, onError });

    await waitForCondition(() => onError.mock.calls.length > 0);

    expect(onError).toHaveBeenCalledWith("No response body");
  });

  it("returns AbortController", () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: makeMockBody('event: done\ndata: {}\n\n'),
    });

    const controller = streamChat("sess-1", "hi", "Balanced", { onToken: jest.fn() });
    expect(controller).toBeInstanceOf(AbortController);
  });
});

describe("getMidiDataUri", () => {
  it("fetches MIDI data URI", async () => {
    const mockData = { data_uri: "data:audio/midi;base64,abc" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const result = await getMidiDataUri("song.mid");
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith(`${BASE}/files/midi/song.mid`);
  });

  it("throws on non-OK response", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    await expect(getMidiDataUri("missing.mid")).rejects.toThrow("MIDI fetch failed: 404");
  });
});

describe("resetChat", () => {
  it("posts to /api/chat/reset", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    await resetChat("session-123");

    expect(mockFetch).toHaveBeenCalledWith(
      `${BASE}/chat/reset`,
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "X-Session-ID": "session-123",
        }),
      }),
    );
  });
});

describe("getChatHistory", () => {
  it("fetches chat history with session header", async () => {
    const mockHistory = {
      messages: [{ role: "user", content: "hello" }],
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockHistory),
    });

    const result = await getChatHistory("session-123");
    expect(result).toEqual(mockHistory);
    expect(mockFetch).toHaveBeenCalledWith(
      `${BASE}/chat/history`,
      expect.objectContaining({
        headers: { "X-Session-ID": "session-123" },
      }),
    );
  });
});
