import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricTileProps {
  label: string;
  value: string;
  emphasis?: boolean;
}

export default function MetricTile({ label, value, emphasis }: MetricTileProps) {
  return (
    <Card className="gap-2 py-4">
      <CardHeader className="px-4">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      </CardHeader>
      <CardContent className="px-4">
        <p className={cn("font-data text-2xl font-semibold", emphasis && "text-primary")}>{value}</p>
      </CardContent>
    </Card>
  );
}
