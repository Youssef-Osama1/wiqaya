from src.core.chunking.chunker import extract_nice_raw_units


class TestExtractNiceRawUnits:
    def test_short_recommendation_becomes_one_atomic_unit(self):
        units = extract_nice_raw_units()
        rec = next(u for u in units if u.recommendation_id == "1.4.39")
        assert rec.is_atomic is True
        assert rec.page_number == 21
        assert "bendroflumethiazide" in rec.text
        assert rec.text.rstrip().endswith("[2019]")

    def test_recommendation_with_bullet_list_stays_one_atomic_unit(self):
        units = extract_nice_raw_units()
        rec = next(u for u in units if u.recommendation_id == "1.4.41")
        assert rec.is_atomic is True
        assert "CCB" in rec.text
        assert "thiazide-like diuretic" in rec.text
        assert rec.text.rstrip().endswith("[2019]")

    def test_inline_subheading_becomes_its_own_non_atomic_unit(self):
        units = extract_nice_raw_units()
        heading = next(u for u in units if u.text.strip() == "Step 2 treatment")
        assert heading.is_atomic is False
        assert heading.recommendation_id is None
        assert heading.page_number == 21

    def test_no_noise_blocks_leak_into_units(self):
        units = extract_nice_raw_units()
        joined = " ".join(u.text for u in units)
        assert "© NICE" not in joined
        assert "Hypertension in adults: diagnosis and management (NG136)" not in joined

    def test_era_tag_split_across_a_block_boundary_still_closes_the_unit(self):
        units = extract_nice_raw_units()
        rec = next(u for u in units if u.recommendation_id == "1.2.13")
        assert rec.page_end == 9
        assert rec.text.rstrip().endswith("2011]")
        assert "chronic kidney disease" not in rec.text
        assert "Assessing cardiovascular risk" not in rec.text

    def test_consecutive_recommendations_stay_separate_units(self):
        units = extract_nice_raw_units()
        rec_ids = [u.recommendation_id for u in units if u.recommendation_id]
        assert "1.4.39" in rec_ids
        assert "1.4.40" in rec_ids
        assert rec_ids.count("1.4.39") == 1
