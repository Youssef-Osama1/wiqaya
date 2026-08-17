import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pymupdf
import tiktoken

from src.core.chunking.chunk_ids import compute_chunk_id
from src.core.ingestion.cleaning import (
    _NICE_COPYRIGHT_LINE1_RE,
    _NICE_PAGE_OF_RE,
    _NICE_TITLE_FOOTER,
    _NICE_TOTAL_PAGES,
    _normalize_nbsp,
)
from src.core.ingestion.pipeline import build_cleaned_pages
from src.core.ingestion.sections import build_section_map
from src.core.registry import get_doc_spec
from src.core.schemas import Chunk, ChunkMetadata

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_REC_START_RE = re.compile(r"^\d+\.\d+\.\d+\s")
_ERA_TAG_RE = re.compile(r"\[\d{4}(?:,\s*amended\s+\d{4})?\]")
_NICE_COPYRIGHT_BLOCK_RE = re.compile(
    r"^©\s*NICE\s+\d{4}\.\s*All rights reserved\..*notice-of-rights\)\.?$",
    re.IGNORECASE | re.DOTALL,
)

_CROSS_REFERENCE_RE = re.compile(r"NICE'?s?\s+guideline on\b|nice\.org\.uk/guidance/(?!ng136\b)", re.IGNORECASE)

_TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_TOKEN_ENCODING.encode(text))


def has_cross_reference(text: str) -> bool:
    return bool(_CROSS_REFERENCE_RE.search(text))


def _is_nice_noise_block(text: str) -> bool:
    stripped = text.strip()
    if stripped == _NICE_TITLE_FOOTER:
        return True
    if _NICE_COPYRIGHT_LINE1_RE.match(stripped) or _NICE_COPYRIGHT_BLOCK_RE.match(stripped):
        return True
    if _NICE_PAGE_OF_RE.match(stripped):
        return True
    if stripped == _NICE_TOTAL_PAGES:
        return True
    return False


@dataclass
class RawUnit:
    text: str
    page_number: int
    page_end: int
    recommendation_id: Optional[str] = None
    is_atomic: bool = False


def extract_nice_raw_units() -> list[RawUnit]:
    spec = get_doc_spec("nice_ng136")
    doc = pymupdf.open(spec.path)
    try:
        page_blocks: list[tuple[int, str]] = []
        for i in range(len(doc)):
            blocks = sorted(doc[i].get_text("blocks"), key=lambda b: b[1])
            for block in blocks:
                text = _normalize_nbsp(block[4]).strip()
                if text and not _is_nice_noise_block(text):
                    page_blocks.append((i + 1, text))
    finally:
        doc.close()

    units: list[RawUnit] = []
    active_parts: list[str] = []
    active_rec_id: Optional[str] = None
    active_start_page: Optional[int] = None

    def flush_active(end_page: int) -> None:
        nonlocal active_parts, active_rec_id, active_start_page
        units.append(
            RawUnit(
                text="\n".join(active_parts),
                page_number=active_start_page,
                page_end=end_page,
                recommendation_id=active_rec_id,
                is_atomic=True,
            )
        )
        active_parts, active_rec_id, active_start_page = [], None, None

    for page_number, text in page_blocks:
        if _REC_START_RE.match(text):
            if active_parts:
                flush_active(page_number)
            active_parts = [text]
            active_rec_id = text.split()[0]
            active_start_page = page_number
            if _ERA_TAG_RE.search("\n".join(active_parts)):
                flush_active(page_number)
            continue

        if active_parts:
            active_parts.append(text)
            if _ERA_TAG_RE.search("\n".join(active_parts)):
                flush_active(page_number)
            continue

        units.append(RawUnit(text=text, page_number=page_number, page_end=page_number))

    if active_parts:
        flush_active(active_start_page)

    return units


def extract_who_raw_units() -> list[RawUnit]:
    units: list[RawUnit] = []
    for page in build_cleaned_pages("who_hypertension"):
        if not page.text:
            continue
        for sentence in _SENTENCE_SPLIT_RE.split(page.text):
            sentence = sentence.strip()
            if sentence:
                units.append(RawUnit(text=sentence, page_number=page.page_number, page_end=page.page_number))
    return units


@dataclass
class Unit:
    text: str
    page_number: int
    page_end: int
    section_title: str
    section_path: list[str] = field(default_factory=list)
    recommendation_id: Optional[str] = None
    is_atomic: bool = False


def _take_trailing_overlap(units: list[Unit], overlap_tokens: int, count_tokens: Callable[[str], int]) -> list[Unit]:
    trailing: list[Unit] = []
    total = 0
    for unit in reversed(units):
        if unit.is_atomic:
            break
        unit_tokens = count_tokens(unit.text)
        if total + unit_tokens > overlap_tokens:
            break
        trailing.insert(0, unit)
        total += unit_tokens
    return trailing


def pack_units(
    units: list[Unit],
    target: int,
    hard_max: int,
    min_tokens: int,
    overlap: int,
    count_tokens: Callable[[str], int],
) -> list[list[Unit]]:
    if not units:
        return []

    chunks: list[list[Unit]] = []
    current: list[Unit] = []
    current_tokens = 0
    has_new_content = False

    def close_chunk(seed_overlap: bool) -> None:
        nonlocal current, current_tokens, has_new_content
        chunks.append(current)
        current = _take_trailing_overlap(current, overlap, count_tokens) if seed_overlap else []
        current_tokens = sum(count_tokens(u.text) for u in current)
        has_new_content = False

    for unit in units:
        unit_tokens = count_tokens(unit.text)
        oversized_atomic = unit.is_atomic and unit_tokens > hard_max

        if current and current_tokens + unit_tokens > hard_max:
            close_chunk(seed_overlap=not oversized_atomic)

        current.append(unit)
        current_tokens += unit_tokens
        has_new_content = True

        if current_tokens >= target:
            close_chunk(seed_overlap=True)

    if current and has_new_content:
        chunks.append(current)

    if len(chunks) > 1:
        last_tokens = sum(count_tokens(u.text) for u in chunks[-1])
        previous_is_pure_atomic = all(u.is_atomic for u in chunks[-2])
        if last_tokens < min_tokens and not previous_is_pure_atomic:
            fragment = chunks.pop()
            new_units = [u for u in fragment if u not in chunks[-1]]
            chunks[-1].extend(new_units)

    return chunks


def _group_into_section_runs(raw_units: list[RawUnit], section_map: dict) -> list[list[Unit]]:
    runs: list[list[Unit]] = []
    current_run: list[Unit] = []
    current_title: Optional[str] = None
    for raw in raw_units:
        info = section_map[raw.page_number]
        unit = Unit(
            text=raw.text,
            page_number=raw.page_number,
            page_end=raw.page_end,
            section_title=info.section_title,
            section_path=info.section_path,
            recommendation_id=raw.recommendation_id,
            is_atomic=raw.is_atomic,
        )
        if current_run and unit.section_title != current_title:
            runs.append(current_run)
            current_run = []
        current_run.append(unit)
        current_title = unit.section_title
    if current_run:
        runs.append(current_run)
    return runs


def chunk_document(
    doc_key: str,
    target_tokens: int = 600,
    hard_max_tokens: int = 800,
    min_tokens: int = 120,
    overlap_tokens: int = 80,
) -> list[Chunk]:
    spec = get_doc_spec(doc_key)
    raw_units = extract_nice_raw_units() if doc_key == "nice_ng136" else extract_who_raw_units()
    section_map = build_section_map(doc_key)
    printed_pages = {p.page_number: p.printed_page for p in build_cleaned_pages(doc_key)}

    runs = _group_into_section_runs(raw_units, section_map)

    chunks: list[Chunk] = []
    for run in runs:
        for group in pack_units(run, target_tokens, hard_max_tokens, min_tokens, overlap_tokens, count_tokens):
            text = "\n".join(u.text for u in group)
            page_number = min(u.page_number for u in group)
            page_end = max(u.page_end for u in group)
            recommendation_ids = sorted(
                {u.recommendation_id for u in group if u.recommendation_id},
                key=lambda rid: tuple(int(p) for p in rid.split(".")),
            )
            first = group[0]
            metadata = ChunkMetadata(
                document_name=spec.document_name,
                page_number=page_number,
                section_title=first.section_title,
                chunk_id=compute_chunk_id(doc_key, page_number, text),
                source_url=spec.source_url,
                doc_key=doc_key,
                section_path=first.section_path,
                page_end=page_end if page_end != page_number else None,
                token_count=count_tokens(text),
                recommendation_ids=recommendation_ids,
                has_cross_reference=has_cross_reference(text),
                printed_page=printed_pages.get(page_number),
            )
            chunks.append(Chunk(text=text, metadata=metadata))
    return chunks


DEFAULT_CHUNKS_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


def write_chunks_to_jsonl(chunks: list[Chunk], doc_key: str, output_dir: Path = DEFAULT_CHUNKS_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{doc_key}_chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.model_dump_json() + "\n")
    return out_path


def write_chunks_jsonl(
    doc_key: str,
    output_dir: Path = DEFAULT_CHUNKS_OUTPUT_DIR,
    target_tokens: int = 600,
    hard_max_tokens: int = 800,
    min_tokens: int = 120,
    overlap_tokens: int = 80,
) -> Path:
    chunks = chunk_document(doc_key, target_tokens, hard_max_tokens, min_tokens, overlap_tokens)
    return write_chunks_to_jsonl(chunks, doc_key, output_dir)
