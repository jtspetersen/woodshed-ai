import { render, screen, fireEvent } from "@testing-library/react";
import ThinkingIndicator from "../ThinkingIndicator";

describe("ThinkingIndicator", () => {
  it("renders the step text", () => {
    render(<ThinkingIndicator step="Checking my notes..." />);
    expect(screen.getByText("Checking my notes...")).toBeInTheDocument();
  });

  it("has the correct testid", () => {
    render(<ThinkingIndicator step="Noodling on it..." />);
    expect(screen.getByTestId("thinking-indicator")).toBeInTheDocument();
  });

  it("renders animated dots", () => {
    const { container } = render(<ThinkingIndicator step="Warming up..." />);
    const dots = container.querySelectorAll(".animate-pulse");
    expect(dots.length).toBe(3);
  });

  it("shows chevron when detail is provided", () => {
    const { container } = render(
      <ThinkingIndicator step="Warming up..." detail="Going with qwen3:30b" />,
    );
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("does not show chevron without detail or thinking", () => {
    const { container } = render(<ThinkingIndicator step="Warming up..." />);
    const svgs = container.querySelectorAll("svg");
    expect(svgs.length).toBe(0);
  });

  it("expands to show detail on click", () => {
    render(
      <ThinkingIndicator step="Warming up..." detail="Going with qwen3:30b" />,
    );
    expect(screen.queryByTestId("thinking-detail")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("thinking-toggle"));
    expect(screen.getByTestId("thinking-detail")).toBeInTheDocument();
    expect(screen.getByText("Going with qwen3:30b")).toBeInTheDocument();
  });

  it("shows thinking content when expanded", () => {
    render(
      <ThinkingIndicator
        step="Noodling on it..."
        thinking="Let me analyze this Dm7 chord..."
      />,
    );
    fireEvent.click(screen.getByTestId("thinking-toggle"));
    expect(screen.getByTestId("thinking-content")).toBeInTheDocument();
    expect(
      screen.getByText("Let me analyze this Dm7 chord..."),
    ).toBeInTheDocument();
  });

  it("collapses on second click", () => {
    render(
      <ThinkingIndicator step="Warming up..." detail="detail text" />,
    );
    fireEvent.click(screen.getByTestId("thinking-toggle"));
    expect(screen.getByTestId("thinking-detail")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("thinking-toggle"));
    expect(screen.queryByTestId("thinking-detail")).not.toBeInTheDocument();
  });
});
