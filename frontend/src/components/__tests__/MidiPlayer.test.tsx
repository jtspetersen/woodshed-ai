import { render, screen, act } from "@testing-library/react";
import MidiPlayer from "../MidiPlayer";

// Simulate the web component already being registered
const originalGet = customElements.get.bind(customElements);
beforeEach(() => {
  jest.spyOn(customElements, "get").mockImplementation((name: string) => {
    if (name === "midi-player") {
      return class {} as unknown as CustomElementConstructor;
    }
    return originalGet(name);
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("MidiPlayer", () => {
  it("renders player container", async () => {
    await act(async () => {
      render(<MidiPlayer src="data:audio/midi;base64,abc123" />);
    });
    expect(screen.getByTestId("midi-player")).toBeInTheDocument();
  });

  it("renders download button with src", async () => {
    const src = "data:audio/midi;base64,abc123";
    await act(async () => {
      render(<MidiPlayer src={src} />);
    });
    const downloadLink = screen.getByTestId("midi-download");
    expect(downloadLink).toHaveAttribute("href", src);
    expect(downloadLink).toHaveAttribute("download");
  });

  it("shows empty message when src is empty", () => {
    render(<MidiPlayer src="" />);
    expect(screen.getByTestId("midi-player-empty")).toBeInTheDocument();
    expect(screen.getByText("No MIDI source available.")).toBeInTheDocument();
  });

  it("renders header with MIDI Playback label", async () => {
    await act(async () => {
      render(<MidiPlayer src="test.mid" />);
    });
    expect(screen.getByText("MIDI Playback")).toBeInTheDocument();
  });

  it("renders web component elements after loading", async () => {
    await act(async () => {
      render(<MidiPlayer src="test.mid" />);
    });
    expect(screen.getByTestId("midi-player-element")).toBeInTheDocument();
    expect(screen.getByTestId("midi-visualizer")).toBeInTheDocument();
  });

  it("shows loading state when web component not registered", async () => {
    jest.spyOn(customElements, "get").mockReturnValue(undefined);

    // Mock createElement to prevent actual script injection
    const originalCreateElement = document.createElement.bind(document);
    jest.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = originalCreateElement(tag);
      if (tag === "script") {
        // Prevent onload from firing, so it stays in loading state
        Object.defineProperty(el, "src", { set: () => {}, get: () => "" });
      }
      return el;
    });

    await act(async () => {
      render(<MidiPlayer src="test.mid" />);
    });
    expect(screen.getByTestId("midi-player-loading")).toBeInTheDocument();
    expect(screen.getByText("Loading MIDI player...")).toBeInTheDocument();
  });
});
