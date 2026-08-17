import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

export default function SlowOperationNotice({ label }: { label: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-3 rounded-md border border-border bg-muted/50 px-4 py-3 text-sm text-muted-foreground">
      <Loader2 className="size-4 animate-spin text-primary" />
      <span>
        {label} — {elapsed}s elapsed
      </span>
    </div>
  );
}
