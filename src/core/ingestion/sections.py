import re
from dataclasses import dataclass, field

import pymupdf

from src.core.registry import get_doc_spec

_NOISE_TITLE_PATTERNS = [
    re.compile(r"^_GoBack$", re.IGNORECASE),
    re.compile(r"^Fig\.?\s", re.IGNORECASE),
]
_BARE_REC_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_NUMERIC_PREFIX_PATTERN = re.compile(r"^\d+(?:\.\d+)*(?=\s|$)")


def _is_noise(title: str) -> bool:
    return any(p.match(title) for p in _NOISE_TITLE_PATTERNS)


def _is_bare_rec(title: str) -> bool:
    return bool(_BARE_REC_PATTERN.fullmatch(title))


def _depth(doc_key: str, title: str, raw_level: int) -> int:
    if doc_key == "who_hypertension":
        match = _NUMERIC_PREFIX_PATTERN.match(title)
        if match:
            return match.group(0).count(".") + 1
    return raw_level


def _rec_sort_key(title: str) -> tuple[int, ...]:
    return tuple(int(part) for part in title.split("."))


@dataclass
class PageSectionInfo:
    section_title: str
    section_path: list[str] = field(default_factory=list)
    recommendation_ids: list[str] = field(default_factory=list)


def build_section_map(doc_key: str) -> dict[int, PageSectionInfo]:
    spec = get_doc_spec(doc_key)
    doc = pymupdf.open(spec.path)
    try:
        toc = doc.get_toc()
        num_pages = len(doc)
    finally:
        doc.close()

    entries: list[tuple[int, int, str]] = []
    for level, raw_title, page in toc:
        title = " ".join(raw_title.split())
        if _is_noise(title):
            continue
        entries.append((page, level, title))
    entries.sort(key=lambda e: e[0])

    rec_ids_by_page: dict[int, list[str]] = {}
    for page, _level, title in entries:
        if _is_bare_rec(title):
            rec_ids_by_page.setdefault(page, []).append(title)

    result: dict[int, PageSectionInfo] = {}
    stack: list[tuple[int, str]] = []
    entry_idx = 0
    for page in range(1, num_pages + 1):
        while entry_idx < len(entries) and entries[entry_idx][0] <= page:
            _, raw_level, title = entries[entry_idx]
            if not _is_bare_rec(title):
                level = _depth(doc_key, title, raw_level)
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, title))
            entry_idx += 1

        if stack:
            section_title = stack[-1][1]
            section_path = [title for _, title in stack]
        else:
            section_title = spec.document_name
            section_path = [spec.document_name]

        result[page] = PageSectionInfo(
            section_title=section_title,
            section_path=section_path,
            recommendation_ids=sorted(rec_ids_by_page.get(page, []), key=_rec_sort_key),
        )
    return result
