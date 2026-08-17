from langchain_cohere import ChatCohere
from langchain_openai import ChatOpenAI

from src.stores.llm_factory import get_llm
from tests.conftest import make_settings


class TestGetLlm:
    def test_openai_backend_returns_chat_openai_with_configured_model_and_temperature(self):
        settings = make_settings(GENERATION_BACKEND="openai", GENERATION_MODEL_ID="gpt-4o-mini", GENERATION_TEMPERATURE=0.0)
        llm = get_llm(settings)
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o-mini"
        assert llm.temperature == 0.0

    def test_cohere_backend_returns_chat_cohere_with_configured_model(self):
        settings = make_settings(GENERATION_BACKEND="cohere", GENERATION_MODEL_ID="command-r")
        llm = get_llm(settings)
        assert isinstance(llm, ChatCohere)
        assert llm.model == "command-r"

    def test_temperature_zero_is_respected_not_treated_as_falsy(self):
        settings = make_settings(GENERATION_BACKEND="openai", GENERATION_TEMPERATURE=0.0)
        llm = get_llm(settings)
        assert llm.temperature == 0.0
