import { GitBranch } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { docStripeClass, formatScore, pageRange, sectionBreadcrumb } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ScoredChunk } from "@/types/api";

export default function EvidenceCard({ scored, rank }: { scored: ScoredChunk; rank: number }) {
  const { chunk, score, source } = scored;
  const meta = chunk.metadata;
  const display = formatScore(score, source);

  return (
    <AccordionItem
      value={meta.chunk_id}
      className={cn("rounded-md border border-l-4 bg-card px-4", docStripeClass(meta.doc_key))}
    >
      <AccordionTrigger className="hover:no-underline">
        <div className="flex w-full flex-wrap items-center gap-x-3 gap-y-1 pr-2 text-left">
          <span className="font-mono text-xs text-muted-foreground">#{rank}</span>
          <span className="font-medium">{meta.document_name}</span>
          <span className="text-sm text-muted-foreground">{pageRange(meta)}</span>
          {source === "hybrid" ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="font-mono text-xs text-muted-foreground underline decoration-dotted">
                  score {display.label}
                </span>
              </TooltipTrigger>
              <TooltipContent>Hybrid mode's score is rank-based, not a real relevance signal.</TooltipContent>
            </Tooltip>
          ) : (
            <span className="font-mono text-xs text-muted-foreground">score {display.label}</span>
          )}
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-3">
        {display.showBar ? <Progress value={display.barValue} className="h-1.5" /> : null}

        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span>{sectionBreadcrumb(meta)}</span>
          <Badge variant="secondary" className="font-mono">
            {meta.chunk_id}
          </Badge>
          {meta.has_cross_reference ? (
            <Badge variant="outline" className="gap-1 border-warning/40 text-warning">
              <GitBranch className="size-3" />
              cross-reference
            </Badge>
          ) : null}
          {meta.recommendation_ids.length > 0 ? (
            <Badge variant="outline" className="font-mono">
              {meta.recommendation_ids.join(", ")}
            </Badge>
          ) : null}
        </div>

        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">{chunk.text}</p>
      </AccordionContent>
    </AccordionItem>
  );
}
