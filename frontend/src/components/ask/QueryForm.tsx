import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
      className="panel flex flex-wrap items-end gap-3 rounded-2xl p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (query.trim()) onSubmit();
      }}
    >
      <div className="min-w-[280px] grow">
        <label htmlFor="clinical-question" className="tiny mb-2 block text-muted-foreground">
          Clinical question
        </label>
        <Input
          id="clinical-question"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Ask a question about hypertension diagnosis or treatment…"
          className="h-auto rounded-xl px-4 py-3 text-base"
        />
      </div>

      <ModeSelector mode={mode} onModeChange={onModeChange} k={k} onKChange={onKChange} />

      <div className="flex items-center gap-2">
        <MicButton onTranscript={onQueryChange} disabled={isPending} />
        <Button
          type="submit"
          disabled={isPending || !query.trim()}
          className="h-auto rounded-xl px-5 py-3 font-bold"
        >
          {isPending ? "Working…" : submitLabel}
          {isPending ? null : <span aria-hidden="true">→</span>}
        </Button>
      </div>
    </form>
  );
}
