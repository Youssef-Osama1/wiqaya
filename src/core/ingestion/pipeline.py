from pathlib import Path

from src.core.ingestion.cleaning import clean_page_text, extract_raw_pages
from src.core.ingestion.sections import build_section_map
from src.core.schemas import CleanedPage

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


def build_cleaned_pages(doc_key: str) -> list[CleanedPage]:
    section_map = build_section_map(doc_key)
    pages = []
    for page_number, raw_text in extract_raw_pages(doc_key):
        cleaned_text, printed_page = clean_page_text(doc_key, raw_text)
        section_info = section_map[page_number]
        pages.append(
            CleanedPage(
                doc_key=doc_key,
                page_number=page_number,
                printed_page=printed_page,
                text=cleaned_text,
                section_title=section_info.section_title,
                section_path=section_info.section_path,
                recommendation_ids=section_info.recommendation_ids,
            )
        )
    return pages


def write_pages_jsonl(doc_key: str, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{doc_key}_pages.jsonl"
    pages = build_cleaned_pages(doc_key)
    with out_path.open("w", encoding="utf-8") as f:
        for page in pages:
            f.write(page.model_dump_json() + "\n")
    return out_path
