"""Tests for core schemas."""

import pytest
from core.schemas import GateDecision, Order, Payment, RiskLevel, ToolCall
from pydantic import ValidationError


def test_gate_decision_defaults() -> None:
    """Gate decision should default to allowed low-risk."""
    decision = GateDecision()

    assert decision.blocked is False
    assert decision.risk_level == RiskLevel.LOW
    assert decision.reasons == []
    assert decision.fallback_response is None


def test_gate_decision_reasons_are_unique_and_sorted() -> None:
    """Guardrail reasons should be stable for tracing."""
    decision = GateDecision(blocked=True, reasons=["b", "a", "b"])

    assert decision.reasons == ["a", "b"]


def test_tool_call_requires_name() -> None:
    """Tool calls must have non-empty names."""
    with pytest.raises(ValidationError):
        ToolCall(name="")


def test_order_normalizes_order_id() -> None:
    """Order IDs should be normalized to uppercase DKA format."""
    order = Order(
        order_id="dka-1042",
        status="pending",
        payment_status="paid",
    )

    assert order.order_id == "DKA-1042"


def test_order_rejects_invalid_order_id() -> None:
    """Order IDs must start with DKA-."""
    with pytest.raises(ValidationError):
        Order(
            order_id="1042",
            status="pending",
            payment_status="paid",
        )


def test_payment_normalizes_reference() -> None:
    """Payment references should be normalized."""
    payment = Payment(
        reference=" qgh7xklm21 ",
        order_id="DKA-1042",
        status="pending_review",
        amount_kes=1000,
    )

    assert payment.reference == "QGH7XKLM21"
