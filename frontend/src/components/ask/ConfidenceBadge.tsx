import { Badge } from "@/components/ui/badge";
import { confidenceVisuals } from "@/lib/confidence";
import type { Confidence } from "@/types/api";

export default function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  const visual = confidenceVisuals[confidence];
  const Icon = visual.icon;

  return (
    <Badge variant="outline" className={`gap-1.5 px-2.5 py-1 font-mono text-xs ${visual.badgeClass}`}>
      <Icon className="size-3.5" />
      {visual.label}
    </Badge>
  );
}
