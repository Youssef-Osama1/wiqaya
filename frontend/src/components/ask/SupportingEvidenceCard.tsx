import { Quote } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import EmptyState from "@/components/common/EmptyState";
import type { EvidenceItem } from "@/types/api";

export default function SupportingEvidenceCard({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Quote className="size-4 text-primary" />
          Supporting Evidence
        </CardTitle>
      </CardHeader>
      <CardContent>
        {evidence.length === 0 ? (
          <EmptyState title="No verified supporting quotes" />
        ) : (
          <ul className="space-y-3">
            {evidence.map((item, i) => (
              <li key={`${item.chunk_id}-${i}`} className="border-l-2 border-primary/40 pl-3 text-sm italic text-foreground/85">
                “{item.quote}”
                <div className="mt-0.5 font-mono text-[11px] not-italic text-muted-foreground">— {item.chunk_id}</div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
