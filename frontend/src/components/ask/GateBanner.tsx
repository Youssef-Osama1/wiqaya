import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { gateVisuals } from "@/lib/confidence";
import type { GateDecision } from "@/types/api";

export default function GateBanner({ gate }: { gate: GateDecision }) {
  const visual = gateVisuals[gate.verdict];
  const Icon = visual.icon;

  return (
    <Alert className={visual.badgeClass}>
      <Icon className="size-4" />
      <AlertTitle className="font-heading">
        {visual.label}
        {gate.triggered_by ? <span className="ml-2 font-mono text-xs font-normal opacity-70">via {gate.triggered_by}</span> : null}
      </AlertTitle>
      <AlertDescription className={visual.textClass}>{gate.reason}</AlertDescription>
    </Alert>
  );
}
