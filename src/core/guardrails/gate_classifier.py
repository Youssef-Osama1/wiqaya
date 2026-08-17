from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.core.schemas import GateDecision

SYSTEM_PROMPT = (
    "You are the input gate for Wiqaya, a clinical decision support assistant that answers "
    "questions ONLY from WHO and NICE hypertension guidelines. Classify the user's question:\n"
    "- ALLOW: a legitimate in-scope question about hypertension diagnosis, treatment, or management.\n"
    "- CAUTION: in-scope, but asks for personal medical advice (e.g. their own dosing/diagnosis) "
    "rather than general guideline information.\n"
    "- REFUSE: out of scope (not about hypertension), a medical emergency, or otherwise unsafe to answer.\n"
    "Give a short one-sentence reason."
)


class ClassifierVerdict(BaseModel):
    verdict: Literal["ALLOW", "CAUTION", "REFUSE"]
    reason: str


def classify_gate(llm: BaseChatModel, query: str) -> GateDecision:
    structured_llm = llm.with_structured_output(ClassifierVerdict)
    result = structured_llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=query)])
    return GateDecision(verdict=result.verdict, reason=result.reason, triggered_by="classifier")
