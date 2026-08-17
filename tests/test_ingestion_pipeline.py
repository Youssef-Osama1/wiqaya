import json

from src.core.ingestion.pipeline import build_cleaned_pages, write_pages_jsonl
from src.core.schemas import CleanedPage


class TestBuildCleanedPages:
    def test_produces_one_page_per_pdf_page(self):
        pages = build_cleaned_pages("nice_ng136")
        assert len(pages) == 52

    def test_mandatory_fields_non_empty_on_every_page(self):
        blank_pages = {2, 12, 61}
        pages = build_cleaned_pages("who_hypertension")
        for page in pages:
            assert page.doc_key == "who_hypertension"
            assert page.page_number > 0
            assert page.section_title != ""
            if page.page_number not in blank_pages:
                assert page.text != ""

    def test_known_recommendation_survives_with_correct_metadata(self):
        pages = build_cleaned_pages("nice_ng136")
        page21 = next(p for p in pages if p.page_number == 21)
        assert "1.4.39" in page21.text
        assert "1.4.39" in page21.recommendation_ids
        assert page21.printed_page == 21

    def test_who_printed_page_offset_survives(self):
        pages = build_cleaned_pages("who_hypertension")
        page26 = next(p for p in pages if p.page_number == 26)
        assert page26.printed_page == 14

    def test_repeated_who_header_line_removed_from_every_page(self):
        header = "guideline for the pharmacological treatment of hypertension in adults"
        for page in build_cleaned_pages("who_hypertension"):
            first_line = page.text.split("\n", 1)[0].strip().casefold()
            assert first_line != header

    def test_nice_footer_noise_removed_from_every_page(self):
        for page in build_cleaned_pages("nice_ng136"):
            assert "© NICE" not in page.text
            assert "notice-of-rights" not in page.text
            lines = [line.strip() for line in page.text.splitlines()]
            assert not any(line.startswith("Page ") and line.endswith(" of") for line in lines)


class TestWritePagesJsonl:
    def test_writes_one_json_line_per_page(self, tmp_path):
        out_path = write_pages_jsonl("nice_ng136", tmp_path)
        lines = out_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 52

    def test_each_line_round_trips_as_cleaned_page(self, tmp_path):
        out_path = write_pages_jsonl("nice_ng136", tmp_path)
        first_line = out_path.read_text(encoding="utf-8").strip().split("\n")[0]
        page = CleanedPage.model_validate(json.loads(first_line))
        assert page.doc_key == "nice_ng136"

    def test_output_filename_matches_doc_key_convention(self, tmp_path):
        out_path = write_pages_jsonl("who_hypertension", tmp_path)
        assert out_path.name == "who_hypertension_pages.jsonl"
