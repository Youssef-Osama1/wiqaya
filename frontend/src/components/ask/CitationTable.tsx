import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import EmptyState from "@/components/common/EmptyState";
import type { Citation } from "@/types/api";

export default function CitationTable({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return <EmptyState title="No verified citations" description="No cited quote passed verbatim verification." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Document</TableHead>
          <TableHead>Section</TableHead>
          <TableHead>Page</TableHead>
          <TableHead>Chunk ID</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {citations.map((c) => (
          <TableRow key={c.chunk_id}>
            <TableCell className="font-medium">{c.document_name}</TableCell>
            <TableCell className="text-muted-foreground">{c.section_title}</TableCell>
            <TableCell>p.{c.page_number}</TableCell>
            <TableCell className="font-mono text-xs">{c.chunk_id}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
