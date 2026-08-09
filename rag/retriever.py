"""BM25 policy retrieval for the MVP knowledge base."""

from __future__ import annotations

from functools import lru_cache

from core.fixtures import load_policy_documents
from core.schemas import RetrievedChunk
from core.text import tokenize
from rank_bm25 import BM25Okapi

from rag.chunker import chunk_policy_documents


@lru_cache
def _policy_index() -> tuple[tuple[RetrievedChunk, ...], BM25Okapi | None]:
    """Build and cache the policy retrieval index."""
    documents = load_policy_documents()
    chunks = chunk_policy_documents(documents)

    pairs = [(chunk, tokenize(_searchable_text(chunk))) for chunk in chunks]

    pairs = [(chunk, tokens) for chunk, tokens in pairs if tokens]

    if not pairs:
        return (), None

    filtered_chunks = tuple(chunk for chunk, _ in pairs)
    tokenized_corpus = [tokens for _, tokens in pairs]

    bm25 = BM25Okapi(tokenized_corpus)

    return filtered_chunks, bm25


def search_policies(query: str, top_k: int = 3) -> tuple[RetrievedChunk, ...]:
    """Search policy chunks using BM25."""
    chunks, bm25 = _policy_index()

    if not chunks or bm25 is None or not query.strip():
        return ()

    tokens = tokenize(query)

    if not tokens:
        return ()

    scores = bm25.get_scores(tokens)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )

    results: list[RetrievedChunk] = []

    for index in ranked_indices[: max(0, top_k)]:
        score = float(scores[index])

        if score <= 0:
            continue

        results.append(chunks[index].model_copy(update={"score": score}))

    return tuple(results)


def _searchable_text(chunk: RetrievedChunk) -> str:
    """Build searchable text from section title and chunk body.

    The section title is indexed for retrieval, but the returned chunk text
    remains the policy paragraph itself.
    """
    section = chunk.section or ""

    return f"{section} {chunk.text}".strip()
