from src.core.generation.citations import resolve_citations
from src.core.schemas import Chunk, ChunkMetadata, EvidenceItem


def make_chunk(chunk_id: str, page: int = 5) -> Chunk:
    return Chunk(
        text="some chunk text",
        metadata=ChunkMetadata(
            document_name="NICE NG136", page_number=page, section_title="Treatment",
            chunk_id=chunk_id, source_url="https://nice.org.uk/ng136", doc_key="nice",
            token_count=10,
        ),
    )


class TestResolveCitations:
    def test_known_chunk_id_resolves_to_citation_from_metadata(self):
        chunks = [make_chunk("nice-p005-aaaa1111", page=5)]
        evidence = [EvidenceItem(quote="q", chunk_id="nice-p005-aaaa1111")]

        citations, unresolved = resolve_citations(evidence, chunks)

        assert unresolved == []
        assert len(citations) == 1
        c = citations[0]
        assert c.chunk_id == "nice-p005-aaaa1111"
        assert c.document_name == "NICE NG136"
        assert c.section_title == "Treatment"
        assert c.page_number == 5

    def test_unknown_chunk_id_is_flagged_not_fabricated(self):
        chunks = [make_chunk("nice-p005-aaaa1111")]
        evidence = [EvidenceItem(quote="q", chunk_id="does-not-exist")]

        citations, unresolved = resolve_citations(evidence, chunks)

        assert citations == []
        assert unresolved == ["does-not-exist"]

    def test_duplicate_chunk_ids_resolve_to_one_citation_each_occurrence_deduped(self):
        chunks = [make_chunk("nice-p005-aaaa1111")]
        evidence = [
            EvidenceItem(quote="q1", chunk_id="nice-p005-aaaa1111"),
            EvidenceItem(quote="q2", chunk_id="nice-p005-aaaa1111"),
        ]

        citations, unresolved = resolve_citations(evidence, chunks)

        assert len(citations) == 1
        assert unresolved == []

    def test_mixed_known_and_unknown_evidence(self):
        chunks = [make_chunk("known-1")]
        evidence = [
            EvidenceItem(quote="q1", chunk_id="known-1"),
            EvidenceItem(quote="q2", chunk_id="unknown-1"),
        ]

        citations, unresolved = resolve_citations(evidence, chunks)

        assert [c.chunk_id for c in citations] == ["known-1"]
        assert unresolved == ["unknown-1"]

    def test_no_evidence_returns_empty_lists(self):
        citations, unresolved = resolve_citations([], [make_chunk("c1")])
        assert citations == []
        assert unresolved == []
