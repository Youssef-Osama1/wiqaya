import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { RetrievalMatrixRow } from "@/types/api";

export default function ModeComparisonTable({ matrix }: { matrix: RetrievalMatrixRow[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Mode</TableHead>
          <TableHead>k</TableHead>
          <TableHead>Precision@k</TableHead>
          <TableHead>Recall@k</TableHead>
          <TableHead>MRR</TableHead>
          <TableHead>n</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {matrix.map((row) => (
          <TableRow key={`${row.mode}-${row.k}`}>
            <TableCell className="font-mono">{row.mode}</TableCell>
            <TableCell>{row.k}</TableCell>
            <TableCell>{row.precision_at_k.toFixed(3)}</TableCell>
            <TableCell>{row.recall_at_k.toFixed(3)}</TableCell>
            <TableCell>{row.mrr.toFixed(3)}</TableCell>
            <TableCell className="text-muted-foreground">{row.n_questions_scored}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
