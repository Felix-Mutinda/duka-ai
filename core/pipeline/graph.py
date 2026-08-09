"""LangGraph workflow for the Duka AI pipeline."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from core.pipeline.nodes import (
    apply_input_gate,
    apply_output_guard,
    compose_response,
    escalate,
    finalize,
    normalize_input,
    route_intent,
)
from core.pipeline.state import PipelineState
from core.schemas import new_id


def build_graph() -> Any:
    """Build the LangGraph pipeline."""
    builder = StateGraph(PipelineState)

    builder.add_node("normalize_input", normalize_input)
    builder.add_node("apply_input_gate", apply_input_gate)
    builder.add_node("route_intent", route_intent)
    builder.add_node("escalate", escalate)
    builder.add_node("compose_response", compose_response)
    builder.add_node("apply_output_guard", apply_output_guard)
    builder.add_node("finalize", finalize)

    builder.add_edge(START, "normalize_input")
    builder.add_edge("normalize_input", "apply_input_gate")

    builder.add_conditional_edges(
        "apply_input_gate",
        _after_input_gate,
        {
            "route_intent": "route_intent",
            "compose_response": "compose_response",
        },
    )

    builder.add_conditional_edges(
        "route_intent",
        _after_route,
        {
            "escalate": "escalate",
            "compose_response": "compose_response",
        },
    )

    builder.add_edge("escalate", "apply_output_guard")
    builder.add_edge("compose_response", "apply_output_guard")
    builder.add_edge("apply_output_guard", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


def run_pipeline(input_text: str, session_id: str | None = None) -> dict[str, Any]:
    """Run one pipeline turn."""
    graph = build_graph()

    initial_state: PipelineState = {
        "session_id": session_id or new_id("sess"),
        "trace_id": new_id("trace"),
        "input_text": input_text,
        "normalized_text": "",
        "gate": {},
        "route": {},
        "retrieved_texts": [],
        "tool_results": [],
        "escalation": {},
        "draft_response": "",
        "output_guard": {},
        "final_response": "",
        "final_action": "",
        "trace": [],
    }

    return graph.invoke(initial_state)


def _after_input_gate(state: dict[str, Any]) -> str:
    """Decide whether to route or use the blocked fallback."""
    gate = state.get("gate") or {}

    if gate.get("blocked"):
        return "compose_response"

    return "route_intent"


def _after_route(state: dict[str, Any]) -> str:
    """Decide whether to escalate or compose a normal response."""
    route = state.get("route") or {}

    if route.get("requires_escalation"):
        return "escalate"

    return "compose_response"
