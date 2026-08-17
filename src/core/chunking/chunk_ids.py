import hashlib


def _normalize_for_hash(text: str) -> str:
    return " ".join(text.split())


def compute_chunk_id(doc_key: str, page_number: int, text: str) -> str:
    digest = hashlib.sha1(_normalize_for_hash(text).encode("utf-8")).hexdigest()[:8]
    return f"{doc_key}-p{page_number:03d}-{digest}"
