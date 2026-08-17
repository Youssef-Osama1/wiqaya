from src.core.evaluation.metrics import (
    citation_accuracy,
    precision_at_k,
    reciprocal_rank,
    recall_at_k,
    refusal_correctness,
    unsupported_claim_rate,
)
from src.core.schemas import ClaimAudit, QuoteCheck


class TestPrecisionAtK:
    def test_all_retrieved_relevant_is_perfect_precision(self):
        assert precision_at_k(["a", "b", "c"], {"a", "b", "c"}, k=3) == 1.0

    def test_none_relevant_is_zero_precision(self):
        assert precision_at_k(["a", "b", "c"], {"x", "y"}, k=3) == 0.0

    def test_partial_match(self):
        assert precision_at_k(["a", "b", "c"], {"a", "x"}, k=3) == 1 / 3

    def test_only_considers_top_k_retrieved(self):
        assert precision_at_k(["a", "b", "c", "d"], {"d"}, k=3) == 0.0

    def test_denominator_is_min_k_and_len_retrieved_not_just_k(self):
        assert precision_at_k(["a"], {"a"}, k=5) == 1.0

    def test_empty_retrieved_is_zero_not_a_crash(self):
        assert precision_at_k([], {"a"}, k=5) == 0.0


class TestRecallAtK:
    def test_all_relevant_found_is_perfect_recall(self):
        assert recall_at_k(["a", "b", "c"], {"a", "b"}, k=3) == 1.0

    def test_none_found_is_zero_recall(self):
        assert recall_at_k(["a", "b", "c"], {"x", "y"}, k=3) == 0.0

    def test_partial_recall(self):
        assert recall_at_k(["a", "b"], {"a", "b", "c", "d"}, k=2) == 0.5

    def test_only_considers_top_k_retrieved(self):
        assert recall_at_k(["a", "b", "c", "d"], {"a", "d"}, k=2) == 0.5

    def test_empty_relevant_set_is_zero_not_a_crash(self):
        assert recall_at_k(["a", "b"], set(), k=2) == 0.0


class TestReciprocalRank:
    def test_first_result_relevant_gives_rank_one(self):
        assert reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0

    def test_third_result_relevant_gives_one_third(self):
        assert reciprocal_rank(["x", "y", "a"], {"a"}) == 1 / 3

    def test_no_relevant_result_gives_zero(self):
        assert reciprocal_rank(["x", "y", "z"], {"a"}) == 0.0

    def test_uses_first_matching_rank_when_multiple_relevant(self):
        assert reciprocal_rank(["x", "a", "b"], {"a", "b"}) == 1 / 2

    def test_empty_retrieved_is_zero_not_a_crash(self):
        assert reciprocal_rank([], {"a"}) == 0.0


def make_quote_check(verified: bool) -> QuoteCheck:
    return QuoteCheck(chunk_id="c1", quote="q", verified=verified, match_ratio=1.0 if verified else 0.1)


class TestCitationAccuracy:
    def test_all_verified_is_perfect_accuracy(self):
        assert citation_accuracy([make_quote_check(True), make_quote_check(True)]) == 1.0

    def test_half_verified_is_half_accuracy(self):
        assert citation_accuracy([make_quote_check(True), make_quote_check(False)]) == 0.5

    def test_no_quote_checks_is_zero_not_a_crash(self):
        assert citation_accuracy([]) == 0.0


class TestUnsupportedClaimRate:
    def test_averages_unsupported_rate_across_answers(self):
        audits = [
            ClaimAudit(quote_checks=[], claims=[], unsupported_rate=0.0),
            ClaimAudit(quote_checks=[], claims=[], unsupported_rate=1.0),
        ]
        assert unsupported_claim_rate(audits) == 0.5

    def test_no_audits_is_zero_not_a_crash(self):
        assert unsupported_claim_rate([]) == 0.0


class TestRefusalCorrectness:
    def test_all_correctly_refused_is_one(self):
        assert refusal_correctness([True, True, True]) == 1.0

    def test_half_correctly_refused_is_half(self):
        assert refusal_correctness([True, False]) == 0.5

    def test_no_out_of_scope_questions_is_zero_not_a_crash(self):
        assert refusal_correctness([]) == 0.0
