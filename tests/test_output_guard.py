"""Tests for the output guard."""

from core.config import GuardrailSettings
from core.guardrails.output_guard import evaluate_output
from core.schemas import OutputGuardContext


def test_safe_response_is_allowed() -> None:
    """A normal order response should pass the output guard."""
    settings = GuardrailSettings()
    context = OutputGuardContext()

    decision = evaluate_output(
        "Your order DKA-1042 is out for delivery.",
        context,
        settings,
    )

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.fallback_response is None


def test_pii_leak_is_blocked() -> None:
    """Responses containing sensitive data should be blocked."""
    settings = GuardrailSettings()
    context = OutputGuardContext()

    decision = evaluate_output(
        "The customer phone is 0712345678.",
        context,
        settings,
    )

    assert decision.allowed is False
    assert decision.reason is not None
    assert "pii_leak" in decision.reason
    assert decision.fallback_response is not None


def test_discount_promise_is_blocked() -> None:
    """Responses promising discount codes should be blocked."""
    settings = GuardrailSettings()
    context = OutputGuardContext()

    decision = evaluate_output(
        "Here is your discount code: SAVE10",
        context,
        settings,
    )

    assert decision.allowed is False
    assert decision.reason is not None
    assert "discount_promise" in decision.reason


def test_discount_refusal_is_allowed() -> None:
    """A refusal that mentions discounts should still be allowed."""
    settings = GuardrailSettings()
    context = OutputGuardContext()

    decision = evaluate_output(
        "I cannot issue discount codes.",
        context,
        settings,
    )

    assert decision.allowed is True


def test_refund_promise_is_blocked() -> None:
    """Responses promising refunds should be blocked."""
    settings = GuardrailSettings()
    context = OutputGuardContext()

    decision = evaluate_output(
        "We will issue a refund for your order.",
        context,
        settings,
    )

    assert decision.allowed is False
    assert decision.reason is not None
    assert "refund_promise" in decision.reason


def test_payment_certainty_is_blocked_when_review_required() -> None:
    """Payment certainty should be blocked when review is required."""
    settings = GuardrailSettings()
    context = OutputGuardContext(payment_requires_human_review=True)

    decision = evaluate_output(
        "Your payment is confirmed.",
        context,
        settings,
    )

    assert decision.allowed is False
    assert decision.reason is not None
    assert "payment_uncertainty" in decision.reason


def test_payment_certainty_is_allowed_when_review_not_required() -> None:
    """Payment certainty is allowed when no review is required."""
    settings = GuardrailSettings()
    context = OutputGuardContext(payment_requires_human_review=False)

    decision = evaluate_output(
        "Your payment is confirmed.",
        context,
        settings,
    )

    assert decision.allowed is True


def test_return_policy_contradiction_is_blocked() -> None:
    """Responses contradicting the retrieved return policy should block."""
    settings = GuardrailSettings()
    context = OutputGuardContext(
        retrieved_texts=["Items can be returned within 7 days of delivery."],
    )

    decision = evaluate_output(
        "You can return this item for lifetime free returns.",
        context,
        settings,
    )

    assert decision.allowed is False
    assert decision.reason is not None
    assert "policy_contradiction" in decision.reason


def test_safe_return_policy_response_is_allowed() -> None:
    """A response matching the 7-day policy should be allowed."""
    settings = GuardrailSettings()
    context = OutputGuardContext(
        retrieved_texts=["Items can be returned within 7 days of delivery."],
    )

    decision = evaluate_output(
        "You can return within 7 days of delivery.",
        context,
        settings,
    )

    assert decision.allowed is True
