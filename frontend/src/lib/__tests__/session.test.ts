import { getSessionId, resetSessionId } from "../session";

// Mock sessionStorage
const store: Record<string, string> = {};
const mockSessionStorage = {
  getItem: jest.fn((key: string) => store[key] ?? null),
  setItem: jest.fn((key: string, value: string) => {
    store[key] = value;
  }),
  removeItem: jest.fn((key: string) => {
    delete store[key];
  }),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};

Object.defineProperty(window, "sessionStorage", { value: mockSessionStorage });

// Mock crypto.randomUUID
let uuidCounter = 0;
Object.defineProperty(globalThis, "crypto", {
  value: {
    randomUUID: () => `mock-uuid-${++uuidCounter}`,
  },
});

beforeEach(() => {
  Object.keys(store).forEach((k) => delete store[k]);
  uuidCounter = 0;
  jest.clearAllMocks();
});

describe("getSessionId", () => {
  it("creates a new session ID on first call", () => {
    const id = getSessionId();
    expect(id).toBe("mock-uuid-1");
    expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
      "woodshed-session-id",
      "mock-uuid-1",
    );
  });

  it("returns the same ID on subsequent calls", () => {
    const id1 = getSessionId();
    const id2 = getSessionId();
    expect(id1).toBe(id2);
  });
});

describe("resetSessionId", () => {
  it("generates a new ID", () => {
    const original = getSessionId();
    const newId = resetSessionId();
    expect(newId).not.toBe(original);
  });

  it("stores the new ID in sessionStorage", () => {
    resetSessionId();
    expect(mockSessionStorage.setItem).toHaveBeenCalled();
  });
});
