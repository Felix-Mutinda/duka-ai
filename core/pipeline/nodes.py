"""LangGraph nodes for the Duka AI pipeline."""

from __future__ import annotations

import re
from typing import Any

from tools.registry import call_tool

from core.config import load_app_config
from core.guardrails import evaluate_input, evaluate_output, redact_text
from core.pipeline.router import ORDER_ID_REGEX, mock_route
from core.pipeline.tracing import trace_event
from core.schemas import (
    ActionType,
    Escalation,
    GateDecision,
    Intent,
    OutputGuardContext,
    RiskLevel,
    RouteDecision,
    ToolCall,
)

FALLBACK_BLOCK = "I can help with shop questions, orders, products, and policies."

FALLBACK_ESCALATION = "This needs review by the store team. I have flagged it for escalation."

FALLBACK_PAYMENT_REVIEW = "This payment needs review by the store team. I cannot confirm it yet."

FALLBACK_CLARIFY = "Can you clarify if this is about an order, product, payment, or policy?"

PAYMENT_REFERENCE_REGEX = re.compile(r"\b(?=[A-Z0-9]*\d)[A-Z0-9]{8,16}\b")


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


def plan_tool_call(state: dict[str, Any]) -> dict[str, Any]:
    """Plan deterministic tool calls based on the route."""
    route_data = state.get("route") or {}

    if not route_data:
        return {
            "tool_requests": [],
            "trace": [
                trace_event(
                    state,
                    "plan_tool_call",
                    "No route available. Skipping tool planning.",
                )
            ],
        }

    route = RouteDecision.model_validate(route_data)
    text = state.get("normalized_text", "")
    requests: list[ToolCall] = []

    if route.intent == Intent.ORDER_STATUS:
        order_id = _extract_order_id(text)

        if order_id:
            requests.append(
                ToolCall(
                    name="order_lookup",
                    args={"order_id": order_id},
                )
            )

    elif route.intent == Intent.INVENTORY:
        requests.append(
            ToolCall(
                name="inventory_check",
                args={"product_query": text},
            )
        )

    elif route.intent == Intent.PAYMENT_STATUS:
        args: dict[str, Any] = {}

        reference = _extract_payment_reference(text)
        order_id = _extract_order_id(text)

        if reference:
            args["reference"] = reference

        if order_id:
            args["order_id"] = order_id

        if args:
            requests.append(
                ToolCall(
                    name="payment_status",
                    args=args,
                )
            )

    elif route.intent == Intent.POLICY:
        requests.append(
            ToolCall(
                name="knowledge_base_search",
                args={"query": text, "top_k": 5},
            )
        )

    return {
        "tool_requests": [request.model_dump(mode="json") for request in requests],
        "trace": [
            trace_event(
                state,
                "plan_tool_call",
                "Tool calls planned.",
                tool_count=len(requests),
                tools=[request.name for request in requests],
            )
        ],
    }


def execute_tools(state: dict[str, Any]) -> dict[str, Any]:
    """Execute planned tool calls."""
    tool_results: list[dict[str, Any]] = []
    retrieved_texts = list(state.get("retrieved_texts", []))
    retrieved_chunks = list(state.get("retrieved_chunks", []))
    payment_requires_human_review = bool(state.get("payment_requires_human_review", False))

    escalation_update: dict[str, Any] = {}

    for request_data in state.get("tool_requests", []):
        tool_call = ToolCall.model_validate(request_data)
        result = call_tool(tool_call)

        tool_results.append(result.model_dump(mode="json"))

        if result.ok and result.name == "knowledge_base_search" and result.data:
            for chunk in result.data.get("results", []):
                text = chunk.get("text")

                if text:
                    retrieved_texts.append(text)
                    retrieved_chunks.append(chunk)

        if (
            result.ok
            and result.name == "payment_status"
            and result.data
            and result.data.get("requires_human_review")
        ):
            payment_requires_human_review = True

            if not escalation_update:
                escalation = Escalation(
                    reason="payment_uncertainty",
                    risk_level=RiskLevel.HIGH,
                    summary="Payment status requires human review.",
                    suggested_next_steps=[
                        "Verify the payment reference manually.",
                        "Do not request the customer's M-Pesa PIN.",
                        "Do not release the order until payment is confirmed.",
                    ],
                    context={
                        "redacted_input": redact_text(state.get("input_text", "")),
                        "payment_reference_masked": result.data.get("reference_masked"),
                    },
                )

                escalation_update = {
                    "escalation": escalation.model_dump(mode="json"),
                    "draft_response": FALLBACK_PAYMENT_REVIEW,
                    "final_action": ActionType.ESCALATE.value,
                }

    update: dict[str, Any] = {
        "tool_results": tool_results,
        "retrieved_texts": retrieved_texts,
        "retrieved_chunks": retrieved_chunks,
        "payment_requires_human_review": payment_requires_human_review,
        "trace": [
            trace_event(
                state,
                "execute_tools",
                "Tool calls executed.",
                tool_result_count=len(tool_results),
            )
        ],
    }

    update.update(escalation_update)

    return update


def compose_response(state: dict[str, Any]) -> dict[str, Any]:
    """Compose a deterministic draft response."""
    blocked_or_escalated = {
        ActionType.BLOCK.value,
        ActionType.ESCALATE.value,
    }

    if state.get("draft_response") and state.get("final_action") in blocked_or_escalated:
        return {
            "trace": [
                trace_event(
                    state,
                    "compose_response",
                    "Using existing blocked or escalated response.",
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
    tool_results = state.get("tool_results", [])

    if route.intent in {
        Intent.ORDER_STATUS,
        Intent.INVENTORY,
        Intent.PAYMENT_STATUS,
    }:
        draft_response = _compose_from_tool_results(
            route,
            tool_results,
            normalized_text,
        )
    elif route.intent == Intent.POLICY:
        draft_response = _compose_policy_response(state)
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
    payment_requires_human_review = bool(state.get("payment_requires_human_review", False))

    context = OutputGuardContext(
        retrieved_texts=retrieved_texts,
        payment_requires_human_review=payment_requires_human_review,
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


def _extract_order_id(text: str) -> str | None:
    """Extract an order identifier from text."""
    match = ORDER_ID_REGEX.search(text)

    if not match:
        return None

    return match.group(0).upper()


def _extract_payment_reference(text: str) -> str | None:
    """Extract a likely payment reference from text."""
    upper_text = text.upper()
    match = PAYMENT_REFERENCE_REGEX.search(upper_text)

    if not match:
        return None

    return match.group(0)


def _compose_from_tool_results(
    route: RouteDecision,
    tool_results: list[dict[str, Any]],
    text: str,
) -> str:
    """Compose a response from structured tool results."""
    if route.intent == Intent.ORDER_STATUS:
        return _compose_order_from_results(tool_results, text)

    if route.intent == Intent.INVENTORY:
        return _compose_inventory_from_results(tool_results)

    if route.intent == Intent.PAYMENT_STATUS:
        return _compose_payment_from_results(tool_results)

    return FALLBACK_CLARIFY


def _compose_order_from_results(
    tool_results: list[dict[str, Any]],
    text: str,
) -> str:
    """Compose an order-status response."""
    order_result = _first_tool_result(tool_results, "order_lookup")

    if order_result is None:
        if _extract_order_id(text):
            return "I could not find that order. Please check the order number."

        return "Please provide the order number, for example DKA-1042."

    if not order_result.get("ok"):
        return "I could not find that order. Please check the order number."

    data = order_result.get("data") or {}

    if not data.get("found"):
        return "I could not find that order. Please check the order number."

    status = (data.get("status") or "unknown").replace("_", " ")
    order_id = data.get("order_id") or "Unknown order"

    return f"Order {order_id} is {status}."


def _compose_inventory_from_results(
    tool_results: list[dict[str, Any]],
) -> str:
    """Compose an inventory response."""
    inventory_result = _first_tool_result(tool_results, "inventory_check")

    if inventory_result is None or not inventory_result.get("ok"):
        return "I could not check inventory right now."

    data = inventory_result.get("data") or {}
    matches = data.get("matches", [])

    if not matches:
        return "I could not find that product."

    first_match = matches[0]
    name = first_match.get("name") or "That product"

    if first_match.get("available"):
        return f"Yes, {name} is in stock."

    return f"No, {name} is out of stock."


def _compose_payment_from_results(
    tool_results: list[dict[str, Any]],
) -> str:
    """Compose a payment-status response."""
    payment_result = _first_tool_result(tool_results, "payment_status")

    if payment_result is None:
        return "Please provide the payment reference or order number."

    if not payment_result.get("ok"):
        return "I could not check that payment right now."

    data = payment_result.get("data") or {}

    if not data.get("found"):
        return "I could not find that payment. Please check the reference."

    status = (data.get("status") or "unknown").replace("_", " ")

    return f"Your payment status is {status}."


def _compose_policy_response(state: dict[str, Any]) -> str:
    """Compose a policy response from retrieved chunks."""
    retrieved_chunks = state.get("retrieved_chunks", [])

    if not retrieved_chunks:
        return "I could not find a policy for that."

    texts: list[str] = []
    seen: set[str] = set()

    for chunk in retrieved_chunks:
        text = str(chunk.get("text", "")).strip()
        text = " ".join(text.split())

        if not text or text in seen:
            continue

        seen.add(text)
        texts.append(text)

    if not texts:
        return "I could not find a policy for that."

    combined = " ".join(texts)
    max_chars = load_app_config().app.max_response_chars

    if len(combined) > max_chars:
        combined = combined[: max_chars - 3].rstrip() + "..."

    return combined


def _first_tool_result(
    tool_results: list[dict[str, Any]],
    name: str,
) -> dict[str, Any] | None:
    """Return the first tool result matching a tool name."""
    for result in tool_results:
        if result.get("name") == name:
            return result

    return None
