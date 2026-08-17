from src.core.guardrails.gate_classifier import classify_gate


class FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class FakeLlm:
    def __init__(self, result):
        self._result = result
        self.last_schema = None

    def with_structured_output(self, schema):
        self.last_schema = schema
        return FakeStructuredRunnable(self._result)


class TestClassifyGate:
    def test_allow_verdict_is_wrapped_into_gate_decision(self):
        from src.core.guardrails.gate_classifier import ClassifierVerdict

        llm = FakeLlm(ClassifierVerdict(verdict="ALLOW", reason="in-scope hypertension question"))
        decision = classify_gate(llm, "What is the target blood pressure for adults?")
        assert decision.verdict == "ALLOW"
        assert decision.reason == "in-scope hypertension question"
        assert decision.triggered_by == "classifier"

    def test_refuse_verdict_is_wrapped_into_gate_decision(self):
        from src.core.guardrails.gate_classifier import ClassifierVerdict

        llm = FakeLlm(ClassifierVerdict(verdict="REFUSE", reason="unrelated to hypertension"))
        decision = classify_gate(llm, "What's the weather today?")
        assert decision.verdict == "REFUSE"
        assert decision.triggered_by == "classifier"

    def test_uses_structured_output_with_classifier_verdict_schema(self):
        from src.core.guardrails.gate_classifier import ClassifierVerdict

        llm = FakeLlm(ClassifierVerdict(verdict="ALLOW", reason="ok"))
        classify_gate(llm, "some question")
        assert llm.last_schema is ClassifierVerdict
