import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import ThresholdGauge from "@/components/ask/ThresholdGauge";
import { formatMs } from "@/lib/format";
import { thresholdVisuals } from "@/lib/confidence";
import type { AnswerTrace } from "@/types/api";

export default function TraceDetails({ trace }: { trace: AnswerTrace }) {
  const timingEntries = Object.entries(trace.timings_ms);

  return (
    <Accordion type="single" collapsible>
      <AccordionItem value="trace" className="rounded-md border border-border px-4">
        <AccordionTrigger className="font-mono text-xs text-muted-foreground hover:no-underline">
          Full trace - timings, threshold, raw model output
        </AccordionTrigger>
        <AccordionContent className="space-y-4 text-sm">
          {timingEntries.length > 0 ? (
            <div>
              <h3 className="mb-1 text-xs font-semibold text-muted-foreground">Timings</h3>
              <div className="flex flex-wrap gap-2">
                {timingEntries.map(([stage, ms]) => (
                  <Badge key={stage} variant="secondary" className="font-mono">
                    {stage}: {formatMs(ms)}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}

          {trace.threshold ? (
            <div>
              <h3 className="mb-1 text-xs font-semibold text-muted-foreground">Retrieval threshold</h3>
              {trace.retrieval?.mode === "hybrid_rerank" ? (
                <ThresholdGauge topScore={trace.threshold.top_score} action={trace.threshold.action} />
              ) : (
                <p className="font-mono text-xs">
                  <span className={thresholdVisuals[trace.threshold.action].textClass}>{trace.threshold.action}</span> - top score{" "}
                  {trace.threshold.top_score.toFixed(3)}
                </p>
              )}
              <p className="mt-1 text-xs text-muted-foreground">{trace.threshold.reason}</p>
            </div>
          ) : null}

          {trace.raw_answer ? (
            <div>
              <h3 className="mb-1 text-xs font-semibold text-muted-foreground">Raw model output (pre-audit)</h3>
              <p className="text-xs text-muted-foreground">insufficient_evidence: {String(trace.raw_answer.insufficient_evidence)}</p>
              {trace.raw_answer.caveats.length > 0 ? (
                <ul className="mt-1 list-disc pl-4 text-xs text-muted-foreground">
                  {trace.raw_answer.caveats.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}

          {trace.audit && trace.audit.claims.length > 0 ? (
            <div>
              <h3 className="mb-1 text-xs font-semibold text-muted-foreground">Tier-2 claim audit</h3>
              <ul className="space-y-1 text-xs">
                {trace.audit.claims.map((claim, i) => (
                  <li key={i} className={claim.supported ? "text-muted-foreground" : "text-destructive"}>
                    {claim.supported ? "✓" : "✗"} {claim.claim}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
