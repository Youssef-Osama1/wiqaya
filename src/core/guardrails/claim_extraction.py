from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.core.schemas import ClaimSupport

SYSTEM_PROMPT = (
    "You extract factual claims from a clinical recommendation and check whether each is "
    "supported by the provided retrieved guideline text. A claim is supported only if the "
    "retrieved text states it or something that directly implies it — do not use outside "
    "medical knowledge. List every distinct factual claim in the recommendation. If there are "
    "none, return an empty list."
)


class ClaimExtractionResult(BaseModel):
    claims: list[ClaimSupport]


def extract_claim_support(llm: BaseChatModel, recommendation: str, retrieved_text: str) -> list[ClaimSupport]:
    structured_llm = llm.with_structured_output(ClaimExtractionResult)
    prompt = f"Recommendation:\n{recommendation}\n\nRetrieved guideline text:\n{retrieved_text}"
    result = structured_llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return result.claims
