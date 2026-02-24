import { render, screen, fireEvent } from "@testing-library/react";
import CreativityControl from "../CreativityControl";

describe("CreativityControl", () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockReset();
  });

  it("renders all three options", () => {
    render(<CreativityControl value="Balanced" onChange={mockOnChange} />);
    expect(screen.getByText("More Precise")).toBeInTheDocument();
    expect(screen.getByText("Balanced")).toBeInTheDocument();
    expect(screen.getByText("More Creative")).toBeInTheDocument();
  });

  it("marks the selected option as checked", () => {
    render(<CreativityControl value="Balanced" onChange={mockOnChange} />);
    const balanced = screen.getByText("Balanced");
    expect(balanced).toHaveAttribute("aria-checked", "true");

    const precise = screen.getByText("More Precise");
    expect(precise).toHaveAttribute("aria-checked", "false");
  });

  it("fires onChange when clicking an option", () => {
    render(<CreativityControl value="Balanced" onChange={mockOnChange} />);
    fireEvent.click(screen.getByText("More Creative"));
    expect(mockOnChange).toHaveBeenCalledWith("More Creative");
  });

  it("does not fire onChange when disabled", () => {
    render(
      <CreativityControl value="Balanced" onChange={mockOnChange} disabled />,
    );
    fireEvent.click(screen.getByText("More Creative"));
    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it("has radiogroup role with label", () => {
    render(<CreativityControl value="Balanced" onChange={mockOnChange} />);
    expect(screen.getByRole("radiogroup")).toHaveAttribute(
      "aria-label",
      "Creativity level",
    );
  });
});
