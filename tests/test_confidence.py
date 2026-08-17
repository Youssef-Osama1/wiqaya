from src.core.generation.confidence import compute_confidence
from src.core.schemas import ClaimAudit, GateDecision, GroundedAnswer, QuoteCheck, ThresholdDecision


def gate(verdict="ALLOW"):
    return GateDecision(verdict=verdict, reason="r", triggered_by=None)


def threshold(action="PROCEED", score=0.9):
    return ThresholdDecision(action=action, top_score=score, reason="r")


def audit(unsupported_rate=0.0, quote_checks=None):
    return ClaimAudit(quote_checks=quote_checks or [], claims=[], unsupported_rate=unsupported_rate)


def answer(insufficient=False):
    return GroundedAnswer(recommendation="rec", evidence=[], insufficient_evidence=insufficient, caveats=[])


class TestComputeConfidence:
    def test_proceed_all_verified_no_unsupported_is_high(self):
        result = compute_confidence(gate(), threshold("PROCEED"), audit(0.0), answer())
        assert result == "High"

    def test_halt_is_insufficient_evidence_regardless_of_other_signals(self):
        result = compute_confidence(gate(), threshold("HALT", 0.1), claim_audit=None, raw_answer=None)
        assert result == "Insufficient Evidence"

    def test_llm_self_reported_insufficient_evidence_overrides_proceed(self):
        result = compute_confidence(gate(), threshold("PROCEED"), audit(0.0), answer(insufficient=True))
        assert result == "Insufficient Evidence"

    def test_downgrade_threshold_is_low(self):
        result = compute_confidence(gate(), threshold("DOWNGRADE", 0.5), audit(0.0), answer())
        assert result == "Low"

    def test_unsupported_claim_is_low_even_on_proceed(self):
        result = compute_confidence(gate(), threshold("PROCEED"), audit(unsupported_rate=0.5), answer())
        assert result == "Low"

    def test_failed_quote_check_is_low_even_with_zero_unsupported_rate(self):
        failed_quote = [QuoteCheck(chunk_id="c1", quote="q", verified=False, match_ratio=0.2)]
        result = compute_confidence(gate(), threshold("PROCEED"), audit(0.0, quote_checks=failed_quote), answer())
        assert result == "Low"

    def test_caution_gate_with_clean_audit_is_medium(self):
        result = compute_confidence(gate("CAUTION"), threshold("PROCEED"), audit(0.0), answer())
        assert result == "Medium"

    def test_caution_gate_with_unsupported_claim_is_low_not_medium(self):
        result = compute_confidence(gate("CAUTION"), threshold("PROCEED"), audit(unsupported_rate=1.0), answer())
        assert result == "Low"
