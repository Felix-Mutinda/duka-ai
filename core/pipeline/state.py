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
    retrieved_texts: list[str]
    tool_results: list[dict[str, Any]]
    escalation: dict[str, Any]
    draft_response: str
    output_guard: dict[str, Any]
    final_response: str
    final_action: str
    trace: Annotated[list[dict[str, Any]], operator.add]
