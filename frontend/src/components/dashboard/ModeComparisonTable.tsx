import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { RetrievalMatrixRow } from "@/types/api";

export default function ModeComparisonTable({ matrix }: { matrix: RetrievalMatrixRow[] }) {
  return (
    <div className="panel overflow-hidden rounded-2xl">
      <Table>
        <TableHeader>
          <TableRow className="bg-popover">
            <TableHead className="tiny">Mode</TableHead>
            <TableHead className="tiny">k</TableHead>
            <TableHead className="tiny">Precision@k</TableHead>
            <TableHead className="tiny">Recall@k</TableHead>
            <TableHead className="tiny">MRR</TableHead>
            <TableHead className="tiny">n</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {matrix.map((row) => (
            <TableRow key={`${row.mode}-${row.k}`}>
              <TableCell className="font-data text-primary">{row.mode}</TableCell>
              <TableCell className="font-data">{row.k}</TableCell>
              <TableCell className="font-data">{row.precision_at_k.toFixed(3)}</TableCell>
              <TableCell className="font-data">{row.recall_at_k.toFixed(3)}</TableCell>
              <TableCell className="font-data">{row.mrr.toFixed(3)}</TableCell>
              <TableCell className="font-data text-muted-foreground">{row.n_questions_scored}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
