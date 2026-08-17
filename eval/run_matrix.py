import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.controllers.EvaluationController import EvaluationController
from src.controllers.RetrievalController import RetrievalController
from src.core.evaluation.golden import load_golden_set
from src.core.evaluation.rate_limiting import RateLimitedSearcher
from src.core.registry import all_doc_specs
from src.helpers.config import get_settings
from src.routes.evaluation import DEFAULT_KS, DEFAULT_MODES
from src.stores.bm25_factory import build_bm25_retriever
from src.stores.embedding_factory import get_embeddings
from src.stores.vectordb_factory import get_vectordb


def main(delay: float) -> None:
    settings = get_settings()
    vectorstore = get_vectordb(settings, get_embeddings(settings))
    bm25 = build_bm25_retriever([spec.doc_key for spec in all_doc_specs()], k=max(DEFAULT_KS))
    retrieval_controller = RetrievalController(settings, vectorstore, bm25)
    searcher = RateLimitedSearcher(retrieval_controller, delay=delay)
    eval_controller = EvaluationController(searcher)

    golden = load_golden_set(Path(__file__).resolve().parent / "golden.jsonl")
    print(f"Loaded {len(golden)} golden questions", flush=True)

    report = eval_controller.evaluate_retrieval(golden, modes=DEFAULT_MODES, ks=DEFAULT_KS)

    runs_dir = Path(__file__).resolve().parent / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = runs_dir / f"retrieval_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2))
    print("Saved to", out_path, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=6.5, help="seconds between rate-limited search calls")
    args = parser.parse_args()
    main(args.delay)
