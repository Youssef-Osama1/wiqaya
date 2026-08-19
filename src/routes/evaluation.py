import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from src.controllers.AnswerController import AnswerController
from src.controllers.EvaluationController import EvaluationController
from src.controllers.GateController import GateController
from src.controllers.RetrievalController import RetrievalController
from src.core.evaluation.golden import load_golden_set
from src.core.evaluation.rate_limiting import RateLimitedAnswerer, RateLimitedSearcher
from src.helpers.config import get_settings
from src.stores.vectordb_factory import get_vectordb

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "eval" / "golden.jsonl"
RUNS_DIR = Path(__file__).resolve().parents[2] / "eval" / "runs"

DEFAULT_MODES = ["semantic", "bm25", "hybrid", "hybrid_rerank"]
DEFAULT_KS = [3, 5, 10]

DEFAULT_E2E_MODE = "hybrid_rerank"
DEFAULT_E2E_K = 5

# same defaults as eval/run_matrix.py / eval/run_e2e.py — a Cohere trial key is
# limited to 10 calls/min, and these routes make far more calls than that if
# triggered live from the Dashboard without pacing them out
LIVE_RETRIEVAL_EVAL_DELAY = 6.5
LIVE_E2E_EVAL_DELAY = 15.0


def _latest_report(prefix: str) -> dict:
    if not RUNS_DIR.exists():
        raise HTTPException(status_code=404, detail=f"No saved {prefix} evaluation yet - run one first.")
    candidates = sorted(RUNS_DIR.glob(f"{prefix}_*.json"))
    if not candidates:
        raise HTTPException(status_code=404, detail=f"No saved {prefix} evaluation yet - run one first.")
    newest = candidates[-1]
    try:
        report = json.loads(newest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Saved {prefix} report could not be read: {e}")
    return {"report_path": str(newest), **report}


@router.get("/retrieval/latest")
def latest_retrieval() -> dict:
    return _latest_report("retrieval")


@router.get("/e2e/latest")
def latest_e2e() -> dict:
    return _latest_report("e2e")


@router.post("/retrieval")
def evaluate_retrieval(req: Request) -> dict:
    settings = get_settings()
    try:
        vectorstore = get_vectordb(settings, req.app.state.embeddings)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Vector store not ready - run POST /api/v1/data/ingest first: {e}",
        )
    retrieval_controller = RetrievalController(settings, vectorstore, req.app.state.bm25_retriever)
    searcher = RateLimitedSearcher(retrieval_controller, delay=LIVE_RETRIEVAL_EVAL_DELAY)
    eval_controller = EvaluationController(searcher)

    golden_questions = load_golden_set(GOLDEN_PATH)
    report = eval_controller.evaluate_retrieval(golden_questions, modes=DEFAULT_MODES, ks=DEFAULT_KS)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RUNS_DIR / f"retrieval_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {"report_path": str(out_path), **report}


@router.post("/e2e")
def evaluate_e2e(req: Request, mode: str = DEFAULT_E2E_MODE, k: int = DEFAULT_E2E_K) -> dict:
    settings = get_settings()

    try:
        vectorstore = get_vectordb(settings, req.app.state.embeddings)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Vector store not ready - run POST /api/v1/data/ingest first: {e}",
        )

    llm = req.app.state.llm
    retrieval_controller = RetrievalController(settings, vectorstore, req.app.state.bm25_retriever)
    gate_controller = GateController(llm)
    answer_controller = AnswerController(settings, gate_controller, retrieval_controller, llm)
    answerer = RateLimitedAnswerer(answer_controller, delay=LIVE_E2E_EVAL_DELAY)
    eval_controller = EvaluationController(answerer)

    golden_questions = load_golden_set(GOLDEN_PATH)
    report = eval_controller.evaluate_e2e(golden_questions, mode=mode, k=k)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RUNS_DIR / f"e2e_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {"report_path": str(out_path), **report}
