from src.core.ingestion.sections import build_section_map


class TestNiceSectionMap:
    def test_covers_every_page(self):
        section_map = build_section_map("nice_ng136")
        assert set(section_map.keys()) == set(range(1, 53))

    def test_page_21_recommendation_ids_include_known_rec(self):
        section_map = build_section_map("nice_ng136")
        assert "1.4.39" in section_map[21].recommendation_ids

    def test_bare_rec_bookmarks_never_become_section_titles(self):
        section_map = build_section_map("nice_ng136")
        for info in section_map.values():
            assert not info.section_title.strip().replace(".", "").isdigit()

    def test_section_title_for_page_5_is_deepest_heading_starting_on_that_page(self):
        section_map = build_section_map("nice_ng136")
        assert section_map[5].section_title == "Training, technique and device maintenance"

    def test_section_path_is_breadcrumb_from_root(self):
        section_map = build_section_map("nice_ng136")
        path = section_map[5].section_path
        assert "Recommendations" in path
        assert "1.1 Measuring blood pressure" in path
        assert path.index("Recommendations") < path.index("1.1 Measuring blood pressure")
        assert path[-1] == "Training, technique and device maintenance"


class TestWhoSectionMap:
    def test_covers_every_page(self):
        section_map = build_section_map("who_hypertension")
        assert set(section_map.keys()) == set(range(1, 62))

    def test_pages_before_first_bookmark_default_to_document_name(self):
        section_map = build_section_map("who_hypertension")
        assert section_map[1].section_title == "WHO Guideline for the Pharmacological Treatment of Hypertension in Adults"

    def test_page_19_section_path_descends_from_recommendations_chapter(self):
        section_map = build_section_map("who_hypertension")
        info = section_map[19]
        assert any("3" in t and "Recommendations" in t for t in info.section_path)
        assert "3.1" in info.section_title

    def test_front_matter_never_becomes_a_phantom_ancestor_of_numbered_chapters(self):
        section_map = build_section_map("who_hypertension")
        info = section_map[19]
        assert "Executive summary" not in info.section_path

    def test_goback_bookmark_never_becomes_a_section_title(self):
        section_map = build_section_map("who_hypertension")
        for info in section_map.values():
            assert info.section_title != "_GoBack"
            assert "_GoBack" not in info.section_path

    def test_figure_caption_bookmarks_never_become_section_titles(self):
        section_map = build_section_map("who_hypertension")
        for info in section_map.values():
            assert not info.section_title.startswith("Fig.")
            assert not any(t.startswith("Fig.") for t in info.section_path)
