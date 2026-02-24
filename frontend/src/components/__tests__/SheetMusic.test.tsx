import { render, screen, act } from "@testing-library/react";
import SheetMusic from "../SheetMusic";

// Mock abcjs
const mockRenderAbc = jest.fn();
jest.mock("abcjs", () => ({
  __esModule: true,
  renderAbc: (...args: unknown[]) => mockRenderAbc(...args),
}));

beforeEach(() => {
  mockRenderAbc.mockClear();
});

describe("SheetMusic", () => {
  it("renders container element", async () => {
    await act(async () => {
      render(<SheetMusic abc="X:1\nK:C\nCDEF" />);
    });
    expect(screen.getByTestId("sheet-music")).toBeInTheDocument();
  });

  it("calls abcjs.renderAbc with the abc string", async () => {
    const abc = "X:1\nK:C\nCDEF";
    await act(async () => {
      render(<SheetMusic abc={abc} />);
    });
    expect(mockRenderAbc).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      abc,
      expect.objectContaining({ responsive: "resize" }),
    );
  });

  it("shows fallback on render error", async () => {
    mockRenderAbc.mockImplementation(() => {
      throw new Error("render failed");
    });
    const abc = "invalid abc";
    await act(async () => {
      render(<SheetMusic abc={abc} />);
    });
    expect(screen.getByTestId("sheet-music-fallback")).toBeInTheDocument();
    expect(screen.getByText(abc)).toBeInTheDocument();
  });
});
