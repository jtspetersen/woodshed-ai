import { render, screen } from "@testing-library/react";
import VUMeter from "../VUMeter";

describe("VUMeter", () => {
  it("renders the correct number of bars", () => {
    render(<VUMeter bars={7} />);
    const bars = screen.getAllByTestId("vu-bar");
    expect(bars).toHaveLength(7);
  });

  it("defaults to 5 bars", () => {
    render(<VUMeter />);
    const bars = screen.getAllByTestId("vu-bar");
    expect(bars).toHaveLength(5);
  });

  it("shows loading label when active", () => {
    render(<VUMeter active={true} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Loading");
  });

  it("shows idle label when inactive", () => {
    render(<VUMeter active={false} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Idle");
  });

  it("applies animation class when active", () => {
    render(<VUMeter active={true} />);
    const bars = screen.getAllByTestId("vu-bar");
    expect(bars[0]).toHaveClass("animate-vu-pulse");
  });

  it("does not apply animation class when inactive", () => {
    render(<VUMeter active={false} />);
    const bars = screen.getAllByTestId("vu-bar");
    expect(bars[0]).not.toHaveClass("animate-vu-pulse");
  });
});
