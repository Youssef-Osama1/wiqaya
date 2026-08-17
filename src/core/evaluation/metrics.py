from src.core.schemas import ClaimAudit, QuoteCheck


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(top_k)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


def citation_accuracy(quote_checks: list[QuoteCheck]) -> float:
    if not quote_checks:
        return 0.0
    return sum(1 for qc in quote_checks if qc.verified) / len(quote_checks)


def unsupported_claim_rate(claim_audits: list[ClaimAudit]) -> float:
    if not claim_audits:
        return 0.0
    return sum(audit.unsupported_rate for audit in claim_audits) / len(claim_audits)


def refusal_correctness(refused: list[bool]) -> float:
    if not refused:
        return 0.0
    return sum(1 for r in refused if r) / len(refused)
