import { gateVisuals } from "@/lib/confidence";
import type { GateDecision } from "@/types/api";

export default function GateBanner({ gate }: { gate: GateDecision }) {
  const visual = gateVisuals[gate.verdict];

  return (
    <div className="panel mb-6 flex flex-wrap items-center justify-between gap-4 rounded-3xl p-5">
      <div className="flex flex-wrap items-center gap-3">
        <span className={`tiny rounded-full border px-3 py-1 ${visual.badgeClass}`}>{visual.label}</span>
        <span className="text-sm text-foreground/70">{gate.reason}</span>
      </div>
      {gate.triggered_by ? (
        <span className="font-data text-xs text-muted-foreground">via {gate.triggered_by}</span>
      ) : null}
    </div>
  );
}
