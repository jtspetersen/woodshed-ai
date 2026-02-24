import { render, screen, fireEvent } from "@testing-library/react";
import ToolCallBlock from "../ToolCallBlock";
import type { ToolCallInfo } from "@/lib/types";

const mockToolCalls: ToolCallInfo[] = [
  {
    name: "analyze_chord",
    arguments: { chord_symbol: "Dm7" },
    result: {
      root: "D",
      quality: "minor seventh",
      notes: ["D", "F", "A", "C"],
    },
  },
  {
    name: "suggest_next_chord",
    arguments: { chords: ["Dm7", "G7"] },
    result: {
      suggestions: [{ chord: "Cmaj7", reason: "Resolves V7 to I" }],
    },
  },
];

describe("ToolCallBlock", () => {
  it("renders all tool calls", () => {
    render(<ToolCallBlock toolCalls={mockToolCalls} />);
    expect(screen.getByTestId("tool-call-block")).toBeInTheDocument();
    expect(screen.getByText("Broke down that chord")).toBeInTheDocument();
    expect(screen.getByText("Found what comes next")).toBeInTheDocument();
  });

  it("shows formatted arguments", () => {
    render(<ToolCallBlock toolCalls={mockToolCalls} />);
    expect(screen.getByText(/chord_symbol: "Dm7"/)).toBeInTheDocument();
  });

  it("is collapsed by default", () => {
    render(<ToolCallBlock toolCalls={mockToolCalls} />);
    // Result text should not be visible
    expect(screen.queryByText(/"minor seventh"/)).not.toBeInTheDocument();
  });

  it("expands on click to show result", () => {
    render(<ToolCallBlock toolCalls={mockToolCalls} />);
    const toggles = screen.getAllByTestId("tool-call-toggle");
    fireEvent.click(toggles[0]);
    expect(screen.getByText(/"minor seventh"/)).toBeInTheDocument();
  });

  it("collapses when clicking the same toggle again", () => {
    render(<ToolCallBlock toolCalls={mockToolCalls} />);
    const toggles = screen.getAllByTestId("tool-call-toggle");
    fireEvent.click(toggles[0]);
    expect(screen.getByText(/"minor seventh"/)).toBeInTheDocument();
    fireEvent.click(toggles[0]);
    expect(screen.queryByText(/"minor seventh"/)).not.toBeInTheDocument();
  });

  it("uses human-readable label for known tools", () => {
    render(
      <ToolCallBlock
        toolCalls={[
          {
            name: "generate_progression_midi",
            arguments: { chords: ["Am", "F"] },
            result: { file_path: "prog.mid" },
          },
        ]}
      />,
    );
    expect(screen.getByText("Built your MIDI file")).toBeInTheDocument();
  });

  it("falls back to raw name for unknown tools", () => {
    render(
      <ToolCallBlock
        toolCalls={[
          {
            name: "custom_unknown_tool",
            arguments: null,
            result: null,
          },
        ]}
      />,
    );
    expect(screen.getByText("custom_unknown_tool")).toBeInTheDocument();
  });
});
