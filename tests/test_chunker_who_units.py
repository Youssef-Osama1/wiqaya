from src.core.chunking.chunker import extract_who_raw_units


class TestExtractWhoRawUnits:
    def test_produces_units_for_every_nonblank_page(self):
        units = extract_who_raw_units()
        pages_with_units = {u.page_number for u in units}
        assert pages_with_units == set(range(1, 62)) - {2, 12, 61}

    def test_units_are_never_atomic(self):
        units = extract_who_raw_units()
        assert all(u.is_atomic is False for u in units)

    def test_units_are_sentence_sized_not_whole_pages(self):
        units = extract_who_raw_units()
        page26_units = [u for u in units if u.page_number == 26]
        assert len(page26_units) > 1

    def test_known_text_survives_in_some_unit(self):
        units = extract_who_raw_units()
        joined = " ".join(u.text for u in units if u.page_number == 26)
        assert "combination therapy" in joined
