import { render, screen } from "@testing-library/react";
import MessageBubble from "../MessageBubble";
import type { DisplayMessage } from "@/lib/types";

jest.mock("@/lib/api", () => ({
  getFileUrl: (f: string) => `/api/files/download/${f}`,
  getMidiDataUri: jest.fn(() =>
    Promise.resolve({ data_uri: "data:audio/midi;base64,test" }),
  ),
}));

describe("MessageBubble", () => {
  it("renders user message right-aligned", () => {
    const msg: DisplayMessage = {
      id: "1",
      role: "user",
      content: "Hello",
    };
    render(<MessageBubble message={msg} />);
    const bubble = screen.getByTestId("message-bubble");
    expect(bubble).toHaveClass("justify-end");
  });

  it("renders assistant message left-aligned", () => {
    const msg: DisplayMessage = {
      id: "2",
      role: "assistant",
      content: "Hi there!",
    };
    render(<MessageBubble message={msg} />);
    const bubble = screen.getByTestId("message-bubble");
    expect(bubble).toHaveClass("justify-start");
  });

  it("renders bold markdown", () => {
    const msg: DisplayMessage = {
      id: "3",
      role: "assistant",
      content: "This is **bold** text",
    };
    render(<MessageBubble message={msg} />);
    const strong = screen.getByText("bold");
    expect(strong.tagName).toBe("STRONG");
  });

  it("does not render file download link for MIDI files (they have inline players)", () => {
    const msg: DisplayMessage = {
      id: "4",
      role: "assistant",
      content: "Here is your file",
      files: ["progression.mid"],
    };
    render(<MessageBubble message={msg} />);
    expect(screen.queryByTestId("file-link")).toBeNull();
  });

  it("renders file download links for non-MIDI files", () => {
    const msg: DisplayMessage = {
      id: "7",
      role: "assistant",
      content: "Here is your export",
      files: ["progression.musicxml"],
    };
    render(<MessageBubble message={msg} />);
    const links = screen.getAllByTestId("file-link");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute(
      "href",
      "/api/files/download/progression.musicxml",
    );
  });

  it("filters MIDI from download links but keeps non-MIDI files", () => {
    const msg: DisplayMessage = {
      id: "8",
      role: "assistant",
      content: "Here are your files",
      files: ["progression.mid", "export.musicxml"],
    };
    render(<MessageBubble message={msg} />);
    const links = screen.getAllByTestId("file-link");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveTextContent("export.musicxml");
  });

  it("does not render file section when no files", () => {
    const msg: DisplayMessage = {
      id: "5",
      role: "assistant",
      content: "No files here",
    };
    render(<MessageBubble message={msg} />);
    expect(screen.queryByTestId("file-link")).toBeNull();
  });

  it("renders chord symbols with chord-tag class", () => {
    const msg: DisplayMessage = {
      id: "6",
      role: "assistant",
      content: "Try playing Dm7 to G7",
    };
    const { container } = render(<MessageBubble message={msg} />);
    const chordTags = container.querySelectorAll(".chord-tag");
    expect(chordTags.length).toBeGreaterThanOrEqual(2);
  });
});
