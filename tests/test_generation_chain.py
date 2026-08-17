from src.core.generation.chain import generate_grounded_answer
from src.core.schemas import Chunk, ChunkMetadata, EvidenceItem, GroundedAnswer


class FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return self._result


class FakeLlm:
    def __init__(self, result):
        self._result = result
        self.last_schema = None
        self.structured_runnable = None

    def with_structured_output(self, schema):
        self.last_schema = schema
        self.structured_runnable = FakeStructuredRunnable(self._result)
        return self.structured_runnable


def make_chunk(chunk_id: str) -> Chunk:
    return Chunk(
        text="Offer an ACE inhibitor as first-line treatment for adults under 55.",
        metadata=ChunkMetadata(
            document_name="NICE NG136", page_number=5, section_title="Treatment",
            chunk_id=chunk_id, source_url="https://nice.org.uk/ng136", doc_key="nice", token_count=10,
        ),
    )


class TestGenerateGroundedAnswer:
    def test_returns_the_structured_result_directly(self):
        expected = GroundedAnswer(
            recommendation="Offer an ACE inhibitor first-line.",
            evidence=[EvidenceItem(quote="Offer an ACE inhibitor as first-line treatment for adults under 55.", chunk_id="c1")],
            insufficient_evidence=False,
            caveats=[],
        )
        llm = FakeLlm(expected)
        result = generate_grounded_answer(llm, "What's first-line treatment?", [make_chunk("c1")])
        assert result == expected

    def test_uses_structured_output_with_grounded_answer_schema(self):
        llm = FakeLlm(GroundedAnswer(recommendation="r", evidence=[], insufficient_evidence=False, caveats=[]))
        generate_grounded_answer(llm, "q", [make_chunk("c1")])
        assert llm.last_schema is GroundedAnswer

    def test_query_and_full_chunk_text_reach_the_prompt(self):
        llm = FakeLlm(GroundedAnswer(recommendation="r", evidence=[], insufficient_evidence=False, caveats=[]))
        generate_grounded_answer(llm, "What's first-line treatment?", [make_chunk("c1")])
        prompt_text = " ".join(m.content for m in llm.structured_runnable.last_messages)
        assert "What's first-line treatment?" in prompt_text
        assert "Offer an ACE inhibitor as first-line treatment for adults under 55." in prompt_text
        assert "c1" in prompt_text
