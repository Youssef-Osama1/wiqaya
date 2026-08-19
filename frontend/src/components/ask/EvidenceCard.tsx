import { GitBranch } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { formatScore, pageRange, sectionBreadcrumb } from "@/lib/format";
import type { ScoredChunk } from "@/types/api";

export default function EvidenceCard({ scored, rank }: { scored: ScoredChunk; rank: number }) {
  const { chunk, score, source } = scored;
  const meta = chunk.metadata;
  const display = formatScore(score, source);

  return (
    <AccordionItem value={meta.chunk_id} className="panel rounded-2xl border px-4">
      <AccordionTrigger className="hover:no-underline">
        <div className="flex w-full flex-wrap items-center gap-x-4 gap-y-1 pr-2 text-left">
          <span className="w-5 font-data text-primary">#{rank}</span>
          <span className="grow font-semibold">{meta.document_name}</span>
          <span className="font-data text-xs text-muted-foreground">{pageRange(meta)}</span>
          {source === "hybrid" ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="font-data text-xs text-muted-foreground underline decoration-dotted">
                  {display.label}
                </span>
              </TooltipTrigger>
              <TooltipContent>Hybrid mode's score is rank-based, not a real relevance signal.</TooltipContent>
            </Tooltip>
          ) : (
            <span className="font-data text-xs text-primary">{display.label}</span>
          )}
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-3 border-t border-border pt-4">
        {display.showBar ? (
          <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
            <span className="block h-full rounded-full bg-primary" style={{ width: `${display.barValue}%` }} />
          </div>
        ) : null}

        <p className="max-w-[78ch] leading-7 text-foreground/80">{chunk.text}</p>

        <div className="flex flex-wrap items-center gap-2 font-data text-[10px] text-muted-foreground">
          <span>{sectionBreadcrumb(meta)}</span>
          <Badge variant="secondary" className="font-data">
            {meta.chunk_id}
          </Badge>
          {meta.has_cross_reference ? (
            <Badge variant="outline" className="gap-1 border-warning/40 text-warning">
              <GitBranch className="size-3" />
              cross-reference
            </Badge>
          ) : null}
          {meta.recommendation_ids.length > 0 ? (
            <Badge variant="outline" className="font-data">
              {meta.recommendation_ids.join(", ")}
            </Badge>
          ) : null}
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
