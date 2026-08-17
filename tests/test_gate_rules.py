import json
from pathlib import Path

import pytest

from src.core.guardrails.gate_rules import apply_gate_rules

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "eval" / "golden.jsonl"

RULE_DESIGNED_QIDS = {"O1", "O2", "O3", "O4"}


class TestEmergencyRule:
    def test_cpr_heart_attack_query_is_refused_with_emergency_reason(self):
        decision = apply_gate_rules("How do I perform CPR on someone having a heart attack?")
        assert decision is not None
        assert decision.verdict == "REFUSE"
        assert decision.triggered_by == "emergency_symptoms"
        assert "emergency services" in decision.reason.lower()

    def test_chest_pain_is_case_insensitive(self):
        decision = apply_gate_rules("I have severe CHEST PAIN, what should I do?")
        assert decision is not None
        assert decision.verdict == "REFUSE"
        assert decision.triggered_by == "emergency_symptoms"


class TestOutOfDomainRule:
    def test_diabetes_question_with_no_hypertension_context_is_refused(self):
        decision = apply_gate_rules("What is the recommended first-line treatment for type 2 diabetes?")
        assert decision is not None
        assert decision.verdict == "REFUSE"
        assert decision.triggered_by == "out_of_domain"

    def test_migraine_painkiller_question_is_refused(self):
        decision = apply_gate_rules("What painkiller should I take for a migraine?")
        assert decision is not None
        assert decision.verdict == "REFUSE"
        assert decision.triggered_by == "out_of_domain"

    def test_metformin_dosage_question_is_refused(self):
        decision = apply_gate_rules("What is the standard dosage of metformin for a newly diagnosed patient?")
        assert decision is not None
        assert decision.verdict == "REFUSE"

    def test_diabetes_mentioned_as_hypertension_comorbidity_is_not_rule_refused(self):
        decision = apply_gate_rules("What antihypertensive is preferred for a patient with diabetes and hypertension?")
        assert decision is None


class TestPersonalDosingRule:
    def test_what_bp_medication_should_i_take_is_caution_not_refuse(self):
        decision = apply_gate_rules("What blood pressure medication should I take?")
        assert decision is not None
        assert decision.verdict == "CAUTION"
        assert decision.triggered_by == "personal_dosing"


class TestNoRuleMatchFallsThroughToClassifier:
    def test_plain_in_scope_question_returns_none(self):
        assert apply_gate_rules("Is a blood pressure reading of 135 over 88 too high?") is None

    def test_onset_of_action_question_returns_none(self):
        assert apply_gate_rules("How long does it take for blood pressure medication to start working?") is None

    def test_off_topic_dosage_question_without_a_rule_keyword_returns_none(self):
        assert apply_gate_rules("What is the appropriate insulin dosage for a type 1 diabetic during illness?") is None

    def test_unrelated_first_aid_question_returns_none(self):
        assert apply_gate_rules("How should a broken arm be splinted in the field?") is None

    def test_direct_guideline_question_returns_none(self):
        assert apply_gate_rules("What is the clinic blood pressure target for people aged 80 and over with hypertension?") is None


class TestGoldenSetRegression:
    @pytest.mark.parametrize(
        "question",
        [
            json.loads(line)["question"]
            for line in GOLDEN_PATH.read_text().splitlines()
            if json.loads(line)["category"] == "out_of_scope" and json.loads(line)["qid"] in RULE_DESIGNED_QIDS
        ],
    )
    def test_every_rule_designed_out_of_scope_golden_question_is_rule_refused(self, question):
        decision = apply_gate_rules(question)
        assert decision is not None, f"expected a rule to catch: {question!r}"
        assert decision.verdict == "REFUSE"
