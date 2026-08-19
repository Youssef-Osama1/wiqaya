import { cn } from "@/lib/utils";

type MetricTone = "neutral" | "good" | "warn";

interface MetricTileProps {
  label: string;
  value: string;
  tone?: MetricTone;
}

const TONE_CLASSES: Record<MetricTone, string> = {
  neutral: "",
  good: "text-success",
  warn: "text-warning",
};

export default function MetricTile({ label, value, tone = "neutral" }: MetricTileProps) {
  return (
    <div className="panel rounded-2xl p-5">
      <div className="tiny text-muted-foreground">{label}</div>
      <div className={cn("metric mt-2", TONE_CLASSES[tone])}>{value}</div>
    </div>
  );
}
