import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/test-utils";
import SearchPage from "@/pages/SearchPage";

describe("SearchPage", () => {
  it("renders the evidence panel for a search, without any answer/confidence content", async () => {
    renderWithProviders(<SearchPage />);
    const user = userEvent.setup();

    await user.type(screen.getByPlaceholderText(/ask a question/i), "ACE inhibitor");
    await user.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => expect(screen.getByText(/evidence panel/i)).toBeInTheDocument());
    expect(screen.getByText("nice_ng136-p016-beee1ff3")).toBeInTheDocument();
    expect(screen.queryByText(/confidence & safety/i)).not.toBeInTheDocument();
  });
});
