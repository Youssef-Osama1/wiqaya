import ReactMarkdown from "react-markdown";
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
    <div className="max-w-4xl">
      <div className="mb-3 flex items-center gap-2">
        <span className="tiny text-muted-foreground">Recommendation</span>
        <SpeakButton text={recommendation} />
      </div>

      {threshold?.action === "HALT" ? (
        <div className="panel mb-6 rounded-2xl p-5">
          <ThresholdGauge topScore={threshold.top_score} action={threshold.action} />
        </div>
      ) : null}

      <div className="prose max-w-none font-heading text-2xl leading-snug prose-p:font-heading prose-strong:text-primary md:text-3xl">
        <ReactMarkdown>{recommendation}</ReactMarkdown>
      </div>
    </div>
  );
}
