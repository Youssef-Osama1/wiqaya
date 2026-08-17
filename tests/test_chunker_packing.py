from src.core.chunking.chunker import Unit, pack_units

WORD_COUNT = lambda text: len(text.split())


def make_unit(words: int, page: int = 1, section: str = "Sec", rec_id=None, atomic=False) -> Unit:
    return Unit(
        text=" ".join(f"w{i}" for i in range(words)),
        page_number=page,
        page_end=page,
        section_title=section,
        section_path=[section],
        recommendation_id=rec_id,
        is_atomic=atomic,
    )


class TestPackUnitsBasic:
    def test_small_units_pack_into_single_chunk(self):
        units = [make_unit(50), make_unit(50), make_unit(50)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        assert len(chunks) == 1
        assert chunks[0] == units

    def test_closes_chunk_once_target_reached(self):
        units = [make_unit(300), make_unit(300), make_unit(300)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        assert len(chunks) == 2
        assert chunks[0] == units[:2]

    def test_never_exceeds_hard_max_for_non_atomic_units(self):
        units = [make_unit(500), make_unit(500), make_unit(500)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        for chunk in chunks:
            assert sum(WORD_COUNT(u.text) for u in chunk) <= 800

    def test_atomic_unit_kept_whole_even_if_it_exceeds_hard_max(self):
        huge_rec = make_unit(1000, rec_id="1.4.39", atomic=True)
        units = [make_unit(100), huge_rec, make_unit(100)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        found = [c for c in chunks if huge_rec in c]
        assert len(found) == 1
        assert len(found[0]) == 1


class TestPackUnitsMinMerge:
    def test_trailing_fragment_below_min_merges_into_previous_chunk(self):
        units = [make_unit(310), make_unit(310), make_unit(310), make_unit(310), make_unit(30)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        last_chunk_tokens = sum(WORD_COUNT(u.text) for u in chunks[-1])
        assert last_chunk_tokens >= 120


class TestPackUnitsOverlap:
    def test_multi_chunk_run_repeats_trailing_units_for_context(self):
        units = [make_unit(60, page=(i // 10) + 1) for i in range(12)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        assert len(chunks) > 1
        first_chunk_last_unit = chunks[0][-1]
        second_chunk_units = chunks[1]
        assert first_chunk_last_unit in second_chunk_units

    def test_overlap_seed_never_forces_a_chunk_past_hard_max(self):
        units = [make_unit(500), make_unit(500), make_unit(500)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        for chunk in chunks:
            assert sum(WORD_COUNT(u.text) for u in chunk) <= 800

    def test_no_trailing_chunk_that_is_pure_overlap_with_no_new_content(self):
        units = [make_unit(300, page=1), make_unit(300, page=2), make_unit(300, page=3), make_unit(300, page=4)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        for prev_chunk, chunk in zip(chunks, chunks[1:]):
            assert any(u not in prev_chunk for u in chunk)

    def test_single_chunk_run_has_no_overlap_duplication(self):
        units = [make_unit(50), make_unit(50)]
        chunks = pack_units(units, target=600, hard_max=800, min_tokens=120, overlap=80, count_tokens=WORD_COUNT)
        assert len(chunks) == 1
        assert len(chunks[0]) == 2
