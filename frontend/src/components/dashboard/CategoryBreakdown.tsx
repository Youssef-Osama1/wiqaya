import { cn } from "@/lib/utils";
import type { GoldenCategory } from "@/types/api";

const CATEGORY_LABELS: Record<GoldenCategory, string> = {
  direct: "Direct",
  multi_chunk: "Multi-chunk",
  ambiguous: "Ambiguous",
  out_of_scope: "Out of scope",
};

interface CategoryBreakdownProps {
  breakdown: Record<GoldenCategory, { count: number; correct: number }>;
}

export default function CategoryBreakdown({ breakdown }: CategoryBreakdownProps) {
  return (
    <div>
      {(Object.entries(breakdown) as [GoldenCategory, { count: number; correct: number }][]).map(([category, stats]) => {
        const perfect = stats.correct === stats.count;
        return (
          <div key={category} className="flex items-center justify-between border-b border-border py-3">
            <span>{CATEGORY_LABELS[category]}</span>
            <span className={cn("font-data", perfect ? "text-success" : "text-warning")}>
              {stats.correct} / {stats.count}
            </span>
          </div>
        );
      })}
    </div>
  );
}
