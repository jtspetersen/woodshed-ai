import { renderHook, act, waitFor } from "@testing-library/react";
import { useStatus } from "../useStatus";

const mockStatus = {
  ollama: {
    available: true,
    models: ["qwen2.5:32b"],
    primary_model: "qwen2.5:32b",
    fast_model: "qwen2.5:7b",
  },
  knowledge_base: { available: true, total_chunks: 100 },
  transcription: { available: false },
};

const mockGetStatus = jest.fn();

jest.mock("@/lib/api", () => ({
  getStatus: (...args: unknown[]) => mockGetStatus(...args),
}));

beforeEach(() => {
  jest.useFakeTimers();
  mockGetStatus.mockReset();
});

afterEach(() => {
  jest.useRealTimers();
});

describe("useStatus", () => {
  it("starts with null status", () => {
    mockGetStatus.mockResolvedValue(mockStatus);
    const { result } = renderHook(() => useStatus());
    expect(result.current.status).toBeNull();
  });

  it("fetches status on mount", async () => {
    mockGetStatus.mockResolvedValue(mockStatus);
    const { result } = renderHook(() => useStatus());

    await waitFor(() => {
      expect(result.current.status).toEqual(mockStatus);
    });
    expect(mockGetStatus).toHaveBeenCalledTimes(1);
  });

  it("sets status to null on fetch error", async () => {
    mockGetStatus.mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => useStatus());

    await waitFor(() => {
      expect(mockGetStatus).toHaveBeenCalled();
    });
    expect(result.current.status).toBeNull();
  });

  it("polls on interval", async () => {
    mockGetStatus.mockResolvedValue(mockStatus);
    renderHook(() => useStatus());

    await waitFor(() => {
      expect(mockGetStatus).toHaveBeenCalledTimes(1);
    });

    // Advance past the poll interval
    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    await waitFor(() => {
      expect(mockGetStatus).toHaveBeenCalledTimes(2);
    });
  });

  it("cleans up interval on unmount", async () => {
    mockGetStatus.mockResolvedValue(mockStatus);
    const { unmount } = renderHook(() => useStatus());

    await waitFor(() => {
      expect(mockGetStatus).toHaveBeenCalledTimes(1);
    });

    unmount();

    // Advance timers — should not trigger another poll
    await act(async () => {
      jest.advanceTimersByTime(60_000);
    });

    expect(mockGetStatus).toHaveBeenCalledTimes(1);
  });
});
