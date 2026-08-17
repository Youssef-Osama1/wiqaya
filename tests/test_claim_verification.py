from src.core.guardrails.claim_verification import verify_evidence_quote
from src.core.schemas import EvidenceItem

CHUNK_TEXT = (
    "1.4.15 Offer an ACE inhibitor as first-line treatment for adults aged under 55 "
    "with hypertension, unless the person is of black African or African-Caribbean origin."
)


class TestVerifyEvidenceQuote:
    def test_exact_verbatim_quote_is_verified_with_ratio_one(self):
        item = EvidenceItem(quote="Offer an ACE inhibitor as first-line treatment for adults aged under 55", chunk_id="c1")
        check = verify_evidence_quote(item, CHUNK_TEXT)
        assert check.verified is True
        assert check.match_ratio == 1.0
        assert check.chunk_id == "c1"

    def test_quote_with_different_case_and_whitespace_still_verifies(self):
        item = EvidenceItem(quote="  offer AN ace inhibitor   as first-line treatment  ", chunk_id="c1")
        check = verify_evidence_quote(item, CHUNK_TEXT)
        assert check.verified is True
        assert check.match_ratio == 1.0

    def test_near_verbatim_quote_with_one_word_typo_still_verifies_via_ratio(self):
        item = EvidenceItem(
            quote="Offer an ACE inhibitor as first-line treetment for adults aged under 55",
            chunk_id="c1",
        )
        check = verify_evidence_quote(item, CHUNK_TEXT)
        assert check.verified is True
        assert check.match_ratio >= 0.9

    def test_fabricated_unrelated_quote_is_not_verified(self):
        item = EvidenceItem(quote="Patients should take metformin twice daily with food", chunk_id="c1")
        check = verify_evidence_quote(item, CHUNK_TEXT)
        assert check.verified is False
        assert check.match_ratio < 0.9

    def test_empty_quote_is_not_verified(self):
        item = EvidenceItem(quote="", chunk_id="c1")
        check = verify_evidence_quote(item, CHUNK_TEXT)
        assert check.verified is False
        assert check.match_ratio == 0.0
