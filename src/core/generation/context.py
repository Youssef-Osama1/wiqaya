from src.core.schemas import Chunk


def assemble_context(chunks: list[Chunk]) -> str:
    blocks = []
    for chunk in chunks:
        meta = chunk.metadata
        header = f"[chunk_id: {meta.chunk_id}] (Document: {meta.document_name}, Section: {meta.section_title}, Page: {meta.page_number})"
        if meta.has_cross_reference:
            header += "\n(cross-reference: this excerpt references guidance outside this corpus)"
        blocks.append(f"{header}\n{chunk.text}")

    return "\n\n".join(blocks)
