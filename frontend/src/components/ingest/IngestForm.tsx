import { useState } from "react";
import { ChevronDown, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { IngestRequest } from "@/api/data";

const DOC_OPTIONS = [
  { key: "who_hypertension", label: "WHO Guideline for the Pharmacological Treatment of Hypertension in Adults" },
  { key: "nice_ng136", label: "NICE NG136: Hypertension in Adults — Diagnosis and Management" },
];

interface IngestFormProps {
  onSubmit: (request: IngestRequest) => void;
  isPending: boolean;
}

export default function IngestForm({ onSubmit, isPending }: IngestFormProps) {
  const [selectedDocs, setSelectedDocs] = useState<string[]>(DOC_OPTIONS.map((d) => d.key));
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [targetTokens, setTargetTokens] = useState("");
  const [hardMaxTokens, setHardMaxTokens] = useState("");
  const [minTokens, setMinTokens] = useState("");
  const [overlapTokens, setOverlapTokens] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const toggleDoc = (key: string) => {
    setSelectedDocs((prev) => (prev.includes(key) ? prev.filter((d) => d !== key) : [...prev, key]));
  };

  const handleConfirm = () => {
    setDialogOpen(false);
    const request: IngestRequest = { doc_keys: selectedDocs };
    if (targetTokens) request.target_tokens = Number(targetTokens);
    if (hardMaxTokens) request.hard_max_tokens = Number(hardMaxTokens);
    if (minTokens) request.min_tokens = Number(minTokens);
    if (overlapTokens) request.overlap_tokens = Number(overlapTokens);
    onSubmit(request);
  };

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-4">
      <div className="space-y-2">
        <p className="text-sm font-medium">Guidelines to ingest</p>
        {DOC_OPTIONS.map((doc) => (
          <label key={doc.key} className="flex items-center gap-2 text-sm">
            <Checkbox checked={selectedDocs.includes(doc.key)} onCheckedChange={() => toggleDoc(doc.key)} />
            {doc.label}
            <span className="font-mono text-xs text-muted-foreground">({doc.key})</span>
          </label>
        ))}
      </div>

      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="gap-1 px-0 text-muted-foreground">
            <ChevronDown className={`size-3.5 transition-transform ${advancedOpen ? "rotate-180" : ""}`} />
            Advanced chunking overrides
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="grid grid-cols-2 gap-3 pt-2 sm:grid-cols-4">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Target tokens</Label>
            <Input type="number" value={targetTokens} onChange={(e) => setTargetTokens(e.target.value)} placeholder="600" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Hard max tokens</Label>
            <Input type="number" value={hardMaxTokens} onChange={(e) => setHardMaxTokens(e.target.value)} placeholder="800" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Min tokens</Label>
            <Input type="number" value={minTokens} onChange={(e) => setMinTokens(e.target.value)} placeholder="120" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Overlap tokens</Label>
            <Input type="number" value={overlapTokens} onChange={(e) => setOverlapTokens(e.target.value)} placeholder="80" />
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <Button disabled={isPending || selectedDocs.length === 0} className="gap-2">
            <UploadCloud className="size-4" />
            {isPending ? "Ingesting…" : "Ingest"}
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Re-ingest {selectedDocs.length} guideline{selectedDocs.length === 1 ? "" : "s"}?</DialogTitle>
            <DialogDescription>
              This re-cleans, re-chunks, and re-embeds the selected guideline(s) and replaces their chunks in the
              vector store. Other documents already indexed are left untouched.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleConfirm}>Confirm ingest</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
