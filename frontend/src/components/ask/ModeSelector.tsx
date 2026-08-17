import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import type { RetrievalMode } from "@/types/api";

const MODES: { value: RetrievalMode; label: string }[] = [
  { value: "hybrid_rerank", label: "Hybrid + Rerank (default)" },
  { value: "hybrid", label: "Hybrid" },
  { value: "semantic", label: "Semantic" },
  { value: "bm25", label: "BM25" },
];

interface ModeSelectorProps {
  mode: RetrievalMode;
  onModeChange: (mode: RetrievalMode) => void;
  k: number;
  onKChange: (k: number) => void;
}

export default function ModeSelector({ mode, onModeChange, k, onKChange }: ModeSelectorProps) {
  return (
    <div className="flex flex-wrap items-end gap-4">
      <div className="space-y-1.5">
        <Label htmlFor="mode-select" className="text-xs text-muted-foreground">
          Retrieval mode
        </Label>
        <Select value={mode} onValueChange={(v) => onModeChange(v as RetrievalMode)}>
          <SelectTrigger id="mode-select" className="w-56">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {MODES.map((m) => (
              <SelectItem key={m.value} value={m.value}>
                {m.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="w-40 space-y-1.5">
        <Label htmlFor="k-slider" className="text-xs text-muted-foreground">
          Top-k: {k}
        </Label>
        <Slider id="k-slider" min={1} max={10} step={1} value={[k]} onValueChange={([v]) => onKChange(v)} />
      </div>
    </div>
  );
}
