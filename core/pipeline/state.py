"""Pipeline state for the Duka AI LangGraph workflow."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class PipelineState(TypedDict):
    """State passed through the Duka AI pipeline."""

    session_id: str
    trace_id: str
    input_text: str
    normalized_text: str
    gate: dict[str, Any]
    route: dict[str, Any]
    tool_requests: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    retrieved_texts: list[str]
    retrieved_chunks: list[dict[str, Any]]
    payment_requires_human_review: bool
    escalation: dict[str, Any]
    draft_response: str
    output_guard: dict[str, Any]
    final_response: str
    final_action: str
    composer_mode: str
    trace: Annotated[list[dict[str, Any]], operator.add]
