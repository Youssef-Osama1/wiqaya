from fastapi import APIRouter, HTTPException

from src.controllers.IngestionController import IngestionController
from src.core.registry import all_doc_specs
from src.helpers.config import get_settings
from src.routes.schemas.data import IngestRequest, IngestResponse, IngestResult

router = APIRouter(prefix="/api/v1/data", tags=["data"])


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    settings = get_settings()
    doc_keys = request.doc_keys or [spec.doc_key for spec in all_doc_specs()]
    controller = IngestionController(settings)

    results = []
    for doc_key in doc_keys:
        try:
            result = controller.ingest(
                doc_key,
                target_tokens=request.target_tokens,
                hard_max_tokens=request.hard_max_tokens,
                min_tokens=request.min_tokens,
                overlap_tokens=request.overlap_tokens,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown doc_key: {doc_key!r}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ingestion failed for {doc_key!r}: {e}")

        results.append(
            IngestResult(
                doc_key=result.doc_key,
                chunk_count=result.chunk_count,
                indexed_vector_count=result.indexed_vector_count,
                pages_path=str(result.pages_path),
                chunks_path=str(result.chunks_path),
            )
        )

    return IngestResponse(results=results)
