import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { IngestResult } from "@/types/api";

export default function IngestResultTable({ results }: { results: IngestResult[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Doc key</TableHead>
          <TableHead>Chunks</TableHead>
          <TableHead>Indexed vectors</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {results.map((r) => (
          <TableRow key={r.doc_key}>
            <TableCell className="font-mono">{r.doc_key}</TableCell>
            <TableCell>{r.chunk_count}</TableCell>
            <TableCell className={r.indexed_vector_count === r.chunk_count ? "text-success" : "text-destructive"}>
              {r.indexed_vector_count}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
