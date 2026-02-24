import { render, screen } from "@testing-library/react";
import StatusBar from "../StatusBar";
import type { StatusResponse } from "@/lib/types";

const mockStatus: StatusResponse = {
  ollama: { available: true, models: ["qwen2.5:32b"] },
  knowledge_base: { documents: 10, categories: {} },
  transcription: { available: false },
};

describe("StatusBar", () => {
  it("renders status dots", () => {
    render(<StatusBar status={mockStatus} />);
    expect(screen.getByTestId("status-dot-ollama")).toBeInTheDocument();
  });

  it("shows sage dot for available services", () => {
    render(<StatusBar status={mockStatus} />);
    const ollamaDot = screen.getByTestId("status-dot-ollama");
    expect(ollamaDot).toHaveClass("bg-sage-400");
  });

  it("shows rust dot for unavailable services", () => {
    render(<StatusBar status={mockStatus} />);
    const transcriptionDot = screen.getByTestId("status-dot-transcription");
    expect(transcriptionDot).toHaveClass("bg-rust-400");
  });

  it("displays model name when Ollama is available", () => {
    render(<StatusBar status={mockStatus} />);
    expect(screen.getByText("qwen2.5:32b")).toBeInTheDocument();
  });

  it("handles null status gracefully", () => {
    render(<StatusBar status={null} />);
    const ollamaDot = screen.getByTestId("status-dot-ollama");
    expect(ollamaDot).toHaveClass("bg-rust-400");
  });
});
