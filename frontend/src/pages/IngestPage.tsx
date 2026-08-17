import IngestForm from "@/components/ingest/IngestForm";
import IngestResultTable from "@/components/ingest/IngestResultTable";
import ErrorBanner from "@/components/common/ErrorBanner";
import { Skeleton } from "@/components/ui/skeleton";
import { useIngestMutation } from "@/hooks/useIngestMutation";

export default function IngestPage() {
  const ingest = useIngestMutation();

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
      <p className="text-sm text-muted-foreground">
        Clean → chunk → embed → index the WHO and NICE guidelines into the active vector store. Run this once before
        using Ask, Search, or Dashboard.
      </p>

      <IngestForm onSubmit={(request) => ingest.mutate(request)} isPending={ingest.isPending} />

      {ingest.isPending ? <Skeleton className="h-24 w-full" /> : null}
      {ingest.isError ? <ErrorBanner error={ingest.error} /> : null}
      {ingest.data ? <IngestResultTable results={ingest.data.results} /> : null}
    </div>
  );
}
