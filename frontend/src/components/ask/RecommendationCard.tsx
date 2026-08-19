import { FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ThresholdGauge from "@/components/ask/ThresholdGauge";
import SpeakButton from "@/components/ask/SpeakButton";
import type { ThresholdDecision } from "@/types/api";

export default function RecommendationCard({
  recommendation,
  threshold,
}: {
  recommendation: string;
  threshold: ThresholdDecision | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="size-4 text-primary" />
          Recommendation
          <span className="ml-auto">
            <SpeakButton text={recommendation} />
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {threshold?.action === "HALT" ? <ThresholdGauge topScore={threshold.top_score} action={threshold.action} /> : null}
        <div className="prose prose-sm max-w-none text-foreground prose-headings:font-heading">
          <ReactMarkdown>{recommendation}</ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}
