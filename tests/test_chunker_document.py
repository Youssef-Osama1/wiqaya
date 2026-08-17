from src.core.chunking.chunker import chunk_document


class TestChunkDocumentMandatoryFields:
    def test_five_mandatory_metadata_fields_non_empty_on_every_chunk(self):
        for doc_key in ("who_hypertension", "nice_ng136"):
            for chunk in chunk_document(doc_key):
                assert chunk.metadata.document_name
                assert chunk.metadata.page_number > 0
                assert chunk.metadata.section_title
                assert chunk.metadata.chunk_id
                assert chunk.metadata.source_url


class TestChunkDocumentDeterminism:
    def test_two_runs_produce_identical_chunk_ids(self):
        ids1 = [c.metadata.chunk_id for c in chunk_document("nice_ng136")]
        ids2 = [c.metadata.chunk_id for c in chunk_document("nice_ng136")]
        assert ids1 == ids2

    def test_chunk_ids_are_unique_within_a_document(self):
        ids = [c.metadata.chunk_id for c in chunk_document("nice_ng136")]
        assert len(ids) == len(set(ids))


class TestChunkDocumentAtomicity:
    def test_known_recommendation_lives_whole_inside_one_chunk(self):
        chunks = chunk_document("nice_ng136")
        matches = [c for c in chunks if "1.4.39" in c.metadata.recommendation_ids]
        assert len(matches) == 1
        assert "bendroflumethiazide" in matches[0].text
        assert matches[0].text.rstrip().endswith("[2019]") or "[2019]" in matches[0].text


class TestChunkDocumentTokenBudget:
    def test_no_chunk_exceeds_hard_max_unless_it_is_a_lone_oversized_recommendation(self):
        for doc_key in ("who_hypertension", "nice_ng136"):
            for chunk in chunk_document(doc_key):
                if chunk.metadata.token_count > 800:
                    assert len(chunk.metadata.recommendation_ids) == 1

    def test_most_chunks_fall_within_the_expected_histogram_band(self):
        for doc_key in ("who_hypertension", "nice_ng136"):
            chunks = chunk_document(doc_key)
            in_band = [c for c in chunks if 120 <= c.metadata.token_count <= 800]
            assert len(in_band) / len(chunks) > 0.8


class TestChunkDocumentCrossReference:
    def test_flags_known_cross_reference_mention(self):
        chunks = chunk_document("nice_ng136")
        flagged = [c for c in chunks if c.metadata.has_cross_reference]
        assert flagged
        assert any("guideline on" in c.text.lower() for c in flagged)
