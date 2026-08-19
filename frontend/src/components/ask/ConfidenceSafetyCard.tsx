import { confidenceVisuals } from "@/lib/confidence";
import type { ClaimAudit, Confidence } from "@/types/api";

function auditSummary(audit: ClaimAudit | null) {
  if (!audit || audit.quote_checks.length === 0) return null;
  const verified = audit.quote_checks.filter((q) => q.verified).length;
  return { verified, total: audit.quote_checks.length, unsupported: audit.unsupported_rate };
}

export default function ConfidenceSafetyCard({
  confidence,
  disclaimer,
  audit,
}: {
  confidence: Confidence;
  disclaimer: string;
  audit: ClaimAudit | null;
}) {
  const visual = confidenceVisuals[confidence];
  const summary = auditSummary(audit);

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <div className="panel rounded-2xl p-6">
        <div className={`tiny ${visual.textClass}`}>Confidence</div>
        <div className={`metric mt-3 uppercase ${visual.textClass}`}>{visual.label}</div>
      </div>

      <div className="panel rounded-2xl p-6">
        <div className="tiny text-muted-foreground">Audit</div>
        {summary ? (
          <>
            <div className="mt-3 text-2xl">
              {summary.verified} / {summary.total} quotes verified
            </div>
            <div className={summary.unsupported === 0 ? "mt-2 text-success" : "mt-2 text-destructive"}>
              {(summary.unsupported * 100).toFixed(0)}% unsupported claims
            </div>
          </>
        ) : (
          <div className="mt-3 text-2xl text-muted-foreground">No claims to audit</div>
        )}
        <p className="mt-7 text-xs leading-5 text-muted-foreground">{disclaimer}</p>
      </div>
    </div>
  );
}
