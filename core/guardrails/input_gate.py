"""Input gate for untrusted customer messages."""

from __future__ import annotations

from core.guardrails.patterns import (
    DISCOUNT_REQUEST_PATTERNS,
    FRAUD_PATTERNS,
    INJECTION_PATTERNS,
    PII_EXTRACTION_PATTERNS,
    matches_any,
)
from core.schemas import GateDecision, RiskLevel

FALLBACK_INJECTION = "I can help with shop questions, orders, products, and delivery policies."

FALLBACK_DISCOUNT_ABUSE = (
    "I cannot issue discount codes. I can help with product and order questions."
)

FALLBACK_PII_EXTRACTION = (
    "I cannot share personal customer details. "
    "If this is your order, please provide the order number."
)


def evaluate_input(text: str) -> GateDecision:
    """Evaluate untrusted input before it reaches the assistant pipeline."""
    reasons: list[str] = []
    blocked = False
    risk_level = RiskLevel.LOW
    fallback_response: str | None = None

    if matches_any(text, INJECTION_PATTERNS):
        blocked = True
        risk_level = RiskLevel.HIGH
        reasons.append("prompt_injection")
        fallback_response = fallback_response or FALLBACK_INJECTION

    if matches_any(text, DISCOUNT_REQUEST_PATTERNS):
        blocked = True
        risk_level = RiskLevel.HIGH
        reasons.append("discount_abuse")
        fallback_response = fallback_response or FALLBACK_DISCOUNT_ABUSE

    if matches_any(text, PII_EXTRACTION_PATTERNS):
        blocked = True
        risk_level = RiskLevel.HIGH
        reasons.append("pii_extraction")
        fallback_response = fallback_response or FALLBACK_PII_EXTRACTION

    if matches_any(text, FRAUD_PATTERNS):
        risk_level = RiskLevel.HIGH
        reasons.append("fraud_report")

    return GateDecision(
        blocked=blocked,
        risk_level=risk_level,
        reasons=reasons,
        fallback_response=fallback_response,
    )
