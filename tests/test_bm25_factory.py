import json

from langchain_community.retrievers import BM25Retriever

from src.stores.bm25_factory import build_bm25_retriever


def write_chunks_fixture(tmp_path, doc_key: str, texts: list[str]):
    out_path = tmp_path / f"{doc_key}_chunks.jsonl"
    with out_path.open("w") as f:
        for i, text in enumerate(texts):
            chunk = {
                "text": text,
                "metadata": {
                    "document_name": "Test Doc",
                    "page_number": i + 1,
                    "section_title": "Section",
                    "chunk_id": f"{doc_key}-p{i + 1:03d}-abcd1234",
                    "source_url": "https://example.com",
                    "doc_key": doc_key,
                    "section_path": ["Section"],
                    "page_end": None,
                    "token_count": 10,
                    "recommendation_ids": [],
                    "has_cross_reference": False,
                    "printed_page": None,
                },
            }
            f.write(json.dumps(chunk) + "\n")
    return out_path


class TestBuildBm25Retriever:
    def test_returns_bm25_retriever(self, tmp_path):
        write_chunks_fixture(tmp_path, "docA", ["hypertension treatment", "diabetes care"])
        retriever = build_bm25_retriever(["docA"], chunks_dir=tmp_path)
        assert isinstance(retriever, BM25Retriever)

    def test_combines_multiple_docs_into_one_corpus(self, tmp_path):
        write_chunks_fixture(tmp_path, "docA", ["hypertension treatment"])
        write_chunks_fixture(tmp_path, "docB", ["blood pressure targets"])
        retriever = build_bm25_retriever(["docA", "docB"], chunks_dir=tmp_path)
        assert len(retriever.docs) == 2

    def test_documents_carry_full_metadata(self, tmp_path):
        write_chunks_fixture(tmp_path, "docA", ["hypertension treatment"])
        retriever = build_bm25_retriever(["docA"], chunks_dir=tmp_path)
        doc = retriever.docs[0]
        assert doc.page_content == "hypertension treatment"
        assert doc.metadata["chunk_id"] == "docA-p001-abcd1234"
        assert doc.metadata["document_name"] == "Test Doc"

    def test_retrieves_relevant_document_for_a_query(self, tmp_path):
        write_chunks_fixture(
            tmp_path,
            "docA",
            [
                "hypertension treatment guideline for adults with high blood pressure",
                "diabetes management protocol for type 2 diabetes patients",
                "stroke prevention advice for elderly patients with cardiovascular risk",
                "kidney disease screening recommendations for at risk populations",
            ],
        )
        retriever = build_bm25_retriever(["docA"], chunks_dir=tmp_path, k=1)
        results = retriever.invoke("hypertension treatment blood pressure")
        assert results
        assert "hypertension" in results[0].page_content
