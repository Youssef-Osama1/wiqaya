from src.core.chunking.chunk_ids import compute_chunk_id


class TestComputeChunkId:
    def test_format_is_doc_key_page_hash(self):
        chunk_id = compute_chunk_id("nice_ng136", 21, "some chunk text")
        doc_key, page_part, hash_part = chunk_id.split("-")
        assert doc_key == "nice_ng136"
        assert page_part == "p021"
        assert len(hash_part) == 8

    def test_same_input_gives_identical_id_across_runs(self):
        id1 = compute_chunk_id("nice_ng136", 21, "some chunk text")
        id2 = compute_chunk_id("nice_ng136", 21, "some chunk text")
        assert id1 == id2

    def test_different_text_gives_different_id(self):
        id1 = compute_chunk_id("nice_ng136", 21, "text A")
        id2 = compute_chunk_id("nice_ng136", 21, "text B")
        assert id1 != id2

    def test_trivial_whitespace_differences_do_not_change_id(self):
        id1 = compute_chunk_id("nice_ng136", 21, "some  chunk\ntext")
        id2 = compute_chunk_id("nice_ng136", 21, "some chunk text")
        assert id1 == id2

    def test_page_number_is_zero_padded_to_3_digits(self):
        chunk_id = compute_chunk_id("who_hypertension", 7, "text")
        assert "-p007-" in chunk_id
