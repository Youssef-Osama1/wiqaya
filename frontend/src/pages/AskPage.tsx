import { useEffect, useRef, useState } from "react";
import { NavLink, Route, Routes, useNavigate, useSearchParams } from "react-router-dom";
import { ShieldX } from "lucide-react";
import QueryForm from "@/components/ask/QueryForm";
import GateBanner from "@/components/ask/GateBanner";
import EvidencePanel from "@/components/ask/EvidencePanel";
import AnswerPanel from "@/components/ask/AnswerPanel";
import TraceDetails from "@/components/ask/TraceDetails";
import ErrorBanner from "@/components/common/ErrorBanner";
import EmptyState from "@/components/common/EmptyState";
import ThresholdGauge from "@/components/ask/ThresholdGauge";
import NotFoundPage from "@/pages/NotFoundPage";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useAnswerMutation } from "@/hooks/useAnswerMutation";
import type { AnswerTrace, RetrievalMode } from "@/types/api";

function AskTabNav({ trace }: { trace: AnswerTrace }) {
  const showResultTabs = trace.gate.verdict !== "REFUSE";
  const tabClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
      isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
    );

  return (
    <nav className="flex gap-1 border-b border-border pb-2" aria-label="Answer sections">
      {showResultTabs ? (
        <>
          <NavLink to="/evidence" className={tabClass}>
            Evidence
          </NavLink>
          <NavLink to="/answer" className={tabClass}>
            Answer
          </NavLink>
        </>
      ) : null}
      <NavLink to="/trace" className={tabClass}>
        Trace
      </NavLink>
    </nav>
  );
}

function AskEvidenceTab({ trace }: { trace: AnswerTrace }) {
  if (trace.gate.verdict === "REFUSE" || !trace.retrieval) return null;
  return <EvidencePanel retrieval={trace.retrieval} />;
}

function AskAnswerTab({ trace }: { trace: AnswerTrace }) {
  if (trace.gate.verdict === "REFUSE") return null;

  if (trace.threshold?.action === "HALT") {
    return (
      <div className="space-y-6">
        {trace.retrieval?.mode === "hybrid_rerank" ? (
          <ThresholdGauge topScore={trace.threshold.top_score} action={trace.threshold.action} />
        ) : null}
        {trace.retrieval ? <EvidencePanel retrieval={trace.retrieval} /> : null}
        <EmptyState
          icon={ShieldX}
          title="Insufficient evidence — the generator was never called"
          description={`Top retrieval score ${trace.threshold.top_score.toFixed(3)} fell below the confidence threshold. The system refused to guess rather than answer without grounding.`}
        />
      </div>
    );
  }

  return <AnswerPanel final={trace.final} audit={trace.audit} />;
}

export default function AskPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<RetrievalMode>("hybrid_rerank");
  const [k, setK] = useState(5);
  const answer = useAnswerMutation();
  const autoSubmitted = useRef(false);

  useEffect(() => {
    const deepLinkQuery = searchParams.get("q");
    if (deepLinkQuery && !autoSubmitted.current) {
      autoSubmitted.current = true;
      const deepLinkMode = (searchParams.get("mode") as RetrievalMode | null) ?? "hybrid_rerank";
      setQuery(deepLinkQuery);
      setMode(deepLinkMode);
      answer.mutate({ query: deepLinkQuery, mode: deepLinkMode, k });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const trace = answer.data;
  const showResults = Boolean(trace) && !answer.isPending;

  useEffect(() => {
    if (!trace) return;
    navigate(trace.gate.verdict === "REFUSE" ? "/trace" : "/answer");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trace]);

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-6">
      <QueryForm
        query={query}
        onQueryChange={setQuery}
        mode={mode}
        onModeChange={setMode}
        k={k}
        onKChange={setK}
        isPending={answer.isPending}
        onSubmit={() => answer.mutate({ query, mode, k })}
      />

      {answer.isPending ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : null}

      {answer.isError ? <ErrorBanner error={answer.error} /> : null}

      {showResults && trace ? <GateBanner gate={trace.gate} /> : null}
      {showResults && trace ? <AskTabNav trace={trace} /> : null}

      <Routes>
        <Route
          index
          element={
            !trace && !answer.isPending && !answer.isError ? (
              <EmptyState
                title="Ask a question to get started"
                description="Answers are grounded in retrieved guideline text with exact citations — the system refuses when the evidence isn't there."
              />
            ) : null
          }
        />
        <Route path="evidence" element={showResults && trace ? <AskEvidenceTab trace={trace} /> : null} />
        <Route path="answer" element={showResults && trace ? <AskAnswerTab trace={trace} /> : null} />
        <Route path="trace" element={showResults && trace ? <TraceDetails trace={trace} /> : null} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
