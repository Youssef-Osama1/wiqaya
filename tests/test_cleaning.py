from src.core.ingestion.cleaning import clean_page_text, extract_raw_pages


class TestExtractRawPages:
    def test_who_page_count_is_61(self):
        pages = extract_raw_pages("who_hypertension")
        assert len(pages) == 61

    def test_nice_page_count_is_52(self):
        pages = extract_raw_pages("nice_ng136")
        assert len(pages) == 52

    def test_page_numbers_are_1_indexed_and_sequential(self):
        pages = extract_raw_pages("nice_ng136")
        assert [p for p, _ in pages] == list(range(1, 53))


class TestCleanWhoPage:
    def _raw_page_26(self) -> str:
        pages = dict(extract_raw_pages("who_hypertension"))
        return pages[26]

    def test_strips_allcaps_header_line(self):
        cleaned, _ = clean_page_text("who_hypertension", self._raw_page_26())
        assert "GUIDELINE FOR THE PHARMACOLOGICAL TREATMENT OF HYPERTENSION IN ADULTS" not in cleaned.upper()

    def test_extracts_printed_page_number(self):
        _, printed_page = clean_page_text("who_hypertension", self._raw_page_26())
        assert printed_page == 14

    def test_known_text_survives_cleaning(self):
        cleaned, _ = clean_page_text("who_hypertension", self._raw_page_26())
        assert "Evidence and rationale" in cleaned
        assert "combination therapy" in cleaned

    def test_normalizes_nbsp(self):
        cleaned, _ = clean_page_text("who_hypertension", self._raw_page_26())
        assert "\xa0" not in cleaned


class TestCleanNicePage:
    def _raw_page(self, page_number: int) -> str:
        pages = dict(extract_raw_pages("nice_ng136"))
        return pages[page_number]

    def test_strips_copyright_footer(self):
        cleaned, _ = clean_page_text("nice_ng136", self._raw_page(21))
        assert "© NICE" not in cleaned
        assert "notice-of-rights" not in cleaned

    def test_strips_page_of_total_footer(self):
        cleaned, _ = clean_page_text("nice_ng136", self._raw_page(21))
        assert "Page 21 of" not in cleaned
        lines = [line.strip() for line in cleaned.splitlines()]
        assert "52" not in lines

    def test_strips_repeated_title_footer_line(self):
        cleaned, _ = clean_page_text("nice_ng136", self._raw_page(21))
        assert "Hypertension in adults: diagnosis and management (NG136)" not in cleaned

    def test_extracts_printed_page_number(self):
        _, printed_page = clean_page_text("nice_ng136", self._raw_page(21))
        assert printed_page == 21

    def test_known_recommendation_text_survives_cleaning(self):
        cleaned, _ = clean_page_text("nice_ng136", self._raw_page(21))
        assert "1.4.39" in cleaned
        assert "bendroflumethiazide" in cleaned

    def test_normalizes_nbsp(self):
        cleaned, _ = clean_page_text("nice_ng136", self._raw_page(20))
        assert "\xa0" not in cleaned
