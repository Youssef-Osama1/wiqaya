from fastapi import APIRouter, HTTPException, Request

from src.controllers.AnswerController import AnswerController
from src.controllers.GateController import GateController
from src.controllers.RetrievalController import RetrievalController
from src.core.schemas import AnswerTrace, RetrievalResult
from src.helpers.config import get_settings
from src.routes.schemas.nlp import AnswerRequest, SearchRequest
from src.stores.vectordb_factory import get_vectordb

router = APIRouter(prefix="/api/v1/nlp", tags=["nlp"])


@router.post("/search", response_model=RetrievalResult)
def search(request: SearchRequest, req: Request) -> RetrievalResult:
    settings = get_settings()
    k = request.k or settings.DEFAULT_TOP_K

    try:
        vectorstore = get_vectordb(settings, req.app.state.embeddings)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Vector store not ready — run POST /api/v1/data/ingest first: {e}",
        )

    controller = RetrievalController(settings, vectorstore, req.app.state.bm25_retriever)
    return controller.search(request.query, request.mode, k)


@router.post("/answer", response_model=AnswerTrace)
def answer(request: AnswerRequest, req: Request) -> AnswerTrace:
    settings = get_settings()
    k = request.k or settings.DEFAULT_TOP_K
    llm = req.app.state.llm
    gate_controller = GateController(llm)

    try:
        gate_decision = gate_controller.evaluate(request.query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI backend error while checking the question: {e}")

    retrieval_controller = None
    if gate_decision.verdict != "REFUSE":
        try:
            vectorstore = get_vectordb(settings, req.app.state.embeddings)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Vector store not ready — run POST /api/v1/data/ingest first: {e}",
            )
        retrieval_controller = RetrievalController(settings, vectorstore, req.app.state.bm25_retriever)

    controller = AnswerController(settings, _PrecomputedGate(gate_decision), retrieval_controller, llm)
    try:
        return controller.answer(request.query, mode=request.mode, k=k)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI backend error while generating the answer: {e}")


class _PrecomputedGate:
    def __init__(self, decision):
        self._decision = decision

    def evaluate(self, _query):
        return self._decision
