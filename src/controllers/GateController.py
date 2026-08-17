from langchain_core.language_models.chat_models import BaseChatModel

from src.core.guardrails.gate_classifier import classify_gate
from src.core.guardrails.gate_rules import apply_gate_rules
from src.core.schemas import GateDecision


class GateController:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def evaluate(self, query: str) -> GateDecision:
        rule_decision = apply_gate_rules(query)
        if rule_decision is not None:
            return rule_decision
        return classify_gate(self.llm, query)
