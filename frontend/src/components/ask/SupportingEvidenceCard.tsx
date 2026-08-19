import EmptyState from "@/components/common/EmptyState";
import type { EvidenceItem } from "@/types/api";

export default function SupportingEvidenceCard({ evidence }: { evidence: EvidenceItem[] }) {
  if (evidence.length === 0) {
    return <EmptyState title="No verified supporting quotes" />;
  }

  return (
    <div className="space-y-3">
      {evidence.map((item, i) => (
        <blockquote key={`${item.chunk_id}-${i}`} className="panel rounded-2xl border-l-2 border-l-primary p-5">
          <p className="text-lg leading-7">“{item.quote}”</p>
          <div className="mt-4 font-data text-[10px] text-muted-foreground">{item.chunk_id}</div>
        </blockquote>
      ))}
    </div>
  );
}
