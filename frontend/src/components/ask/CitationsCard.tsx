import { BookMarked } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import CitationTable from "@/components/ask/CitationTable";
import type { Citation } from "@/types/api";

export default function CitationsCard({ citations }: { citations: Citation[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookMarked className="size-4 text-primary" />
          Citations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <CitationTable citations={citations} />
      </CardContent>
    </Card>
  );
}
