import { useState } from "react";
import QueryForm from "@/components/ask/QueryForm";
import EvidencePanel from "@/components/ask/EvidencePanel";
import ErrorBanner from "@/components/common/ErrorBanner";
import EmptyState from "@/components/common/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { useSearchMutation } from "@/hooks/useSearchMutation";
import type { RetrievalMode } from "@/types/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<RetrievalMode>("hybrid_rerank");
  const [k, setK] = useState(5);
  const search = useSearchMutation();

  return (
    <section className="max-w-5xl py-10">
      <div className="tiny mb-3 text-muted-foreground">Retrieval lab / no generation</div>
      <h1 className="font-heading text-5xl font-semibold tracking-tight">See what the retriever sees.</h1>
      <p className="mb-7 mt-3 text-muted-foreground">
        Same question, same corpus. Change the strategy and watch the evidence ranking move. No answer generation, no
        safety verdict.
      </p>

      <QueryForm
        query={query}
        onQueryChange={setQuery}
        mode={mode}
        onModeChange={setMode}
        k={k}
        onKChange={setK}
        isPending={search.isPending}
        submitLabel="Search"
        onSubmit={() => search.mutate({ query, mode, k })}
      />

      <div className="mt-7">
        {search.isPending ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full rounded-2xl" />
            <Skeleton className="h-16 w-full rounded-2xl" />
            <Skeleton className="h-16 w-full rounded-2xl" />
          </div>
        ) : null}

        {search.isError ? <ErrorBanner error={search.error} /> : null}

        {search.data && !search.isPending ? <EvidencePanel retrieval={search.data} /> : null}

        {!search.data && !search.isPending && !search.isError ? (
          <EmptyState
            title="Run a search to compare modes"
            description="semantic and hybrid_rerank scores are roughly 0–1; bm25 is unbounded; hybrid's score is rank-based and not a real relevance signal."
          />
        ) : null}
      </div>
    </section>
  );
}
