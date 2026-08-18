import { ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { confidenceVisuals } from "@/lib/confidence";
import type { ClaimAudit, Confidence } from "@/types/api";

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
  const Icon = visual.icon;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="size-4 text-primary" />
          Confidence &amp; Safety
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`relative rounded-md border-2 border-double p-4 ${visual.badgeClass}`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Icon className="size-5" />
              <span className="font-heading text-lg font-semibold uppercase tracking-wide">{visual.label}</span>
            </div>
            <AuditLine audit={audit} />
          </div>
          <p className="mt-3 border-t border-current/20 pt-3 text-xs leading-relaxed opacity-80">{disclaimer}</p>
        </div>
      </CardContent>
    </Card>
  );
}
