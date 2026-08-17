import { Progress } from "@/components/ui/progress";
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
    <div className="space-y-3">
      {(Object.entries(breakdown) as [GoldenCategory, { count: number; correct: number }][]).map(([category, stats]) => (
        <div key={category} className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">{CATEGORY_LABELS[category]}</span>
            <span className="font-mono text-xs text-muted-foreground">
              {stats.correct}/{stats.count}
            </span>
          </div>
          <Progress value={stats.count > 0 ? (stats.correct / stats.count) * 100 : 0} className="h-1.5" />
        </div>
      ))}
    </div>
  );
}
