import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import AboutPage from "@/pages/AboutPage";

describe("AboutPage", () => {
  it("renders all three guardrail layers and demo-case deep links", () => {
    renderWithProviders(<AboutPage />);

    expect(screen.getByText("INPUT SAFETY")).toBeInTheDocument();
    expect(screen.getByText("RETRIEVAL CONFIDENCE")).toBeInTheDocument();
    expect(screen.getByText("FACT AUDIT")).toBeInTheDocument();

    const demoLinks = screen.getAllByRole("link", { name: /blood pressure|amlodipine|type 2 diabetes/i });
    expect(demoLinks).toHaveLength(3);
    expect(demoLinks[0]).toHaveAttribute(
      "href",
      expect.stringContaining("/?q=What%20is%20the%20clinic%20blood%20pressure%20target"),
    );
  });

  it("shows one demo case per gate verdict, so each safety path is demonstrable", () => {
    renderWithProviders(<AboutPage />);

    expect(screen.getAllByText("Allowed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Caution").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Refused").length).toBeGreaterThan(0);
  });
});
