import { render, screen } from "@testing-library/react";
import GuitarTab from "../GuitarTab";

describe("GuitarTab", () => {
  const sampleTab = `e|---0---0---|
B|---1---1---|
G|---0---0---|
D|---2---2---|
A|---3---3---|
E|-----------|`;

  it("renders preformatted tab content", () => {
    render(<GuitarTab tab={sampleTab} />);
    const pre = screen.getByTestId("guitar-tab");
    expect(pre.tagName).toBe("PRE");
    expect(pre).toHaveClass("font-mono");
  });

  it("renders all tab lines", () => {
    render(<GuitarTab tab={sampleTab} />);
    const pre = screen.getByTestId("guitar-tab");
    // All lines should be present in the output
    expect(pre.textContent).toContain("e|---0---0---|");
    expect(pre.textContent).toContain("E|-----------|");
  });

  it("highlights chord names in label lines", () => {
    const tabWithChords = `Am          Dm7
e|---0---0---|---1---1---|
B|---1---1---|---1---1---|
G|---2---2---|---2---2---|
D|---2---2---|---0---0---|
A|---0---0---|-----------|
E|-----------|-----------|`;
    const { container } = render(<GuitarTab tab={tabWithChords} />);
    // Chord names should be highlighted with amber color
    const chordSpans = container.querySelectorAll(".text-amber-400.font-bold");
    expect(chordSpans.length).toBeGreaterThanOrEqual(1);
  });

  it("has correct styling classes", () => {
    render(<GuitarTab tab={sampleTab} />);
    const pre = screen.getByTestId("guitar-tab");
    expect(pre).toHaveClass("bg-bark-800");
    expect(pre).toHaveClass("border-bark-600");
    expect(pre).toHaveClass("rounded-md");
  });
});
