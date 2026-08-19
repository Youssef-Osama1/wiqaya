import { useQueryClient } from "@tanstack/react-query";
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
import {
  LATEST_E2E_KEY,
  LATEST_RETRIEVAL_KEY,
  useLatestE2EEval,
  useLatestRetrievalEval,
} from "@/hooks/useLatestEvalReports";
import { formatPercent, formatTimestamp } from "@/lib/format";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const savedE2E = useLatestE2EEval();
  const savedRetrieval = useLatestRetrievalEval();

  const e2e = useE2EEvalMutation();
  const retrieval = useRetrievalEvalMutation();

  // a finished run is the newest saved report, so seed the cache rather than refetching it
  const runE2E = () =>
    e2e.mutate({}, { onSuccess: (report) => queryClient.setQueryData(LATEST_E2E_KEY, report) });
  const runRetrieval = () =>
    retrieval.mutate(undefined, { onSuccess: (report) => queryClient.setQueryData(LATEST_RETRIEVAL_KEY, report) });

  const e2eReport = savedE2E.data;
  const retrievalReport = savedRetrieval.data;
  const anythingLoading = savedE2E.isPending || savedRetrieval.isPending;
  const nothingToShow = !e2eReport && !retrievalReport && !e2e.isPending && !retrieval.isPending && !anythingLoading;

  return (
    <section className="space-y-6 py-10">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="tiny mb-3 text-primary">Evaluation / fixed 25 questions</div>
          <h1 className="font-heading text-5xl font-semibold">Trust, measured.</h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            Results are saved on the server and reloaded automatically, so a run survives restarting the app. Re-run
            only when the corpus or the pipeline changes - an end-to-end run makes a real model call per golden
            question and takes several minutes.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={runRetrieval} disabled={retrieval.isPending}>
            {retrievalReport ? "Re-run retrieval eval" : "Run retrieval eval"}
          </Button>
          <Button onClick={runE2E} disabled={e2e.isPending}>
            {e2eReport ? "Re-run end-to-end eval" : "Run end-to-end eval"}
          </Button>
        </div>
      </div>

      {retrieval.isPending ? (
        <SlowOperationNotice label="Running the retrieval matrix (4 modes × 3 k values × 25 questions)" />
      ) : null}
      {retrieval.isError ? <ErrorBanner error={retrieval.error} /> : null}

      {e2e.isPending ? <SlowOperationNotice label="Running the full e2e evaluation against 25 questions" /> : null}
      {e2e.isError ? <ErrorBanner error={e2e.error} /> : null}

      {e2eReport ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="font-heading text-lg font-semibold">End-to-end evaluation</h2>
            <span className="font-data text-xs text-muted-foreground">
              last run {formatTimestamp(e2eReport.timestamp)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
            <MetricTile label={`Precision@${e2eReport.k}`} value={e2eReport.precision_at_k.toFixed(3)} />
            <MetricTile label={`Recall@${e2eReport.k}`} value={e2eReport.recall_at_k.toFixed(3)} />
            <MetricTile label="MRR" value={e2eReport.mrr.toFixed(3)} />
            <MetricTile
              label="Citation Accuracy"
              value={formatPercent(e2eReport.citation_accuracy)}
              tone={e2eReport.citation_accuracy === 1 ? "good" : "warn"}
            />
            <MetricTile
              label="Unsupported Claims"
              value={formatPercent(e2eReport.unsupported_claim_rate)}
              tone={e2eReport.unsupported_claim_rate === 0 ? "good" : "warn"}
            />
            <MetricTile
              label="Refusal Correctness"
              value={formatPercent(e2eReport.refusal_correctness)}
              tone={e2eReport.refusal_correctness === 1 ? "good" : "warn"}
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="panel rounded-2xl p-5">
              <div className="tiny mb-4 text-muted-foreground">By question category</div>
              <CategoryBreakdown breakdown={e2eReport.category_breakdown} />
            </div>
            <div className="panel rounded-2xl p-5">
              <div className="tiny mb-4 text-muted-foreground">Failed questions</div>
              <FailureList failures={e2eReport.failures} />
            </div>
          </div>
        </div>
      ) : null}

      {retrievalReport ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="font-heading text-lg font-semibold">Retriever comparison</h2>
            <span className="font-data text-xs text-muted-foreground">
              last run {formatTimestamp(retrievalReport.timestamp)}
            </span>
          </div>
          <ModeComparisonTable matrix={retrievalReport.matrix} />
        </div>
      ) : null}

      {nothingToShow ? (
        <EmptyState
          title="No evaluation has been run yet"
          description="Trigger a retrieval or end-to-end evaluation above. The result is saved on the server, so you only need to run it once."
        />
      ) : null}
    </section>
  );
}
