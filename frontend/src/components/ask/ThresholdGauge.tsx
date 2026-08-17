import { cn } from "@/lib/utils";
import type { ThresholdDecision } from "@/types/api";

const HALT_THRESHOLD = 0.45;
const DOWNGRADE_THRESHOLD = 0.65;

const pct = (v: number) => `${Math.min(Math.max(v, 0), 1) * 100}%`;

export default function ThresholdGauge({ topScore, action }: { topScore: number; action: ThresholdDecision["action"] }) {
  const zoneClass: Record<ThresholdDecision["action"], string> = {
    HALT: "text-destructive",
    DOWNGRADE: "text-warning",
    PROCEED: "text-success",
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between font-data text-xs">
        <span className="text-muted-foreground">retrieval confidence reading</span>
        <span className={cn("font-semibold", zoneClass[action])}>
          {topScore.toFixed(3)} · {action}
        </span>
      </div>
      <div className="relative h-2.5 rounded-full border border-border" aria-hidden="true">
        <div className="absolute inset-y-0 left-0 rounded-l-full bg-destructive/20" style={{ width: pct(HALT_THRESHOLD) }} />
        <div
          className="absolute inset-y-0 bg-warning/20"
          style={{ left: pct(HALT_THRESHOLD), width: pct(DOWNGRADE_THRESHOLD - HALT_THRESHOLD) }}
        />
        <div
          className="absolute inset-y-0 right-0 rounded-r-full bg-success/20"
          style={{ left: pct(DOWNGRADE_THRESHOLD) }}
        />
        <div className="absolute inset-y-0 w-px bg-foreground/30" style={{ left: pct(HALT_THRESHOLD) }} />
        <div className="absolute inset-y-0 w-px bg-foreground/30" style={{ left: pct(DOWNGRADE_THRESHOLD) }} />
        <div
          className="absolute -top-1 -bottom-1 w-[3px] rounded-full bg-foreground"
          style={{ left: `calc(${pct(topScore)} - 1.5px)` }}
        />
      </div>
      <div className="flex justify-between font-data text-[10px] text-muted-foreground">
        <span>halt &lt; {HALT_THRESHOLD.toFixed(2)}</span>
        <span>downgrade &lt; {DOWNGRADE_THRESHOLD.toFixed(2)}</span>
        <span>proceed ≥ {DOWNGRADE_THRESHOLD.toFixed(2)}</span>
      </div>
    </div>
  );
}
