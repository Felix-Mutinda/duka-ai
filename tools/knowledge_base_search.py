"""Knowledge base search tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from rag.retriever import search_policies


class KnowledgeBaseSearchArgs(BaseModel):
    """Arguments for knowledge base search."""

    query: str = Field(min_length=2)
    top_k: int = Field(default=3, ge=1, le=5)


def knowledge_base_search(args: dict[str, Any]) -> dict[str, Any]:
    """Search policy knowledge base chunks."""
    parsed = KnowledgeBaseSearchArgs.model_validate(args)

    results = search_policies(parsed.query, parsed.top_k)

    return {
        "results": [chunk.model_dump(mode="json") for chunk in results],
    }
