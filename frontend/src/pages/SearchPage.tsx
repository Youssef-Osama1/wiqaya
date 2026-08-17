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
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-6">
      <p className="text-sm text-muted-foreground">
        Retrieval only — no generation, no guardrails. Compare how the 4 retrieval modes rank evidence for the same
        question.
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

      {search.isPending ? (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
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
  );
}
