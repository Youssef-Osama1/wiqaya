import json
from pathlib import Path

from src.core.schemas import Chunk, GoldenQuestion

DEFAULT_CHUNKS_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


def load_golden_set(path: Path) -> list[GoldenQuestion]:
    questions = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(GoldenQuestion.model_validate_json(line))
    return questions


def load_chunks_by_id(doc_keys: list[str], chunks_dir: Path = DEFAULT_CHUNKS_DIR) -> dict[str, Chunk]:
    chunks_by_id: dict[str, Chunk] = {}
    for doc_key in doc_keys:
        chunks_path = chunks_dir / f"{doc_key}_chunks.jsonl"
        with chunks_path.open(encoding="utf-8") as f:
            for line in f:
                chunk = Chunk.model_validate_json(line)
                chunks_by_id[chunk.metadata.chunk_id] = chunk
    return chunks_by_id


def validate_golden_set(questions: list[GoldenQuestion], chunks_by_id: dict[str, Chunk]) -> list[str]:
    errors: list[str] = []
    for q in questions:
        for chunk_id in q.relevant_chunk_ids:
            if chunk_id not in chunks_by_id:
                errors.append(f"{q.qid}: relevant_chunk_id {chunk_id!r} not found in corpus")
        for anchor in q.anchors:
            chunk = chunks_by_id.get(anchor.chunk_id)
            if chunk is None:
                errors.append(f"{q.qid}: anchor chunk_id {anchor.chunk_id!r} not found in corpus")
            elif anchor.anchor_text not in chunk.text:
                errors.append(
                    f"{q.qid}: anchor_text {anchor.anchor_text!r} not found verbatim in chunk {anchor.chunk_id!r}"
                )
    return errors
