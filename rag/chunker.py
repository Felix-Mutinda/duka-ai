"""Policy chunking for the MVP knowledge base."""

from __future__ import annotations

from core.schemas import PolicyDocument, RetrievedChunk


def chunk_policy_documents(
    documents: tuple[PolicyDocument, ...],
) -> tuple[RetrievedChunk, ...]:
    """Chunk policy documents into retrievable units."""
    chunks: list[RetrievedChunk] = []

    for document in documents:
        chunks.extend(_chunk_policy_document(document))

    return tuple(chunks)


def _chunk_policy_document(document: PolicyDocument) -> list[RetrievedChunk]:
    """Chunk one policy document by paragraph."""
    chunks: list[RetrievedChunk] = []

    paragraphs = [
        paragraph.strip() for paragraph in document.body.split("\n\n") if paragraph.strip()
    ]

    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            continue

        chunks.append(
            RetrievedChunk(
                source=document.source,
                section=document.title,
                text=paragraph,
            )
        )

    if not chunks:
        chunks.append(
            RetrievedChunk(
                source=document.source,
                section=document.title,
                text=document.body.strip(),
            )
        )

    return chunks
