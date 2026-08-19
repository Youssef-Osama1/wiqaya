import IngestForm from "@/components/ingest/IngestForm";
import IngestResultTable from "@/components/ingest/IngestResultTable";
import ErrorBanner from "@/components/common/ErrorBanner";
import { Skeleton } from "@/components/ui/skeleton";
import { useIngestMutation } from "@/hooks/useIngestMutation";

export default function IngestPage() {
  const ingest = useIngestMutation();

  return (
    <section className="max-w-5xl py-10">
      <div className="tiny mb-3 text-primary">Data pipeline / re-index</div>
      <h1 className="font-heading text-5xl font-semibold">Rebuild the evidence layer.</h1>
      <p className="mb-8 mt-3 max-w-2xl text-muted-foreground">
        Chunking is a product decision: it changes what the retriever can see. Clean → chunk → embed → index the WHO
        and NICE guidelines into the active vector store. Re-indexing overwrites the current index.
      </p>

      <IngestForm onSubmit={(request) => ingest.mutate(request)} isPending={ingest.isPending} />

      <div className="mt-6 space-y-4">
        {ingest.isPending ? <Skeleton className="h-24 w-full rounded-2xl" /> : null}
        {ingest.isError ? <ErrorBanner error={ingest.error} /> : null}
        {ingest.data ? <IngestResultTable results={ingest.data.results} /> : null}
      </div>
    </section>
  );
}
