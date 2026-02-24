import { render, screen } from "@testing-library/react";
import ChordTag from "../ChordTag";

describe("ChordTag", () => {
  it("renders children text", () => {
    render(<ChordTag>Dm7</ChordTag>);
    expect(screen.getByText("Dm7")).toBeInTheDocument();
  });

  it("applies the chord-tag class for mono font styling", () => {
    render(<ChordTag>Cmaj7</ChordTag>);
    const el = screen.getByTestId("chord-tag");
    expect(el).toHaveClass("chord-tag");
  });

  it("accepts additional className", () => {
    render(<ChordTag className="ml-2">G7</ChordTag>);
    const el = screen.getByTestId("chord-tag");
    expect(el).toHaveClass("ml-2");
  });
});
