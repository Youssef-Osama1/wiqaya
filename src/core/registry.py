from pathlib import Path

from pydantic import BaseModel

DATA_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


class DocSpec(BaseModel):
    doc_key: str
    path: Path
    document_name: str
    source_url: str
    cleaning_profile: str


REGISTRY: dict[str, DocSpec] = {
    "who_hypertension": DocSpec(
        doc_key="who_hypertension",
        path=DATA_RAW_DIR / "Guideline for the pharmacological treatment of hypertension in adults.pdf",
        document_name="WHO Guideline for the Pharmacological Treatment of Hypertension in Adults",
        source_url="https://www.who.int/publications/i/item/9789240033986",
        cleaning_profile="who_hypertension",
    ),
    "nice_ng136": DocSpec(
        doc_key="nice_ng136",
        path=DATA_RAW_DIR / "hypertension-in-adults-diagnosis-and-management.pdf",
        document_name="NICE NG136: Hypertension in Adults - Diagnosis and Management",
        source_url="https://www.nice.org.uk/guidance/ng136",
        cleaning_profile="nice_ng136",
    ),
}


def get_doc_spec(doc_key: str) -> DocSpec:
    try:
        return REGISTRY[doc_key]
    except KeyError:
        raise KeyError(f"Unknown doc_key {doc_key!r}; known keys: {sorted(REGISTRY)}") from None


def all_doc_specs() -> list[DocSpec]:
    return list(REGISTRY.values())
