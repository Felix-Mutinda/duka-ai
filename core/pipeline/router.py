"""Deterministic mock router for Phase 3.

This router is intentionally rule-based. Later phases can replace it with a
live model or a trained classifier while keeping the same RouteDecision shape.
"""

from __future__ import annotations

import re

from core.schemas import (
    Confidence,
    GateDecision,
    Intent,
    RiskLevel,
    RouteDecision,
)

ORDER_ID_REGEX = re.compile(r"\bDKA-\d{4,}\b", re.IGNORECASE)

ORDER_KEYWORDS = (
    "order",
    "iko wapi",
    "where is my",
)

PAYMENT_KEYWORDS = (
    "m-pesa",
    "mpesa",
    "payment",
    "paid",
    "reference",
)

INVENTORY_KEYWORDS = (
    "stock",
    "available",
    "inventory",
    "ziko",
)

POLICY_KEYWORDS = (
    "return",
    "refund",
    "warranty",
    "shipping",
    "policy",
)


def mock_route(text: str, gate: GateDecision) -> RouteDecision:
    """Route input using deterministic rules."""
    lower = text.lower()

    if gate.blocked:
        return RouteDecision(
            intent=Intent.INJECTION_ATTEMPT,
            confidence=Confidence.HIGH,
            risk_level=gate.risk_level,
            requires_escalation=False,
            reason="blocked_by_input_gate",
        )

    if "fraud_report" in gate.reasons:
        return RouteDecision(
            intent=Intent.FRAUD_OR_DISPUTE,
            confidence=Confidence.MEDIUM,
            risk_level=RiskLevel.HIGH,
            requires_escalation=True,
            reason="fraud_report",
        )

    if ORDER_ID_REGEX.search(text):
        return RouteDecision(
            intent=Intent.ORDER_STATUS,
            confidence=Confidence.HIGH,
            risk_level=RiskLevel.LOW,
            requires_tool=True,
            reason="order_identifier_present",
        )

    if any(keyword in lower for keyword in PAYMENT_KEYWORDS):
        return RouteDecision(
            intent=Intent.PAYMENT_STATUS,
            confidence=Confidence.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            requires_tool=True,
            reason="payment_keywords",
        )

    if any(keyword in lower for keyword in ORDER_KEYWORDS):
        return RouteDecision(
            intent=Intent.ORDER_STATUS,
            confidence=Confidence.MEDIUM,
            risk_level=RiskLevel.LOW,
            requires_tool=True,
            reason="order_keywords",
        )

    if any(keyword in lower for keyword in INVENTORY_KEYWORDS):
        return RouteDecision(
            intent=Intent.INVENTORY,
            confidence=Confidence.MEDIUM,
            risk_level=RiskLevel.LOW,
            requires_tool=True,
            reason="inventory_keywords",
        )

    if any(keyword in lower for keyword in POLICY_KEYWORDS):
        return RouteDecision(
            intent=Intent.POLICY,
            confidence=Confidence.MEDIUM,
            risk_level=RiskLevel.LOW,
            requires_retrieval=True,
            reason="policy_keywords",
        )

    return RouteDecision(
        intent=Intent.UNCLEAR,
        confidence=Confidence.LOW,
        risk_level=RiskLevel.LOW,
        reason="no_clear_intent",
    )
