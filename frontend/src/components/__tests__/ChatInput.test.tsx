import { render, screen, fireEvent } from "@testing-library/react";
import ChatInput from "../ChatInput";

describe("ChatInput", () => {
  const mockOnSend = jest.fn();
  const mockOnFileUpload = jest.fn();
  const mockOnCancel = jest.fn();

  const defaultProps = {
    onSend: mockOnSend,
    onFileUpload: mockOnFileUpload,
    isStreaming: false,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls onSend on Enter key press", () => {
    render(<ChatInput {...defaultProps} />);
    const textarea = screen.getByTestId("chat-textarea");

    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(mockOnSend).toHaveBeenCalledWith("Hello");
  });

  it("does not call onSend on Shift+Enter", () => {
    render(<ChatInput {...defaultProps} />);
    const textarea = screen.getByTestId("chat-textarea");

    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it("disables Send button when textarea is empty", () => {
    render(<ChatInput {...defaultProps} />);
    const sendButton = screen.getByText("Send");
    expect(sendButton).toBeDisabled();
  });

  it("disables textarea during streaming", () => {
    render(<ChatInput {...defaultProps} isStreaming={true} />);
    const textarea = screen.getByTestId("chat-textarea");
    expect(textarea).toBeDisabled();
  });

  it("shows Cancel button during streaming", () => {
    render(<ChatInput {...defaultProps} isStreaming={true} />);
    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(screen.queryByText("Send")).toBeNull();
  });

  it("calls onCancel when Cancel is clicked", () => {
    render(<ChatInput {...defaultProps} isStreaming={true} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it("clears textarea after sending", () => {
    render(<ChatInput {...defaultProps} />);
    const textarea = screen.getByTestId("chat-textarea") as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(textarea.value).toBe("");
  });
});
