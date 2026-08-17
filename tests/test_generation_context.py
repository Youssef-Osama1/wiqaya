from src.core.generation.context import assemble_context
from src.core.schemas import Chunk, ChunkMetadata


def make_chunk(chunk_id: str, text: str, has_cross_reference: bool = False) -> Chunk:
    return Chunk(
        text=text,
        metadata=ChunkMetadata(
            document_name="NICE NG136", page_number=5, section_title="Treatment",
            chunk_id=chunk_id, source_url="https://nice.org.uk/ng136", doc_key="nice",
            token_count=10, has_cross_reference=has_cross_reference,
        ),
    )


class TestAssembleContext:
    def test_chunk_id_header_and_full_text_are_present(self):
        chunk = make_chunk("nice-p005-aaaa1111", "Offer an ACE inhibitor as first-line treatment.")
        context = assemble_context([chunk])
        assert "nice-p005-aaaa1111" in context
        assert "Offer an ACE inhibitor as first-line treatment." in context

    def test_full_chunk_text_never_truncated(self):
        long_text = "Clinical detail sentence. " * 200
        chunk = make_chunk("c1", long_text)
        context = assemble_context([chunk])
        assert long_text in context

    def test_cross_reference_flag_is_noted_when_true(self):
        chunk = make_chunk("c1", "text", has_cross_reference=True)
        context = assemble_context([chunk])
        assert "cross-reference" in context.lower()

    def test_cross_reference_note_absent_when_false(self):
        chunk = make_chunk("c1", "text", has_cross_reference=False)
        context = assemble_context([chunk])
        assert "cross-reference" not in context.lower()

    def test_multiple_chunks_all_present(self):
        chunks = [make_chunk("c1", "first chunk text"), make_chunk("c2", "second chunk text")]
        context = assemble_context(chunks)
        assert "first chunk text" in context
        assert "second chunk text" in context
        assert "c1" in context
        assert "c2" in context

    def test_empty_chunk_list_returns_empty_string(self):
        assert assemble_context([]) == ""
