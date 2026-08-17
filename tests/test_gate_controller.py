from src.controllers.GateController import GateController
from src.core.guardrails.gate_classifier import ClassifierVerdict
from src.core.schemas import GateDecision


class FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class FakeLlm:
    def __init__(self, result):
        self._result = result
        self.invoked = False

    def with_structured_output(self, _schema):
        self.invoked = True
        return FakeStructuredRunnable(self._result)


class TestGateController:
    def test_rule_match_short_circuits_and_never_calls_the_llm(self):
        llm = FakeLlm(ClassifierVerdict(verdict="ALLOW", reason="unused"))
        controller = GateController(llm)
        decision = controller.evaluate("How do I perform CPR on someone having a heart attack?")
        assert decision.verdict == "REFUSE"
        assert decision.triggered_by == "emergency_symptoms"
        assert llm.invoked is False

    def test_no_rule_match_falls_through_to_classifier(self):
        llm = FakeLlm(ClassifierVerdict(verdict="ALLOW", reason="in-scope"))
        controller = GateController(llm)
        decision = controller.evaluate("Is a blood pressure reading of 135 over 88 too high?")
        assert decision == GateDecision(verdict="ALLOW", reason="in-scope", triggered_by="classifier")
        assert llm.invoked is True
