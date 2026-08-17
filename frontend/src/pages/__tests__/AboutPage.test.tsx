import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import AboutPage from "@/pages/AboutPage";

describe("AboutPage", () => {
  it("renders all three guardrail layers and demo-case deep links", () => {
    renderWithProviders(<AboutPage />);

    expect(screen.getByText("Input gate")).toBeInTheDocument();
    expect(screen.getByText("Retrieval confidence threshold")).toBeInTheDocument();
    expect(screen.getByText("Post-generation claim audit")).toBeInTheDocument();

    const tryLinks = screen.getAllByRole("link", { name: /try this query/i });
    expect(tryLinks).toHaveLength(3);
    expect(tryLinks[0]).toHaveAttribute(
      "href",
      expect.stringContaining("/?q=What%20is%20the%20clinic%20blood%20pressure%20target"),
    );
  });
});
