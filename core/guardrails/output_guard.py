"""Output guard for assistant responses."""

from __future__ import annotations

from core.config import GuardrailSettings
from core.guardrails.patterns import (
    DISCOUNT_PROMISE_PATTERNS,
    PAYMENT_CERTAINTY_PATTERNS,
    REFUND_PROMISE_PATTERNS,
    RETURN_CONTRADICTION_PATTERNS,
    matches_any,
)
from core.guardrails.pii import contains_pii
from core.schemas import OutputGuardContext, OutputGuardDecision

GENERIC_FALLBACK = (
    "I cannot complete that request safely. "
    "I can help with shop questions or escalate this to the store team."
)

FALLBACKS: dict[str, str] = {
    "pii_leak": (
        "I cannot share personal or payment details. I can help with the order or escalate it."
    ),
    "discount_promise": (
        "I cannot issue discounts or promo codes. I can help with product and order questions."
    ),
    "refund_promise": (
        "I cannot approve refunds. I can escalate this to the store team for review."
    ),
    "policy_contradiction": (
        "Our store policy is the source of truth. I can share the current policy or escalate this."
    ),
    "payment_uncertainty": (
        "This payment needs review by the store team. I cannot confirm it yet."
    ),
}


def evaluate_output(
    response: str,
    context: OutputGuardContext,
    settings: GuardrailSettings,
) -> OutputGuardDecision:
    """Evaluate a draft assistant response before delivery."""
    reasons: list[str] = []

    if settings.redact_pii and contains_pii(response):
        reasons.append("pii_leak")

    if settings.block_discount_promises and matches_any(
        response,
        DISCOUNT_PROMISE_PATTERNS,
    ):
        reasons.append("discount_promise")

    if matches_any(response, REFUND_PROMISE_PATTERNS):
        reasons.append("refund_promise")

    if settings.block_policy_override and _has_return_policy_contradiction(
        response,
        context.retrieved_texts,
    ):
        reasons.append("policy_contradiction")

    if context.payment_requires_human_review and matches_any(
        response,
        PAYMENT_CERTAINTY_PATTERNS,
    ):
        reasons.append("payment_uncertainty")

    if not reasons:
        return OutputGuardDecision(allowed=True)

    primary_reason = reasons[0]

    return OutputGuardDecision(
        allowed=False,
        reason=", ".join(reasons),
        fallback_response=FALLBACKS.get(primary_reason, GENERIC_FALLBACK),
    )


def _has_return_policy_contradiction(
    response: str,
    retrieved_texts: list[str],
) -> bool:
    """Detect obvious contradictions against a 7-day return policy.

    This is intentionally narrow and deterministic for the MVP. Later phases
    can replace this with a retrieval-faithfulness check.
    """
    policy_text = " ".join(retrieved_texts).lower()

    if "7 days" not in policy_text:
        return False

    return matches_any(response, RETURN_CONTRADICTION_PATTERNS)
