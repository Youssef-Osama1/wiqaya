import { Accordion } from "@/components/ui/accordion";
import EvidenceCard from "@/components/ask/EvidenceCard";
import EmptyState from "@/components/common/EmptyState";
import type { RetrievalResult } from "@/types/api";

export default function EvidencePanel({ retrieval }: { retrieval: RetrievalResult }) {
  const { results, mode } = retrieval;

  if (results.length === 0) {
    return <EmptyState title="No matching evidence" description="Try a different question or retrieval mode." />;
  }

  const defaultOpen = results.slice(0, 2).map((r) => r.chunk.metadata.chunk_id);

  return (
    <div className="space-y-2">
      <h2 className="font-heading text-sm font-semibold text-muted-foreground">
        Evidence Panel — {results.length} chunk{results.length === 1 ? "" : "s"}, mode: <span className="font-mono">{mode}</span>
      </h2>
      <Accordion type="multiple" defaultValue={defaultOpen} className="space-y-2">
        {results.map((scored, i) => (
          <EvidenceCard key={scored.chunk.metadata.chunk_id} scored={scored} rank={i + 1} />
        ))}
      </Accordion>
    </div>
  );
}
