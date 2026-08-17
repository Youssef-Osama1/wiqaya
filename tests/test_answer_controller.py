from src.controllers.AnswerController import AnswerController
from src.core.guardrails.claim_extraction import ClaimExtractionResult
from src.core.schemas import (
    Chunk,
    ChunkMetadata,
    ClaimSupport,
    EvidenceItem,
    GateDecision,
    GroundedAnswer,
    RetrievalResult,
    ScoredChunk,
)
from tests.conftest import make_settings

CHUNK_TEXT = "Offer an ACE inhibitor as first-line treatment for adults aged under 55 with hypertension."


def make_chunk(chunk_id: str = "nice-p005-aaaa1111") -> Chunk:
    return Chunk(
        text=CHUNK_TEXT,
        metadata=ChunkMetadata(
            document_name="NICE NG136", page_number=5, section_title="Treatment",
            chunk_id=chunk_id, source_url="https://nice.org.uk/ng136", doc_key="nice", token_count=15,
        ),
    )


class FakeGateController:
    def __init__(self, decision: GateDecision):
        self.decision = decision
        self.called_with = None

    def evaluate(self, query):
        self.called_with = query
        return self.decision


class FakeRetrievalController:
    def __init__(self, result: RetrievalResult):
        self.result = result
        self.called = False

    def search(self, query, mode, k):
        self.called = True
        return self.result


class FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class FakeLlm:
    def __init__(self, results_by_schema: dict):
        self.results_by_schema = results_by_schema
        self.invoked_schemas = []

    def with_structured_output(self, schema):
        self.invoked_schemas.append(schema)
        return FakeStructuredRunnable(self.results_by_schema[schema])


def make_retrieval_result(score: float, chunk: Chunk) -> RetrievalResult:
    return RetrievalResult(
        query="q", mode="hybrid_rerank", k=1,
        results=[ScoredChunk(chunk=chunk, score=score, source="hybrid_rerank")],
    )


class TestAnswerControllerRefuse:
    def test_refuse_gate_never_calls_retrieval_or_llm(self):
        gate = FakeGateController(GateDecision(verdict="REFUSE", reason="out of scope", triggered_by="out_of_domain"))
        retrieval = FakeRetrievalController(make_retrieval_result(0.9, make_chunk()))
        llm = FakeLlm({})
        controller = AnswerController(make_settings(), gate, retrieval, llm)

        trace = controller.answer("what's the weather?")

        assert retrieval.called is False
        assert llm.invoked_schemas == []
        assert trace.retrieval is None
        assert trace.threshold is None
        assert trace.raw_answer is None
        assert trace.final.confidence == "Insufficient Evidence"


class TestAnswerControllerHalt:
    def test_low_score_halts_before_generation(self):
        gate = FakeGateController(GateDecision(verdict="ALLOW", reason="in scope", triggered_by=None))
        retrieval = FakeRetrievalController(make_retrieval_result(0.1, make_chunk()))
        llm = FakeLlm({})
        settings = make_settings(SIM_HALT_THRESHOLD=0.45, SIM_DOWNGRADE_THRESHOLD=0.65)
        controller = AnswerController(settings, gate, retrieval, llm)

        trace = controller.answer("some in-scope question")

        assert retrieval.called is True
        assert llm.invoked_schemas == []
        assert trace.threshold.action == "HALT"
        assert trace.raw_answer is None
        assert trace.final.confidence == "Insufficient Evidence"


class TestAnswerControllerProceed:
    def test_verified_evidence_produces_high_confidence_with_citation(self):
        chunk = make_chunk()
        gate = FakeGateController(GateDecision(verdict="ALLOW", reason="in scope", triggered_by=None))
        retrieval = FakeRetrievalController(make_retrieval_result(0.95, chunk))
        raw_answer = GroundedAnswer(
            recommendation="Offer an ACE inhibitor first-line.",
            evidence=[EvidenceItem(quote=CHUNK_TEXT, chunk_id=chunk.metadata.chunk_id)],
            insufficient_evidence=False,
            caveats=[],
        )
        llm = FakeLlm({
            GroundedAnswer: raw_answer,
            ClaimExtractionResult: ClaimExtractionResult(claims=[ClaimSupport(claim="ACE inhibitor is first-line", supported=True)]),
        })
        settings = make_settings(SIM_HALT_THRESHOLD=0.45, SIM_DOWNGRADE_THRESHOLD=0.65)
        controller = AnswerController(settings, gate, retrieval, llm)

        trace = controller.answer("What is first-line treatment?")

        assert trace.final.confidence == "High"
        assert len(trace.final.citations) == 1
        assert trace.final.citations[0].chunk_id == chunk.metadata.chunk_id
        assert len(trace.final.evidence) == 1
        assert trace.audit.unsupported_rate == 0.0

    def test_hallucinated_quote_is_dropped_and_downgrades_confidence(self):
        chunk = make_chunk()
        gate = FakeGateController(GateDecision(verdict="ALLOW", reason="in scope", triggered_by=None))
        retrieval = FakeRetrievalController(make_retrieval_result(0.95, chunk))
        raw_answer = GroundedAnswer(
            recommendation="Take 200mg twice daily.",
            evidence=[EvidenceItem(quote="This exact sentence never appears anywhere in the guideline text.", chunk_id=chunk.metadata.chunk_id)],
            insufficient_evidence=False,
            caveats=[],
        )
        llm = FakeLlm({
            GroundedAnswer: raw_answer,
            ClaimExtractionResult: ClaimExtractionResult(claims=[]),
        })
        settings = make_settings(SIM_HALT_THRESHOLD=0.45, SIM_DOWNGRADE_THRESHOLD=0.65)
        controller = AnswerController(settings, gate, retrieval, llm)

        trace = controller.answer("What is first-line treatment?")

        assert trace.final.evidence == []
        assert trace.final.confidence == "Low"

    def test_downgrade_threshold_caps_confidence_at_low(self):
        chunk = make_chunk()
        gate = FakeGateController(GateDecision(verdict="ALLOW", reason="in scope", triggered_by=None))
        retrieval = FakeRetrievalController(make_retrieval_result(0.5, chunk))
        raw_answer = GroundedAnswer(
            recommendation="Offer an ACE inhibitor first-line.",
            evidence=[EvidenceItem(quote=CHUNK_TEXT, chunk_id=chunk.metadata.chunk_id)],
            insufficient_evidence=False,
            caveats=[],
        )
        llm = FakeLlm({
            GroundedAnswer: raw_answer,
            ClaimExtractionResult: ClaimExtractionResult(claims=[]),
        })
        settings = make_settings(SIM_HALT_THRESHOLD=0.45, SIM_DOWNGRADE_THRESHOLD=0.65)
        controller = AnswerController(settings, gate, retrieval, llm)

        trace = controller.answer("What is first-line treatment?")

        assert trace.threshold.action == "DOWNGRADE"
        assert trace.final.confidence == "Low"

    def test_caution_gate_uses_strengthened_disclaimer(self):
        chunk = make_chunk()
        gate = FakeGateController(GateDecision(verdict="CAUTION", reason="personal dosing question", triggered_by="personal_dosing"))
        retrieval = FakeRetrievalController(make_retrieval_result(0.95, chunk))
        raw_answer = GroundedAnswer(
            recommendation="Offer an ACE inhibitor first-line.",
            evidence=[EvidenceItem(quote=CHUNK_TEXT, chunk_id=chunk.metadata.chunk_id)],
            insufficient_evidence=False,
            caveats=[],
        )
        llm = FakeLlm({
            GroundedAnswer: raw_answer,
            ClaimExtractionResult: ClaimExtractionResult(claims=[]),
        })
        settings = make_settings(SIM_HALT_THRESHOLD=0.45, SIM_DOWNGRADE_THRESHOLD=0.65)
        controller = AnswerController(settings, gate, retrieval, llm)

        trace = controller.answer("What BP medication should I take?")

        assert trace.final.confidence == "Medium"
        assert "healthcare provider" in trace.final.disclaimer.lower()
