import { render, screen, fireEvent } from "@testing-library/react";
import ChatInterface from "../ChatInterface";
import { useChat } from "@/hooks/useChat";
import { useStatus } from "@/hooks/useStatus";
import type { DisplayMessage } from "@/lib/types";

jest.mock("@/hooks/useChat");
jest.mock("@/hooks/useStatus");
jest.mock("@/lib/api", () => ({
  uploadFile: jest.fn(),
  getFileUrl: (f: string) => `/api/files/download/${f}`,
}));
jest.mock("@/lib/session", () => ({
  getSessionId: () => "test-session",
}));

const mockSendMessage = jest.fn();
const mockReset = jest.fn();
const mockCancel = jest.fn();

function setupMocks(overrides: Partial<ReturnType<typeof useChat>> = {}) {
  (useChat as jest.Mock).mockReturnValue({
    messages: [],
    isStreaming: false,
    error: null,
    statusStep: null,
    statusDetail: null,
    sendMessage: mockSendMessage,
    reset: mockReset,
    cancel: mockCancel,
    ...overrides,
  });

  (useStatus as jest.Mock).mockReturnValue({
    status: null,
  });
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("ChatInterface", () => {
  it("shows example prompts when no messages", () => {
    setupMocks();
    render(<ChatInterface />);
    expect(screen.getByText("Welcome to Woodshed AI")).toBeInTheDocument();
    expect(screen.getAllByTestId("example-prompt")).toHaveLength(6);
  });

  it("shows messages when present", () => {
    const messages: DisplayMessage[] = [
      { id: "1", role: "user", content: "Hello" },
      { id: "2", role: "assistant", content: "Hi!" },
    ];
    setupMocks({ messages });
    render(<ChatInterface />);

    expect(screen.queryByText("Welcome to Woodshed AI")).toBeNull();
    expect(screen.getAllByTestId("message-bubble")).toHaveLength(2);
  });

  it("shows VUMeter during streaming without status step", () => {
    const messages: DisplayMessage[] = [
      { id: "1", role: "user", content: "Hello" },
      { id: "2", role: "assistant", content: "Hi" },
    ];
    setupMocks({ messages, isStreaming: true, statusStep: null });
    render(<ChatInterface />);

    expect(screen.getByTestId("vu-meter")).toBeInTheDocument();
    expect(screen.queryByTestId("thinking-indicator")).not.toBeInTheDocument();
  });

  it("shows ThinkingIndicator when status step is set", () => {
    const messages: DisplayMessage[] = [
      { id: "1", role: "user", content: "Hello" },
      { id: "2", role: "assistant", content: "" },
    ];
    setupMocks({
      messages,
      isStreaming: true,
      statusStep: "Searching knowledge base...",
    });
    render(<ChatInterface />);

    expect(screen.getByTestId("thinking-indicator")).toBeInTheDocument();
    expect(screen.getByText("Searching knowledge base...")).toBeInTheDocument();
    expect(screen.queryByTestId("vu-meter")).not.toBeInTheDocument();
  });

  it("shows error bar when error is set", () => {
    setupMocks({ error: "Something went wrong" });
    render(<ChatInterface />);

    expect(screen.getByTestId("error-bar")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("sends message when example prompt is clicked", () => {
    setupMocks();
    render(<ChatInterface />);

    const prompts = screen.getAllByTestId("example-prompt");
    fireEvent.click(prompts[0]);

    expect(mockSendMessage).toHaveBeenCalledWith(
      "What are the notes in a Dm7 chord?",
      "Balanced",
    );
  });

  it("calls reset when New Chat is clicked", () => {
    setupMocks();
    render(<ChatInterface />);

    fireEvent.click(screen.getByText("New Chat"));
    expect(mockReset).toHaveBeenCalled();
  });
});
