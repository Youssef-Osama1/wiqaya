from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.generation.context import assemble_context
from src.core.schemas import Chunk, GroundedAnswer

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = (
    "You are a clinical guideline summarization assistant for Wiqaya. Answer the question "
    "using ONLY the provided excerpts from WHO and NICE hypertension guidelines below — never "
    "use outside medical knowledge, and never diagnose or prescribe for a specific individual. "
    "Every piece of evidence you cite must be a verbatim quote from one of the excerpts, tagged "
    "with that excerpt's chunk_id. If the excerpts are marked as a cross-reference to guidance "
    "outside this corpus, say so instead of extrapolating what that guidance says. If the "
    "excerpts do not contain enough information to answer, set insufficient_evidence to true "
    "honestly rather than guessing."
)


def generate_grounded_answer(llm: BaseChatModel, query: str, chunks: list[Chunk]) -> GroundedAnswer:
    context = assemble_context(chunks)
    structured_llm = llm.with_structured_output(GroundedAnswer)
    human_prompt = f"Retrieved excerpts:\n{context}\n\nQuestion: {query}"
    return structured_llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_prompt)])
