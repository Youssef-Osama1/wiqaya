import { PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import MetricTile from "@/components/dashboard/MetricTile";
import CategoryBreakdown from "@/components/dashboard/CategoryBreakdown";
import FailureList from "@/components/dashboard/FailureList";
import ModeComparisonTable from "@/components/dashboard/ModeComparisonTable";
import ErrorBanner from "@/components/common/ErrorBanner";
import EmptyState from "@/components/common/EmptyState";
import SlowOperationNotice from "@/components/common/SlowOperationNotice";
import { useE2EEvalMutation } from "@/hooks/useE2EEvalMutation";
import { useRetrievalEvalMutation } from "@/hooks/useRetrievalEvalMutation";
import { formatPercent, formatTimestamp } from "@/lib/format";

export default function DashboardPage() {
  const e2e = useE2EEvalMutation();
  const retrieval = useRetrievalEvalMutation();

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-4 md:p-6">
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-4">
        <p className="flex-1 text-sm text-muted-foreground">
          Runs happen live against the API — nothing is cached from disk. The e2e run makes a real LLM call per
          golden question, so it typically takes a few minutes.
        </p>
        <Button variant="outline" onClick={() => retrieval.mutate()} disabled={retrieval.isPending} className="gap-2">
          <PlayCircle className="size-4" />
          Run retrieval matrix
        </Button>
        <Button onClick={() => e2e.mutate({})} disabled={e2e.isPending} className="gap-2">
          <PlayCircle className="size-4" />
          Run full e2e eval
        </Button>
      </div>

      {retrieval.isPending ? <SlowOperationNotice label="Running the retrieval matrix (4 modes × 3 k values × 25 questions)" /> : null}
      {retrieval.isError ? <ErrorBanner error={retrieval.error} /> : null}

      {e2e.isPending ? <SlowOperationNotice label="Running the full e2e evaluation against 25 questions" /> : null}
      {e2e.isError ? <ErrorBanner error={e2e.error} /> : null}

      {e2e.data ? (
        <section className="space-y-6">
          <div className="flex items-baseline justify-between">
            <h2 className="font-heading text-lg font-semibold">End-to-end evaluation</h2>
            <span className="font-data text-xs text-muted-foreground">{formatTimestamp(e2e.data.timestamp)}</span>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Retrieval quality</p>
            <div className="grid grid-cols-3 gap-3">
              <MetricTile label={`Precision@${e2e.data.k}`} value={e2e.data.precision_at_k.toFixed(3)} />
              <MetricTile label={`Recall@${e2e.data.k}`} value={e2e.data.recall_at_k.toFixed(3)} />
              <MetricTile label="MRR" value={e2e.data.mrr.toFixed(3)} />
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Grounding &amp; citation</p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <MetricTile label="Citation Accuracy" value={formatPercent(e2e.data.citation_accuracy)} emphasis />
              <MetricTile label="Unsupported Claim Rate" value={formatPercent(e2e.data.unsupported_claim_rate)} emphasis />
              <MetricTile label="Refusal Correctness" value={formatPercent(e2e.data.refusal_correctness)} emphasis />
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Evaluation depth</p>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="mb-2 font-heading text-sm font-semibold text-muted-foreground">Per-category breakdown</h3>
                <CategoryBreakdown breakdown={e2e.data.category_breakdown} />
              </div>
              <div>
                <h3 className="mb-2 font-heading text-sm font-semibold text-muted-foreground">Failures</h3>
                <FailureList failures={e2e.data.failures} />
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {retrieval.data ? (
        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Retrieval quality</p>
          <div className="flex items-baseline justify-between">
            <h2 className="font-heading text-lg font-semibold">Retrieval matrix</h2>
            <span className="font-data text-xs text-muted-foreground">{formatTimestamp(retrieval.data.timestamp)}</span>
          </div>
          <ModeComparisonTable matrix={retrieval.data.matrix} />
        </section>
      ) : null}

      {!e2e.data && !retrieval.data && !e2e.isPending && !retrieval.isPending ? (
        <EmptyState
          title="Nothing run yet this session"
          description="Trigger a retrieval matrix or full e2e evaluation above — results aren't persisted across page loads."
        />
      ) : null}
    </div>
  );
}
