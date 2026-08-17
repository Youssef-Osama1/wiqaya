from fastapi import APIRouter, HTTPException, Request

from src.controllers.RetrievalController import RetrievalController
from src.core.schemas import RetrievalResult
from src.helpers.config import get_settings
from src.routes.schemas.nlp import SearchRequest
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
