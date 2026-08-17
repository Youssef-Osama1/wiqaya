import json

from src.core.evaluation.golden import load_chunks_by_id, load_golden_set, validate_golden_set
from src.core.schemas import Chunk, GoldenAnchor, GoldenQuestion


def make_question(**overrides) -> GoldenQuestion:
    base = dict(
        qid="Q1", question="What is the target BP?", category="direct",
        relevant_chunk_ids=["doc-p001-aaaa1111"],
        anchors=[GoldenAnchor(chunk_id="doc-p001-aaaa1111", anchor_text="target blood pressure")],
        expected_behavior="answer", notes="",
    )
    base.update(overrides)
    return GoldenQuestion(**base)


def make_chunks_by_id() -> dict[str, Chunk]:
    return {
        "doc-p001-aaaa1111": Chunk(
            text="The target blood pressure for adults under 80 is below 140/90 mmHg.",
            metadata={
                "document_name": "Test Doc", "page_number": 1, "section_title": "Targets",
                "chunk_id": "doc-p001-aaaa1111", "source_url": "https://example.com", "doc_key": "doc",
                "token_count": 12,
            },
        )
    }


class TestValidateGoldenSet:
    def test_valid_question_produces_no_errors(self):
        errors = validate_golden_set([make_question()], make_chunks_by_id())
        assert errors == []

    def test_unknown_relevant_chunk_id_is_an_error(self):
        q = make_question(relevant_chunk_ids=["doc-p999-notreal"], anchors=[])
        errors = validate_golden_set([q], make_chunks_by_id())
        assert len(errors) == 1
        assert "doc-p999-notreal" in errors[0]

    def test_unknown_anchor_chunk_id_is_an_error(self):
        q = make_question(
            relevant_chunk_ids=[],
            anchors=[GoldenAnchor(chunk_id="doc-p999-notreal", anchor_text="anything")],
        )
        errors = validate_golden_set([q], make_chunks_by_id())
        assert len(errors) == 1

    def test_anchor_text_not_in_chunk_is_an_error(self):
        q = make_question(
            relevant_chunk_ids=["doc-p001-aaaa1111"],
            anchors=[GoldenAnchor(chunk_id="doc-p001-aaaa1111", anchor_text="this text was never in the chunk")],
        )
        errors = validate_golden_set([q], make_chunks_by_id())
        assert len(errors) == 1
        assert "anchor" in errors[0].lower()

    def test_out_of_scope_question_with_no_relevant_ids_is_valid(self):
        q = make_question(relevant_chunk_ids=[], anchors=[], category="out_of_scope", expected_behavior="refuse")
        errors = validate_golden_set([q], make_chunks_by_id())
        assert errors == []


class TestLoadGoldenSet:
    def test_round_trips_from_jsonl(self, tmp_path):
        path = tmp_path / "golden.jsonl"
        with path.open("w") as f:
            f.write(make_question().model_dump_json() + "\n")
            f.write(make_question(qid="Q2").model_dump_json() + "\n")
        questions = load_golden_set(path)
        assert len(questions) == 2
        assert questions[0].qid == "Q1"
        assert questions[1].qid == "Q2"


class TestLoadChunksById:
    def test_loads_from_chunk_artifacts(self, tmp_path):
        chunks_path = tmp_path / "doc_chunks.jsonl"
        with chunks_path.open("w") as f:
            chunk = {
                "text": "sample text",
                "metadata": {
                    "document_name": "Test Doc", "page_number": 1, "section_title": "Sec",
                    "chunk_id": "doc-p001-aaaa1111", "source_url": "https://example.com", "doc_key": "doc",
                    "token_count": 2,
                },
            }
            f.write(json.dumps(chunk) + "\n")
        chunks_by_id = load_chunks_by_id(["doc"], chunks_dir=tmp_path)
        assert "doc-p001-aaaa1111" in chunks_by_id
        assert chunks_by_id["doc-p001-aaaa1111"].text == "sample text"
