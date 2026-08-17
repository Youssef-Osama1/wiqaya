import re
from typing import Optional

from src.core.schemas import GateDecision

HYPERTENSION_CONTEXT = re.compile(
    r"\b(blood pressure|hypertension|antihypertensive|systolic|diastolic)\b", re.IGNORECASE
)

EMERGENCY_SYMPTOMS = re.compile(
    r"\b(cpr|heart attack|chest pain|stroke|slurred speech|facial droop|"
    r"can'?t breathe|difficulty breathing|unconscious|seizure)\b",
    re.IGNORECASE,
)

OUT_OF_DOMAIN_TOPICS = re.compile(
    r"\b(diabetes|metformin|migraine|painkiller)\b", re.IGNORECASE
)

PERSONAL_DOSING_PHRASE = re.compile(
    r"\b(how much (should|can) i take|what dose|should i take|"
    r"increase my (dose|dosage)|is it safe (for me )?to take)\b",
    re.IGNORECASE,
)


def apply_gate_rules(query: str) -> Optional[GateDecision]:
    if EMERGENCY_SYMPTOMS.search(query):
        return GateDecision(
            verdict="REFUSE",
            reason="This question describes a potential medical emergency — call emergency services immediately.",
            triggered_by="emergency_symptoms",
        )

    if OUT_OF_DOMAIN_TOPICS.search(query) and not HYPERTENSION_CONTEXT.search(query):
        return GateDecision(
            verdict="REFUSE",
            reason="This system covers hypertension guidelines only and cannot answer questions about other conditions.",
            triggered_by="out_of_domain",
        )

    if HYPERTENSION_CONTEXT.search(query) and PERSONAL_DOSING_PHRASE.search(query):
        return GateDecision(
            verdict="CAUTION",
            reason="This looks like a personal medication question — general guideline information only, not a prescription.",
            triggered_by="personal_dosing",
        )

    return None
