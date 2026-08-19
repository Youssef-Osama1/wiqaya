import { useEffect, useRef, useState } from "react";
import { NavLink, Route, Routes, useNavigate, useSearchParams } from "react-router-dom";
import QueryForm from "@/components/ask/QueryForm";
import GateBanner from "@/components/ask/GateBanner";
import EvidencePanel from "@/components/ask/EvidencePanel";
import RecommendationCard from "@/components/ask/RecommendationCard";
import SupportingEvidenceCard from "@/components/ask/SupportingEvidenceCard";
import CitationsCard from "@/components/ask/CitationsCard";
import ConfidenceSafetyCard from "@/components/ask/ConfidenceSafetyCard";
import TraceDetails from "@/components/ask/TraceDetails";
import ErrorBanner from "@/components/common/ErrorBanner";
import NotFoundPage from "@/pages/NotFoundPage";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useAnswerMutation } from "@/hooks/useAnswerMutation";
import type { RetrievalMode } from "@/types/api";

const RESULT_TABS = [
  { to: "/recommendation", label: "01 Recommendation" },
  { to: "/evidence", label: "02 Evidence quotes" },
  { to: "/citations", label: "03 Citations" },
  { to: "/confidence", label: "04 Confidence & audit" },
  { to: "/chunks", label: "05 Raw retrieval" },
] as const;

function ResultTabs({ showResultTabs }: { showResultTabs: boolean }) {
  const tabClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "shrink-0 border-b-2 px-4 py-3 text-sm transition-colors",
      isActive
        ? "border-primary bg-accent text-primary"
        : "border-transparent text-muted-foreground hover:bg-accent/60 hover:text-foreground",
    );

  return (
    <nav className="mb-7 flex gap-1 overflow-x-auto border-b border-border" aria-label="Answer sections">
      {showResultTabs
        ? RESULT_TABS.map(({ to, label }) => (
            <NavLink key={to} to={to} className={tabClass}>
              {label}
            </NavLink>
          ))
        : null}
      <NavLink to="/trace" className={tabClass}>
        06 Technical trace
      </NavLink>
    </nav>
  );
}

function AskHero() {
  return (
    <div className="mb-9 grid items-end gap-8 lg:grid-cols-[1fr_280px]">
      <div>
        <div className="tiny mb-3 text-primary">Clinical evidence interface / 01</div>
        <h1 className="font-heading text-5xl font-semibold leading-[.92] tracking-[-.05em] md:text-7xl">
          Ask a question.
          <br />
          <span className="text-muted-foreground">Make evidence earn it.</span>
        </h1>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">
        Wiqaya separates fluency from safety. Every generated claim is tied back to source evidence - or the system
        stays quiet.
      </p>
    </div>
  );
}

function EmptyTrail() {
  return (
    <div className="panel glow grid min-h-[360px] place-items-center rounded-3xl p-10 text-center">
      <div>
        <div className="mb-5 font-heading text-6xl text-primary">⌁</div>
        <h2 className="font-heading text-2xl font-semibold">No evidence trail yet.</h2>
        <p className="mx-auto mt-2 max-w-md text-muted-foreground">
          Ask a clinical question to create a traceable chain from retrieval → safety gate → answer → audit.
        </p>
        <div className="mt-6 font-data text-xs text-muted-foreground">0 claims // 0 citations // 0 assumptions</div>
      </div>
    </div>
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
    <section className="py-10">
      <AskHero />

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

      <div className="mt-7">
        {answer.isPending ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-48 w-full rounded-2xl" />
          </div>
        ) : null}

        {answer.isError ? <ErrorBanner error={answer.error} /> : null}

        {showResults && trace ? (
          <>
            <GateBanner gate={trace.gate} />
            <ResultTabs showResultTabs={trace.gate.verdict !== "REFUSE"} />
          </>
        ) : null}

        <Routes>
          <Route index element={!trace && !answer.isPending && !answer.isError ? <EmptyTrail /> : null} />
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
                element={
                  <ConfidenceSafetyCard
                    confidence={trace.final.confidence}
                    disclaimer={trace.final.disclaimer}
                    audit={trace.audit}
                  />
                }
              />
              <Route path="chunks" element={trace.retrieval ? <EvidencePanel retrieval={trace.retrieval} /> : null} />
            </>
          ) : null}
          <Route path="trace" element={showResults && trace ? <TraceDetails trace={trace} /> : null} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </section>
  );
}
