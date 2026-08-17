import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/test-utils";
import IngestPage from "@/pages/IngestPage";

describe("IngestPage", () => {
  it("requires confirmation before ingesting, then shows the result table", async () => {
    renderWithProviders(<IngestPage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /^ingest$/i }));

    const dialog = await screen.findByRole("dialog");
    await user.click(screen.getByRole("button", { name: /confirm ingest/i }));

    await waitFor(() => expect(dialog).not.toBeInTheDocument());
    await waitFor(() => expect(screen.getByText("who_hypertension")).toBeInTheDocument());
    expect(screen.getByText("nice_ng136")).toBeInTheDocument();
    expect(screen.getAllByText("76").length).toBe(2); // chunk_count + indexed_vector_count
  });

  it("unchecking both docs disables the ingest button", async () => {
    renderWithProviders(<IngestPage />);
    const user = userEvent.setup();

    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);
    await user.click(checkboxes[1]);

    expect(screen.getByRole("button", { name: /^ingest$/i })).toBeDisabled();
  });
});
