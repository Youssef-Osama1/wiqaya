import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.controllers.AnswerController import AnswerController
from src.controllers.EvaluationController import EvaluationController
from src.controllers.GateController import GateController
from src.controllers.RetrievalController import RetrievalController
from src.core.evaluation.golden import load_golden_set
from src.core.registry import all_doc_specs
from src.helpers.config import get_settings
from src.routes.evaluation import DEFAULT_E2E_K, DEFAULT_E2E_MODE
from src.stores.bm25_factory import build_bm25_retriever
from src.stores.embedding_factory import get_embeddings
from src.stores.llm_factory import get_llm
from src.stores.vectordb_factory import get_vectordb


class RateLimitedAnswerer:
    def __init__(self, inner, delay: float):
        self.inner = inner
        self.delay = delay

    def answer(self, query, mode, k):
        result = self.inner.answer(query, mode, k)
        print(f"  -> gate={result.gate.verdict} confidence={result.final.confidence}", flush=True)
        if self.delay:
            time.sleep(self.delay)
        return result


def main(delay: float, mode: str, k: int) -> None:
    settings = get_settings()
    embeddings = get_embeddings(settings)
    vectorstore = get_vectordb(settings, embeddings)
    bm25 = build_bm25_retriever([spec.doc_key for spec in all_doc_specs()], k=max(k, settings.DEFAULT_TOP_K))
    llm = get_llm(settings)

    retrieval_controller = RetrievalController(settings, vectorstore, bm25)
    gate_controller = GateController(llm)
    answer_controller = AnswerController(settings, gate_controller, retrieval_controller, llm)
    answerer = RateLimitedAnswerer(answer_controller, delay=delay)
    eval_controller = EvaluationController(answerer)

    golden = load_golden_set(Path(__file__).resolve().parent / "golden.jsonl")
    print(f"Loaded {len(golden)} golden questions, mode={mode} k={k} delay={delay}s", flush=True)

    report = eval_controller.evaluate_e2e(golden, mode=mode, k=k)

    runs_dir = Path(__file__).resolve().parent / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = runs_dir / f"e2e_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2))
    print("Saved to", out_path, flush=True)

    print(
        f"\nprecision@{k}={report['precision_at_k']:.3f} recall@{k}={report['recall_at_k']:.3f} "
        f"mrr={report['mrr']:.3f} (n={report['n_questions_scored']})"
    )
    print(
        f"citation_accuracy={report['citation_accuracy']:.3f} "
        f"unsupported_claim_rate={report['unsupported_claim_rate']:.3f} "
        f"refusal_correctness={report['refusal_correctness']:.3f}"
    )
    print("\ncategory breakdown:")
    for category, stats in report["category_breakdown"].items():
        print(f"  {category}: {stats['correct']}/{stats['count']}")

    if report["failures"]:
        print(f"\n{len(report['failures'])} failure(s):")
        for f in report["failures"]:
            print(
                f"  {f['qid']} ({f['category']}): expected={f['expected_behavior']} "
                f"actual_gate={f['actual_gate_verdict']} actual_confidence={f['actual_confidence']!r}"
            )
    else:
        print("\nno failures")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=15.0, help="seconds to sleep after each answer() call")
    parser.add_argument("--mode", type=str, default=DEFAULT_E2E_MODE)
    parser.add_argument("--k", type=int, default=DEFAULT_E2E_K)
    args = parser.parse_args()
    main(args.delay, args.mode, args.k)
