import difflib
import re

from src.core.schemas import EvidenceItem, QuoteCheck

MATCH_RATIO_THRESHOLD = 0.9


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _verify_quote_text(quote: str, chunk_text: str) -> tuple[bool, float]:
    quote_norm = _normalize(quote)
    chunk_norm = _normalize(chunk_text)

    if not quote_norm:
        return False, 0.0

    if quote_norm in chunk_norm:
        return True, 1.0

    matcher = difflib.SequenceMatcher(None, chunk_norm, quote_norm)
    match = matcher.find_longest_match(0, len(chunk_norm), 0, len(quote_norm))
    if match.size == 0:
        return False, 0.0

    window_start = max(0, match.a - match.b)
    window = chunk_norm[window_start : window_start + len(quote_norm)]
    ratio = difflib.SequenceMatcher(None, quote_norm, window).ratio()
    return ratio >= MATCH_RATIO_THRESHOLD, ratio


def verify_evidence_quote(item: EvidenceItem, chunk_text: str) -> QuoteCheck:
    verified, ratio = _verify_quote_text(item.quote, chunk_text)
    return QuoteCheck(chunk_id=item.chunk_id, quote=item.quote, verified=verified, match_ratio=ratio)
