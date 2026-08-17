import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import EmptyState from "@/components/common/EmptyState";
import type { EvalFailure } from "@/types/api";

export default function FailureList({ failures }: { failures: EvalFailure[] }) {
  if (failures.length === 0) {
    return <EmptyState title="No failures in this run" description="Every question's actual behavior matched its expected behavior." />;
  }

  return (
    <Accordion type="multiple" className="space-y-2">
      {failures.map((f) => (
        <AccordionItem key={f.qid} value={f.qid} className="rounded-md border border-destructive/30 px-4">
          <AccordionTrigger className="hover:no-underline">
            <span className="text-left text-sm">
              <span className="font-mono text-destructive">{f.qid}</span> ({f.category}) — expected {f.expected_behavior}, got{" "}
              {f.actual_confidence ?? "error"}
            </span>
          </AccordionTrigger>
          <AccordionContent className="space-y-2 text-sm">
            <p>{f.question}</p>
            {f.error ? (
              <p className="font-mono text-xs text-destructive">error: {f.error}</p>
            ) : (
              <>
                <p className="text-xs text-muted-foreground">
                  gate: <span className="font-mono">{f.actual_gate_verdict}</span> · confidence:{" "}
                  <span className="font-mono">{f.actual_confidence}</span>
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">Relevant chunk_ids</p>
                    <p className="font-mono text-xs">{f.relevant_chunk_ids.join(", ") || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">Retrieved chunk_ids</p>
                    <p className="font-mono text-xs">{f.retrieved_chunk_ids.join(", ") || "—"}</p>
                  </div>
                </div>
              </>
            )}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
