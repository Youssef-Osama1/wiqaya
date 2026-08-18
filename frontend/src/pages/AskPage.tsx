import { useEffect, useRef, useState } from "react";
import { NavLink, Route, Routes, useNavigate, useSearchParams } from "react-router-dom";
import { BookMarked, FileText, GitBranch, Layers, Quote, ShieldCheck } from "lucide-react";
import QueryForm from "@/components/ask/QueryForm";
import GateBanner from "@/components/ask/GateBanner";
import EvidencePanel from "@/components/ask/EvidencePanel";
import RecommendationCard from "@/components/ask/RecommendationCard";
import SupportingEvidenceCard from "@/components/ask/SupportingEvidenceCard";
import CitationsCard from "@/components/ask/CitationsCard";
import ConfidenceSafetyCard from "@/components/ask/ConfidenceSafetyCard";
import TraceDetails from "@/components/ask/TraceDetails";
import ErrorBanner from "@/components/common/ErrorBanner";
import EmptyState from "@/components/common/EmptyState";
import NotFoundPage from "@/pages/NotFoundPage";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useAnswerMutation } from "@/hooks/useAnswerMutation";
import type { RetrievalMode } from "@/types/api";

const RESULT_TABS = [
  { to: "/recommendation", label: "Recommendation", icon: FileText },
  { to: "/evidence", label: "Evidence", icon: Quote },
  { to: "/citations", label: "Citations", icon: BookMarked },
  { to: "/confidence", label: "Confidence", icon: ShieldCheck },
  { to: "/chunks", label: "Retrieved Chunks", icon: Layers },
] as const;

function AskResultTabs({ showResultTabs }: { showResultTabs: boolean }) {
  const tabClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
      isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
    );

  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-border pb-2" aria-label="Answer sections">
      {showResultTabs
        ? RESULT_TABS.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={tabClass}>
              <Icon className="size-3.5" aria-hidden="true" />
              {label}
            </NavLink>
          ))
        : null}
      <NavLink to="/trace" className={tabClass}>
        <GitBranch className="size-3.5" aria-hidden="true" />
        Trace
      </NavLink>
    </nav>
  );
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
    navigate(trace.gate.verdict === "REFUSE" ? "/trace" : "/recommendation");
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
      {showResults && trace ? <AskResultTabs showResultTabs={trace.gate.verdict !== "REFUSE"} /> : null}

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
        {showResults && trace && trace.gate.verdict !== "REFUSE" ? (
          <>
            <Route
              path="recommendation"
              element={<RecommendationCard recommendation={trace.final.recommendation} threshold={trace.threshold} />}
            />
            <Route path="evidence" element={<SupportingEvidenceCard evidence={trace.final.evidence} />} />
            <Route path="citations" element={<CitationsCard citations={trace.final.citations} />} />
            <Route
              path="confidence"
              element={<ConfidenceSafetyCard confidence={trace.final.confidence} disclaimer={trace.final.disclaimer} audit={trace.audit} />}
            />
            <Route path="chunks" element={trace.retrieval ? <EvidencePanel retrieval={trace.retrieval} /> : null} />
          </>
        ) : null}
        <Route path="trace" element={showResults && trace ? <TraceDetails trace={trace} /> : null} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
