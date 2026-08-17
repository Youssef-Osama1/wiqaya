from src.core.guardrails.claim_extraction import extract_claim_support
from src.core.schemas import ClaimSupport


class FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class FakeLlm:
    def __init__(self, result):
        self._result = result
        self.last_schema = None

    def with_structured_output(self, schema):
        self.last_schema = schema
        return FakeStructuredRunnable(self._result)


class TestExtractClaimSupport:
    def test_returns_claim_support_list_from_structured_result(self):
        from src.core.guardrails.claim_extraction import ClaimExtractionResult

        fake_result = ClaimExtractionResult(
            claims=[
                ClaimSupport(claim="ACE inhibitors are first-line for adults under 55", supported=True),
                ClaimSupport(claim="Treatment should start at 200mg daily", supported=False),
            ]
        )
        llm = FakeLlm(fake_result)
        claims = extract_claim_support(llm, recommendation="...", retrieved_text="...")
        assert claims == fake_result.claims

    def test_uses_structured_output_with_claim_extraction_schema(self):
        from src.core.guardrails.claim_extraction import ClaimExtractionResult

        llm = FakeLlm(ClaimExtractionResult(claims=[]))
        extract_claim_support(llm, recommendation="...", retrieved_text="...")
        assert llm.last_schema is ClaimExtractionResult

    def test_no_claims_extracted_returns_empty_list(self):
        from src.core.guardrails.claim_extraction import ClaimExtractionResult

        llm = FakeLlm(ClaimExtractionResult(claims=[]))
        claims = extract_claim_support(llm, recommendation="no factual claims here", retrieved_text="...")
        assert claims == []
