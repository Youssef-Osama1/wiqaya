import { ArrowRight, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const GUARDRAIL_LAYERS = [
  {
    n: "01",
    title: "Input gate",
    detail: "Deterministic rules (emergency symptoms, obvious out-of-domain topics, personal-dosing questions) checked first; anything else falls through to an LLM classifier for ALLOW / CAUTION / REFUSE.",
  },
  {
    n: "02",
    title: "Retrieval confidence threshold",
    detail: "Calibrated from real score distributions, not guessed. Below the halt threshold, the generator is never called at all.",
  },
  {
    n: "03",
    title: "Post-generation claim audit",
    detail: "Tier-1 verifies every cited quote appears verbatim in its source chunk. Tier-2 has an LLM check each claim's support against the retrieved text.",
  },
];

const TECH_STACK: [string, string][] = [
  ["API", "FastAPI + uvicorn"],
  ["Generation", "ChatOpenAI (gpt-4o-mini) / ChatCohere (command-a-03-2025)"],
  ["Embeddings", "OpenAIEmbeddings / CohereEmbeddings"],
  ["Vector DB", "PGVector / QdrantVectorStore (docker-compose)"],
  ["Keyword search", "BM25Retriever (in-process)"],
  ["Hybrid", "EnsembleRetriever (weighted RRF)"],
  ["Reranker", "CohereRerank (rerank-v3.5)"],
  ["Structured output", "llm.with_structured_output(...), provider-agnostic"],
  ["Frontend", "React + Vite + TypeScript, talks to FastAPI over HTTP"],
];

const DEMO_CASES = [
  {
    label: "Case A — direct question, exact citations",
    query: "What is the clinic blood pressure target for people aged 80 and over with hypertension?",
    outcome: "Answer: below 150/90 mmHg. Citations: NICE NG136 p.14, p.16. Confidence: High.",
  },
  {
    label: "Case B — multi-document aggregation",
    query: "What is the target blood pressure for adults with hypertension according to both WHO and NICE?",
    outcome: "Synthesizes WHO's <140/90 mmHg (no comorbidities) with NICE's under-80 vs. 80-and-over distinction, citing both documents. Confidence: High.",
  },
  {
    label: "Case C — threshold-driven refusal",
    query: "What is the recommended target inflation pressure for a compression stocking used to manage blood pressure?",
    outcome: "Retrieval's top score (0.258) falls below the halt threshold (0.45) — the generator is never called. Confidence: Insufficient Evidence.",
  },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-12 p-4 md:p-6">
      <section className="space-y-3">
        <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
          Clinical decision support · WHO + NICE hypertension guidelines
        </p>
        <h1 className="font-heading text-3xl font-bold">"Fluent Answer ≠ Safe Answer."</h1>
        <p className="max-w-2xl text-muted-foreground">
          Every answer is grounded in retrieved guideline text with exact citations — document, section, page, and
          chunk ID. The system refuses when the evidence isn't there. The LLM only summarizes retrieved evidence: it
          never diagnoses, and it never cites anything code didn't verify came from the corpus.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-heading text-xl font-semibold">Three independent guardrail layers</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {GUARDRAIL_LAYERS.map((layer) => (
            <Card key={layer.n}>
              <CardHeader>
                <span className="font-mono text-xs text-primary">{layer.n}</span>
                <CardTitle className="font-heading">{layer.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{layer.detail}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Any one layer can downgrade or halt the answer; none of them can be bypassed by the generator.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-heading text-xl font-semibold">Try the scripted demo cases</h2>
        <div className="grid gap-4">
          {DEMO_CASES.map((demo) => (
            <Card key={demo.label}>
              <CardHeader>
                <CardTitle className="font-heading text-base">{demo.label}</CardTitle>
                <CardDescription className="font-mono text-xs">"{demo.query}"</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-muted-foreground">{demo.outcome}</p>
                <Button asChild size="sm" className="gap-1.5">
                  <Link to={`/?q=${encodeURIComponent(demo.query)}&mode=hybrid_rerank`}>
                    Try this query
                    <ArrowRight className="size-3.5" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-heading text-xl font-semibold">Tech stack</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Area</TableHead>
              <TableHead>Choice</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {TECH_STACK.map(([area, choice]) => (
              <TableRow key={area}>
                <TableCell className="font-medium">{area}</TableCell>
                <TableCell className="text-muted-foreground">{choice}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <section className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-4">
        <Badge variant="outline" className="gap-1.5 border-primary/30 text-primary">
          <ShieldCheck className="size-3.5" /> ALLOW
        </Badge>
        <Badge variant="outline" className="gap-1.5 border-warning/30 text-warning">
          <ShieldAlert className="size-3.5" /> CAUTION
        </Badge>
        <Badge variant="outline" className="gap-1.5 border-destructive/30 text-destructive">
          <ShieldX className="size-3.5" /> REFUSE
        </Badge>
        <p className="text-xs text-muted-foreground">
          Not a medical device. General guideline information only — always consult a qualified healthcare provider.
        </p>
      </section>
    </div>
  );
}
