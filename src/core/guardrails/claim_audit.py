from src.core.schemas import ClaimAudit, ClaimSupport, QuoteCheck


def compute_claim_audit(quote_checks: list[QuoteCheck], claims: list[ClaimSupport]) -> ClaimAudit:
    unsupported_rate = sum(1 for c in claims if not c.supported) / len(claims) if claims else 0.0
    return ClaimAudit(quote_checks=quote_checks, claims=claims, unsupported_rate=unsupported_rate)
