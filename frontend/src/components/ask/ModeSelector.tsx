import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { RetrievalMode } from "@/types/api";

const MODES: { value: RetrievalMode; label: string }[] = [
  { value: "hybrid_rerank", label: "Hybrid + Rerank" },
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
    <>
      <div>
        <label htmlFor="mode-select" className="tiny mb-2 block text-muted-foreground">
          Retrieval
        </label>
        <Select value={mode} onValueChange={(v) => onModeChange(v as RetrievalMode)}>
          <SelectTrigger id="mode-select" className="h-auto w-48 rounded-xl px-4 py-3">
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

      <div className="w-24">
        <label htmlFor="passages" className="tiny mb-2 block text-muted-foreground">
          Passages
        </label>
        <Input
          id="passages"
          type="number"
          min={1}
          max={10}
          value={k}
          onChange={(e) => onKChange(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
          className="h-auto rounded-xl px-4 py-3"
        />
      </div>
    </>
  );
}
