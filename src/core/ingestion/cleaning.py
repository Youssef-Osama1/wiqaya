import re
from typing import Callable, Optional

import pymupdf

from src.core.registry import get_doc_spec

_WHO_HEADER = "GUIDELINE FOR THE PHARMACOLOGICAL TREATMENT OF HYPERTENSION IN ADULTS"

_NICE_TITLE_FOOTER = "Hypertension in adults: diagnosis and management (NG136)"
_NICE_COPYRIGHT_LINE1_RE = re.compile(
    r"^©\s*NICE\s+\d{4}\.\s*All rights reserved\.\s*Subject to Notice of rights"
)
_NICE_COPYRIGHT_LINE2_RE = re.compile(r"^conditions#notice-of-rights\)\.?$")
_NICE_PAGE_OF_RE = re.compile(r"^Page (\d+) of$")
_NICE_TOTAL_PAGES = "52"


def extract_raw_pages(doc_key: str) -> list[tuple[int, str]]:
    spec = get_doc_spec(doc_key)
    doc = pymupdf.open(spec.path)
    try:
        return [(i + 1, doc[i].get_text()) for i in range(len(doc))]
    finally:
        doc.close()


def _normalize_nbsp(text: str) -> str:
    return text.replace("\xa0", " ")


def _clean_who_page(raw_text: str) -> tuple[str, Optional[int]]:
    text = _normalize_nbsp(raw_text)
    lines = text.split("\n")
    printed_page: Optional[int] = None
    kept: list[str] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue
        if stripped.casefold() == _WHO_HEADER.casefold():
            continue
        is_last_nonempty = not any(l.strip() for l in lines[idx + 1 :])
        if is_last_nonempty:
            if re.fullmatch(r"\d+", stripped):
                printed_page = int(stripped)
                continue
            if re.fullmatch(r"[ivxlcdm]+", stripped, re.IGNORECASE):
                continue
        kept.append(line)
    return "\n".join(kept).strip(), printed_page


def _clean_nice_page(raw_text: str) -> tuple[str, Optional[int]]:
    text = _normalize_nbsp(raw_text)
    printed_page: Optional[int] = None
    kept: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == _NICE_TITLE_FOOTER:
            continue
        if _NICE_COPYRIGHT_LINE1_RE.match(stripped):
            continue
        if _NICE_COPYRIGHT_LINE2_RE.match(stripped):
            continue
        page_of_match = _NICE_PAGE_OF_RE.match(stripped)
        if page_of_match:
            printed_page = int(page_of_match.group(1))
            continue
        if stripped == _NICE_TOTAL_PAGES:
            continue
        kept.append(line)
    return "\n".join(kept).strip(), printed_page


_CLEANERS: dict[str, Callable[[str], tuple[str, Optional[int]]]] = {
    "who_hypertension": _clean_who_page,
    "nice_ng136": _clean_nice_page,
}


def clean_page_text(doc_key: str, raw_text: str) -> tuple[str, Optional[int]]:
    return _CLEANERS[doc_key](raw_text)
