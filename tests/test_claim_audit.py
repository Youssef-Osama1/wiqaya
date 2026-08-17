from src.core.guardrails.claim_audit import compute_claim_audit
from src.core.schemas import ClaimSupport, QuoteCheck


class TestComputeClaimAudit:
    def test_all_claims_supported_gives_zero_unsupported_rate(self):
        claims = [ClaimSupport(claim="a", supported=True), ClaimSupport(claim="b", supported=True)]
        audit = compute_claim_audit(quote_checks=[], claims=claims)
        assert audit.unsupported_rate == 0.0
        assert audit.claims == claims

    def test_half_unsupported_gives_half_rate(self):
        claims = [ClaimSupport(claim="a", supported=True), ClaimSupport(claim="b", supported=False)]
        audit = compute_claim_audit(quote_checks=[], claims=claims)
        assert audit.unsupported_rate == 0.5

    def test_no_claims_gives_zero_rate_not_division_error(self):
        audit = compute_claim_audit(quote_checks=[], claims=[])
        assert audit.unsupported_rate == 0.0

    def test_quote_checks_are_carried_through_unchanged(self):
        quote_checks = [QuoteCheck(chunk_id="c1", quote="q", verified=True, match_ratio=1.0)]
        audit = compute_claim_audit(quote_checks=quote_checks, claims=[])
        assert audit.quote_checks == quote_checks
