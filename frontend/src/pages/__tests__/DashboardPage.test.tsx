import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderWithProviders } from "@/test/test-utils";
import { server } from "@/test/mocks/server";
import { E2E_EVAL_REPORT } from "@/test/mocks/handlers";
import DashboardPage from "@/pages/DashboardPage";

const API_BASE = "http://localhost:8000/api/v1";

describe("DashboardPage", () => {
  it("reloads a previously saved run on mount, so a result survives restarting the app", async () => {
    server.use(http.get(`${API_BASE}/evaluation/e2e/latest`, () => HttpResponse.json(E2E_EVAL_REPORT)));
    renderWithProviders(<DashboardPage />);

    await waitFor(() => expect(screen.getByText(/end-to-end evaluation/i)).toBeInTheDocument());
    expect(screen.getByText(/last run/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /re-run end-to-end eval/i })).toBeInTheDocument();
    expect(screen.queryByText(/no evaluation has been run yet/i)).not.toBeInTheDocument();
  });

  it("shows an empty state when the server has no saved run", async () => {
    renderWithProviders(<DashboardPage />);
    // the empty state waits for the "is anything saved?" check rather than flashing first
    await waitFor(() => expect(screen.getByText(/no evaluation has been run yet/i)).toBeInTheDocument());
  });

  it("runs the e2e eval and renders metric tiles, category breakdown, and no-failures state", async () => {
    renderWithProviders(<DashboardPage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /run end-to-end eval/i }));

    await waitFor(() => expect(screen.getByText(/end-to-end evaluation/i)).toBeInTheDocument());
    expect(screen.getAllByText("100.0%").length).toBeGreaterThanOrEqual(2); // citation accuracy + refusal correctness
    expect(screen.getByText("Direct")).toBeInTheDocument();
    expect(screen.getByText(/no failures in this run/i)).toBeInTheDocument();
  });

  it("shows a clean error banner when the eval endpoint returns 503", async () => {
    server.use(
      http.post(`${API_BASE}/evaluation/e2e`, () => HttpResponse.json({ detail: "Vector store not ready" }, { status: 503 })),
    );
    renderWithProviders(<DashboardPage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /run end-to-end eval/i }));

    await waitFor(() => expect(screen.getByText(/corpus not ready/i)).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /ingest the guidelines/i })).toBeInTheDocument();
  });

  it("runs the retrieval matrix independently and renders the comparison table", async () => {
    renderWithProviders(<DashboardPage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /run retrieval eval/i }));

    await waitFor(() => expect(screen.getByRole("heading", { name: /retriever comparison/i })).toBeInTheDocument());
    expect(screen.getByText("hybrid_rerank")).toBeInTheDocument();
  });
});
