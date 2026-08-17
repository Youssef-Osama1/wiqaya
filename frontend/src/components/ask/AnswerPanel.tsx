import ReactMarkdown from "react-markdown";
import { confidenceVisuals } from "@/lib/confidence";
import CitationTable from "@/components/ask/CitationTable";
import EmptyState from "@/components/common/EmptyState";
import type { ClaimAudit, FinalAnswer } from "@/types/api";

function AuditLine({ audit }: { audit: ClaimAudit | null }) {
  if (!audit) return null;
  const verified = audit.quote_checks.filter((q) => q.verified).length;
  const total = audit.quote_checks.length;
  if (total === 0) return null;
  return (
    <span className="font-mono text-[11px] uppercase tracking-wide opacity-70">
      {verified}/{total} quotes verified · {(audit.unsupported_rate * 100).toFixed(0)}% unsupported
    </span>
  );
}

export default function AnswerPanel({ final, audit }: { final: FinalAnswer; audit: ClaimAudit | null }) {
  const visual = confidenceVisuals[final.confidence];
  const Icon = visual.icon;

  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-2 font-heading text-sm font-semibold text-muted-foreground">Recommendation</h2>
        <div className="prose prose-sm max-w-none text-foreground prose-headings:font-heading">
          <ReactMarkdown>{final.recommendation}</ReactMarkdown>
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-heading text-sm font-semibold text-muted-foreground">Supporting Evidence</h2>
        {final.evidence.length === 0 ? (
          <EmptyState title="No verified supporting quotes" />
        ) : (
          <ul className="space-y-2">
            {final.evidence.map((item, i) => (
              <li key={`${item.chunk_id}-${i}`} className="border-l-2 border-primary/40 pl-3 text-sm italic text-foreground/85">
                “{item.quote}”
                <div className="mt-0.5 font-mono text-[11px] not-italic text-muted-foreground">— {item.chunk_id}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-2 font-heading text-sm font-semibold text-muted-foreground">Citations</h2>
        <CitationTable citations={final.citations} />
      </section>

      <section>
        <h2 className="mb-2 font-heading text-sm font-semibold text-muted-foreground">Confidence &amp; Safety</h2>
        <div className={`relative rounded-md border-2 border-double p-4 ${visual.badgeClass}`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Icon className="size-5" />
              <span className="font-heading text-lg font-semibold uppercase tracking-wide">{visual.label}</span>
            </div>
            <AuditLine audit={audit} />
          </div>
          <p className="mt-3 border-t border-current/20 pt-3 text-xs leading-relaxed opacity-80">{final.disclaimer}</p>
        </div>
      </section>
    </div>
  );
}
