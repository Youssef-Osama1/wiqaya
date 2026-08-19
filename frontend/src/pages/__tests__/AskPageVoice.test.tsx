import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderWithProviders } from "@/test/test-utils";
import { server } from "@/test/mocks/server";
import { ALLOW_HIGH_TRACE } from "@/test/mocks/handlers";
import AskPage from "@/pages/AskPage";

const API_BASE = "http://localhost:8000/api/v1";

let activeRecognition: FakeRecognition | null = null;

function registerRecognition(recognition: FakeRecognition) {
  activeRecognition = recognition;
}

class FakeRecognition {
  lang = "";
  continuous = false;
  interimResults = false;
  maxAlternatives = 1;
  onresult: ((ev: SpeechRecognitionEvent) => unknown) | null = null;
  onerror: ((ev: SpeechRecognitionErrorEvent) => unknown) | null = null;
  onend: ((ev: Event) => unknown) | null = null;
  onstart: ((ev: Event) => unknown) | null = null;
  onaudioend: ((ev: Event) => unknown) | null = null;
  start = vi.fn();
  stop = vi.fn();
  abort = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn(() => true);

  constructor() {
    registerRecognition(this);
  }

  emitTranscript(transcript: string) {
    const event = {
      resultIndex: 0,
      results: [[{ transcript, confidence: 1 }]],
    } as unknown as SpeechRecognitionEvent;
    this.onresult?.(event);
  }
}

function installRecognition() {
  window.SpeechRecognition = FakeRecognition as unknown as SpeechRecognitionConstructor;
}

function installSynthesis() {
  const speak = vi.fn();
  Object.defineProperty(window, "speechSynthesis", {
    configurable: true,
    writable: true,
    value: { speak, cancel: vi.fn(), pause: vi.fn(), resume: vi.fn(), getVoices: () => [] },
  });
  Object.defineProperty(window, "SpeechSynthesisUtterance", {
    configurable: true,
    writable: true,
    value: class {
      text: string;
      lang = "";
      onend: (() => void) | null = null;
      onerror: (() => void) | null = null;
      constructor(text: string) {
        this.text = text;
      }
    },
  });
  return speak;
}

afterEach(() => {
  activeRecognition = null;
  delete window.SpeechRecognition;
  Reflect.deleteProperty(window, "speechSynthesis");
  Reflect.deleteProperty(window, "SpeechSynthesisUtterance");
});

describe("AskPage voice input", () => {
  it("hides the mic button when the browser has no speech recognition", () => {
    renderWithProviders(<AskPage />);
    expect(screen.queryByRole("button", { name: /voice input/i })).not.toBeInTheDocument();
  });

  it("puts the spoken transcript into the textarea without submitting it", async () => {
    installRecognition();
    const user = userEvent.setup();
    renderWithProviders(<AskPage />);

    await user.click(screen.getByRole("button", { name: /start voice input/i }));
    activeRecognition!.emitTranscript("What is the target blood pressure for adults?");

    await waitFor(() =>
      expect(screen.getByDisplayValue(/what is the target blood pressure for adults\?/i)).toBeInTheDocument(),
    );

    expect(screen.queryByText(/allowed/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^recommendation$/i })).not.toBeInTheDocument();
  });
});

describe("AskPage spoken answer", () => {
  it("reads the recommendation aloud with markdown stripped", async () => {
    const speak = installSynthesis();
    server.use(
      http.post(`${API_BASE}/nlp/answer`, () =>
        HttpResponse.json({
          ...ALLOW_HIGH_TRACE,
          final: { ...ALLOW_HIGH_TRACE.final, recommendation: "Reduce clinic BP to **150/90 mmHg** for adults." },
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<AskPage />);

    await user.type(screen.getByPlaceholderText(/ask a question/i), "target bp?");
    await user.click(screen.getByRole("button", { name: /^ask$/i }));

    await user.click(await screen.findByRole("button", { name: /read recommendation aloud/i }));

    expect(speak).toHaveBeenCalledTimes(1);
    expect(speak.mock.calls[0][0].text).toBe("Reduce clinic BP to 150/90 mmHg for adults.");
  });
});
