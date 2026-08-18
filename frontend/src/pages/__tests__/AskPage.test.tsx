import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderWithProviders } from "@/test/test-utils";
import { server } from "@/test/mocks/server";
import { ALLOW_HIGH_TRACE, HALT_TRACE, REFUSE_TRACE } from "@/test/mocks/handlers";
import AskPage from "@/pages/AskPage";

const API_BASE = "http://localhost:8000/api/v1";

async function askQuestion(text: string) {
  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText(/ask a question/i), text);
  await user.click(screen.getByRole("button", { name: /ask/i }));
}

describe("AskPage", () => {
  it("renders a High-confidence answer across the Recommendation/Evidence/Citations/Confidence tabs for an ALLOW response", async () => {
    const user = userEvent.setup();
    renderWithProviders(<AskPage />);

    await askQuestion(ALLOW_HIGH_TRACE.query);

    await waitFor(() => expect(screen.getByText(/allowed/i)).toBeInTheDocument());
    await waitFor(() =>
      expect(screen.getAllByText(/reduce clinic blood pressure to below 150\/90 mmhg/i).length).toBeGreaterThan(0),
    );

    await user.click(screen.getByRole("link", { name: /^evidence$/i }));
    expect(screen.getByText(/nice_ng136-p016-beee1ff3/)).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /^citations$/i }));
    expect(screen.getByText("NICE NG136")).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /^confidence$/i }));
    expect(screen.getByText(/^high$/i)).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /retrieved chunks/i }));
    expect(screen.getByText(/evidence panel/i)).toBeInTheDocument();
  });

  it("shows only the refusal reason and hides the result tabs on REFUSE", async () => {
    server.use(http.post(`${API_BASE}/nlp/answer`, () => HttpResponse.json(REFUSE_TRACE)));
    renderWithProviders(<AskPage />);

    await askQuestion(REFUSE_TRACE.query);

    await waitFor(() => expect(screen.getByText(/refused/i)).toBeInTheDocument());
    expect(screen.getByText(REFUSE_TRACE.gate.reason)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^recommendation$/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/evidence panel/i)).not.toBeInTheDocument();
  });

  it("shows the halt callout on the Recommendation tab and the low-scoring chunk under Retrieved Chunks, when the threshold halts", async () => {
    const user = userEvent.setup();
    server.use(http.post(`${API_BASE}/nlp/answer`, () => HttpResponse.json(HALT_TRACE)));
    renderWithProviders(<AskPage />);

    await askQuestion(HALT_TRACE.query);

    await waitFor(() =>
      expect(screen.getByText(/the guidelines do not contain enough relevant information/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/0\.100 · HALT/)).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /retrieved chunks/i }));
    expect(screen.getByText(/evidence panel/i)).toBeInTheDocument();
  });

  it("shows a clean error banner instead of crashing when the API is unreachable", async () => {
    server.use(http.post(`${API_BASE}/nlp/answer`, () => HttpResponse.error()));
    renderWithProviders(<AskPage />);

    await askQuestion("any question");

    await waitFor(() => expect(screen.getByText(/could not reach the wiqaya api/i)).toBeInTheDocument(), { timeout: 3000 });
  });

  it("prefills and auto-submits from a ?q= deep link", async () => {
    server.use(http.post(`${API_BASE}/nlp/answer`, () => HttpResponse.json(ALLOW_HIGH_TRACE)));
    renderWithProviders(<AskPage />, { route: "/?q=What+is+first-line+treatment%3F&mode=hybrid_rerank" });

    await waitFor(() => expect(screen.getByText(/allowed/i)).toBeInTheDocument());
    expect(screen.getByDisplayValue(/what is first-line treatment\?/i)).toBeInTheDocument();
  });
});
