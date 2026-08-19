import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ModeSelector from "@/components/ask/ModeSelector";
import MicButton from "@/components/ask/MicButton";
import type { RetrievalMode } from "@/types/api";

interface QueryFormProps {
  query: string;
  onQueryChange: (query: string) => void;
  mode: RetrievalMode;
  onModeChange: (mode: RetrievalMode) => void;
  k: number;
  onKChange: (k: number) => void;
  onSubmit: () => void;
  isPending: boolean;
  submitLabel?: string;
}

export default function QueryForm({
  query,
  onQueryChange,
  mode,
  onModeChange,
  k,
  onKChange,
  onSubmit,
  isPending,
  submitLabel = "Ask",
}: QueryFormProps) {
  return (
    <form
      className="space-y-4 rounded-lg border border-border bg-card p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (query.trim()) onSubmit();
      }}
    >
      <Textarea
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="Ask a question about hypertension diagnosis or treatment…"
        rows={3}
        className="resize-none"
      />
      <div className="flex flex-wrap items-end justify-between gap-4">
        <ModeSelector mode={mode} onModeChange={onModeChange} k={k} onKChange={onKChange} />
        <div className="flex items-center gap-2">
          <MicButton onTranscript={onQueryChange} disabled={isPending} />
          <Button type="submit" disabled={isPending || !query.trim()} className="gap-2">
            <Search className="size-4" />
            {isPending ? "Working…" : submitLabel}
          </Button>
        </div>
      </div>
    </form>
  );
}
