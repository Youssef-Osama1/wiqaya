import { Link } from "react-router-dom";
import { gateVisuals } from "@/lib/confidence";

const GUARDRAIL_LAYERS = [
  {
    n: "01",
    title: "INPUT SAFETY",
    detail:
      "Deterministic rules (emergency symptoms, out-of-domain topics, personal-dosing questions) run first; anything else falls through to a classifier for ALLOW / CAUTION / REFUSE.",
  },
  {
    n: "02",
    title: "RETRIEVAL CONFIDENCE",
    detail:
      "Two thresholds, calibrated from real score distributions rather than guessed, separate refusal from a cautious answer and from a normal grounded answer.",
  },
  {
    n: "03",
    title: "FACT AUDIT",
    detail:
      "Tier-1 verifies every cited quote appears verbatim in its source chunk. Tier-2 has the model check each claim's support against the retrieved text.",
  },
];

const TECH_STACK = [
  "React + Vite + TypeScript",
  "Tailwind CSS",
  "FastAPI / HTTP",
  "PGVector / Qdrant + BM25 hybrid",
  "Cohere generation, embeddings, rerank",
  "WHO + NICE guideline corpus",
];

const DEMO_CASES = [
  {
    query: "What is the clinic blood pressure target for people aged 80 and over with hypertension?",
    verdict: "ALLOW" as const,
  },
  {
    query: "What dose of amlodipine should I take for my blood pressure?",
    verdict: "CAUTION" as const,
  },
  {
    query: "What is the recommended first-line treatment for type 2 diabetes?",
    verdict: "REFUSE" as const,
  },
];

export default function AboutPage() {
  return (
    <section className="py-10">
      <div className="grid items-start gap-10 lg:grid-cols-[1.25fr_.75fr]">
        <div>
          <div className="tiny mb-4 text-primary">Wiqaya / hackathon thesis</div>
          <h1 className="font-heading text-6xl font-semibold leading-[.88] tracking-[-.06em] md:text-8xl">
            Fluent answer
            <br />
            <span className="text-muted-foreground">≠ safe answer.</span>
          </h1>
          <p className="mt-8 max-w-2xl text-xl leading-8 text-foreground/70">
            Wiqaya is a clinical decision-support RAG system designed around one uncomfortable rule: if the evidence
            cannot carry the claim, the system should not say it.
          </p>

          <div className="mt-10 grid gap-3 md:grid-cols-3">
            {GUARDRAIL_LAYERS.map((layer) => (
              <div key={layer.n} className="panel rounded-2xl p-5">
                <div className="font-data text-primary">{layer.n}</div>
                <div className="mt-5 font-bold">{layer.title}</div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{layer.detail}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel rounded-3xl p-6">
          <div className="tiny mb-5 text-muted-foreground">Try these / one click</div>
          {DEMO_CASES.map((demo) => {
            const visual = gateVisuals[demo.verdict];
            return (
              <Link
                key={demo.query}
                to={`/?q=${encodeURIComponent(demo.query)}&mode=hybrid_rerank`}
                className="mb-2 block rounded-xl border border-input p-4 transition-colors hover:bg-accent"
              >
                <div className="font-semibold">{demo.query}</div>
                <div className={`tiny mt-2 ${visual.textClass}`}>{visual.label}</div>
              </Link>
            );
          })}

          <div className="tiny mb-3 mt-7 text-muted-foreground">Stack</div>
          <div className="font-data text-xs leading-7 text-muted-foreground">
            {TECH_STACK.map((item) => (
              <div key={item}>{item}</div>
            ))}
          </div>

          <div className="tiny mb-3 mt-7 text-muted-foreground">Verdicts</div>
          <div className="flex flex-wrap gap-2">
            {(["ALLOW", "CAUTION", "REFUSE"] as const).map((verdict) => (
              <span key={verdict} className={`tiny rounded-full border px-3 py-1 ${gateVisuals[verdict].badgeClass}`}>
                {gateVisuals[verdict].label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <p className="mt-10 border-t border-border pt-5 text-xs text-muted-foreground">
        Medical disclaimer: Wiqaya is a prototype clinical decision-support system. It does not replace professional
        medical judgment, local protocols, or the current full guideline.
      </p>
    </section>
  );
}
