from typing import Optional

from src.core.schemas import ClaimAudit, Confidence, GateDecision, GroundedAnswer, ThresholdDecision


def compute_confidence(
    gate: GateDecision,
    threshold: Optional[ThresholdDecision],
    claim_audit: Optional[ClaimAudit],
    raw_answer: Optional[GroundedAnswer],
) -> Confidence:
    if (threshold is not None and threshold.action == "HALT") or (raw_answer is not None and raw_answer.insufficient_evidence):
        return "Insufficient Evidence"

    has_unsupported_claim = claim_audit is not None and claim_audit.unsupported_rate > 0
    has_failed_quote = claim_audit is not None and any(not qc.verified for qc in claim_audit.quote_checks)
    if (threshold is not None and threshold.action == "DOWNGRADE") or has_unsupported_claim or has_failed_quote:
        return "Low"

    if gate.verdict == "CAUTION":
        return "Medium"

    return "High"
