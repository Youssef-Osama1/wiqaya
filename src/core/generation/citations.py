from src.core.schemas import Chunk, Citation, EvidenceItem


def resolve_citations(evidence: list[EvidenceItem], retrieved_chunks: list[Chunk]) -> tuple[list[Citation], list[str]]:
    chunks_by_id = {chunk.metadata.chunk_id: chunk for chunk in retrieved_chunks}

    citations: list[Citation] = []
    unresolved: list[str] = []
    seen_chunk_ids: set[str] = set()

    for item in evidence:
        if item.chunk_id in seen_chunk_ids:
            continue

        chunk = chunks_by_id.get(item.chunk_id)
        if chunk is None:
            unresolved.append(item.chunk_id)
            continue

        seen_chunk_ids.add(item.chunk_id)
        citations.append(
            Citation(
                document_name=chunk.metadata.document_name,
                section_title=chunk.metadata.section_title,
                page_number=chunk.metadata.page_number,
                chunk_id=chunk.metadata.chunk_id,
            )
        )

    return citations, unresolved
