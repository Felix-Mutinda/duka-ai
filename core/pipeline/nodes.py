"""LangGraph nodes for the Duka AI pipeline."""

from __future__ import annotations

from typing import Any

from core.config import load_app_config
from core.fixtures import FixtureNotFoundError, get_order
from core.guardrails import evaluate_input, evaluate_output, redact_text
from core.pipeline.router import ORDER_ID_REGEX, mock_route
from core.pipeline.tracing import trace_event
from core.schemas import (
    ActionType,
    Escalation,
    GateDecision,
    Intent,
    OutputGuardContext,
    RouteDecision,
)

FALLBACK_BLOCK = "I can help with shop questions, orders, products, and policies."

FALLBACK_ESCALATION = "This needs review by the store team. I have flagged it for escalation."

FALLBACK_CLARIFY = "Can you clarify if this is about an order, product, payment, or policy?"


def normalize_input(state: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw customer input."""
    input_text = state.get("input_text", "")
    normalized_text = input_text.strip()

    return {
        "normalized_text": normalized_text,
        "trace": [
            trace_event(
                state,
                "normalize_input",
                "Normalized input.",
                input_length=len(input_text),
            )
        ],
    }


def apply_input_gate(state: dict[str, Any]) -> dict[str, Any]:
    """Run the input gate before routing or model use."""
    normalized_text = state.get("normalized_text", "")
    decision = evaluate_input(normalized_text)

    update: dict[str, Any] = {
        "gate": decision.model_dump(mode="json"),
        "trace": [
            trace_event(
                state,
                "apply_input_gate",
                "Input gate evaluated.",
                blocked=decision.blocked,
                risk_level=decision.risk_level.value,
                reasons=decision.reasons,
            )
        ],
    }

    if decision.blocked:
        update["draft_response"] = decision.fallback_response or FALLBACK_BLOCK
        update["final_action"] = ActionType.BLOCK.value

    return update


def route_intent(state: dict[str, Any]) -> dict[str, Any]:
    """Route the normalized input using the deterministic mock router."""
    normalized_text = state.get("normalized_text", "")
    gate_data = state.get("gate") or {}
    gate = GateDecision.model_validate(gate_data) if gate_data else GateDecision()

    route = mock_route(normalized_text, gate)

    return {
        "route": route.model_dump(mode="json"),
        "trace": [
            trace_event(
                state,
                "route_intent",
                "Intent routed.",
                intent=route.intent.value,
                confidence=route.confidence.value,
                requires_escalation=route.requires_escalation,
            )
        ],
    }


def escalate(state: dict[str, Any]) -> dict[str, Any]:
    """Create an escalation package and set an escalation response."""
    route_data = state.get("route") or {}
    route = RouteDecision.model_validate(route_data)

    input_text = state.get("input_text", "")

    escalation = Escalation(
        reason=route.reason or route.intent.value,
        risk_level=route.risk_level,
        summary="Customer requires human review.",
        suggested_next_steps=[
            "Review the conversation and verify the customer's concern.",
            "Do not request the customer's M-Pesa PIN.",
            "If payment is involved, verify the reference manually.",
        ],
        context={
            "intent": route.intent.value,
            "redacted_input": redact_text(input_text),
        },
    )

    return {
        "escalation": escalation.model_dump(mode="json"),
        "draft_response": FALLBACK_ESCALATION,
        "final_action": ActionType.ESCALATE.value,
        "trace": [
            trace_event(
                state,
                "escalate",
                "Escalation created.",
                escalation_id=escalation.escalation_id,
                reason=escalation.reason,
            )
        ],
    }


def compose_response(state: dict[str, Any]) -> dict[str, Any]:
    """Compose a deterministic draft response."""
    if state.get("draft_response") and state.get("final_action") == ActionType.BLOCK.value:
        return {
            "trace": [
                trace_event(
                    state,
                    "compose_response",
                    "Using blocked fallback response.",
                )
            ],
        }

    route_data = state.get("route") or {}

    if not route_data:
        return {
            "draft_response": FALLBACK_CLARIFY,
            "final_action": ActionType.RESPOND.value,
            "trace": [
                trace_event(
                    state,
                    "compose_response",
                    "No route available. Asking for clarification.",
                )
            ],
        }

    route = RouteDecision.model_validate(route_data)
    normalized_text = state.get("normalized_text", "")

    if route.intent == Intent.ORDER_STATUS:
        draft_response = _compose_order_status(normalized_text)
    elif route.intent == Intent.PAYMENT_STATUS:
        draft_response = "Payment status checks are wired in Phase 4."
    elif route.intent == Intent.INVENTORY:
        draft_response = "Inventory checks are wired in Phase 4."
    elif route.intent == Intent.POLICY:
        draft_response = "Policy retrieval is wired in Phase 4."
    elif route.intent == Intent.FRAUD_OR_DISPUTE:
        draft_response = FALLBACK_ESCALATION
    else:
        draft_response = FALLBACK_CLARIFY

    return {
        "draft_response": draft_response,
        "final_action": ActionType.RESPOND.value,
        "trace": [
            trace_event(
                state,
                "compose_response",
                "Draft response composed.",
                intent=route.intent.value,
            )
        ],
    }


def apply_output_guard(state: dict[str, Any]) -> dict[str, Any]:
    """Run the output guard before final delivery."""
    draft_response = state.get("draft_response", "")
    retrieved_texts = state.get("retrieved_texts", [])

    context = OutputGuardContext(
        retrieved_texts=retrieved_texts,
        payment_requires_human_review=False,
    )

    settings = load_app_config().guardrails
    decision = evaluate_output(draft_response, context, settings)

    update: dict[str, Any] = {
        "output_guard": decision.model_dump(mode="json"),
        "trace": [
            trace_event(
                state,
                "apply_output_guard",
                "Output guard evaluated.",
                allowed=decision.allowed,
                reason=decision.reason,
            )
        ],
    }

    if decision.allowed:
        update["final_response"] = draft_response

        if not state.get("final_action"):
            update["final_action"] = ActionType.RESPOND.value

        return update

    update["final_response"] = decision.fallback_response or FALLBACK_BLOCK
    update["final_action"] = ActionType.BLOCK.value

    return update


def finalize(state: dict[str, Any]) -> dict[str, Any]:
    """Finish the pipeline run."""
    return {
        "trace": [
            trace_event(
                state,
                "finalize",
                "Pipeline finished.",
                final_action=state.get("final_action"),
            )
        ],
    }


def _compose_order_status(text: str) -> str:
    """Compose a deterministic order-status response from fixtures."""
    order_id = _extract_order_id(text)

    if not order_id:
        return "Please provide the order number, for example DKA-1042."

    try:
        order = get_order(order_id)
    except FixtureNotFoundError:
        return "I could not find that order. Please check the order number."

    status = order.status.replace("_", " ")

    return f"Order {order.order_id} is {status}."


def _extract_order_id(text: str) -> str | None:
    """Extract an order identifier from text."""
    match = ORDER_ID_REGEX.search(text)

    if not match:
        return None

    return match.group(0).upper()
