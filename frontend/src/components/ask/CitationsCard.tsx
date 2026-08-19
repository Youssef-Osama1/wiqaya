import CitationTable from "@/components/ask/CitationTable";
import type { Citation } from "@/types/api";

export default function CitationsCard({ citations }: { citations: Citation[] }) {
  return (
    <div className="panel overflow-hidden rounded-2xl">
      <CitationTable citations={citations} />
    </div>
  );
}
