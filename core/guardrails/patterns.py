"""Deterministic guardrail patterns for the MVP.

These patterns are intentionally conservative and testable. They are not a
full production classifier. They exist to demonstrate structural guardrails.
"""

from __future__ import annotations

import re
from re import Pattern

PHONE: Pattern[str] = re.compile(r"(?:\+?254|0)(?:7|1)\d{8}\b")

EMAIL: Pattern[str] = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

PAYMENT_REFERENCE: Pattern[str] = re.compile(r"\b[A-Z0-9]{8,16}\b")

INJECTION_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore (all |any )?(previous|prior|above) instructions",
        r"disregard (all |any )?(previous|prior|above) instructions",
        r"reveal (your )?system prompt",
        r"show (your )?system prompt",
        r"print (your )?system prompt",
        r"developer mode",
        r"jailbreak",
        r"override (your )?(instructions|policy|guardrails)",
    )
)

DISCOUNT_REQUEST_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(give|generate|create|issue) .{0,40}(discount|promo|coupon) code",
        r"100% discount",
        r"full discount",
        r"supervisor mode",
    )
)

PII_EXTRACTION_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(give|show|reveal|tell|send) .{0,60}"
        r"(customer|client|user).{0,60}"
        r"(phone|email|address|national id)",
        r"(phone number|email address|address|national id) .{0,30}"
        r"(of|for) .{0,30}"
        r"(customer|client|user)",
        r"customer .{0,30}(phone|email|address)",
    )
)

FRAUD_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bfraud\b",
        r"\bstolen\b",
        r"\bunauthorized\b",
        r"without (my )?permission",
        r"\bscam\b",
    )
)

DISCOUNT_PROMISE_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(here is|use|your|give|issued|created) .{0,50}"
        r"(discount|promo|coupon) code",
        r"(i|we) (can|will|have) .{0,50}"
        r"(issue|give|create|apply) .{0,50}discount",
        r"\b\d{1,3}%\s*(off|discount)\b",
    )
)

REFUND_PROMISE_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(refund|money back) (has been|is) (approved|issued|processed)",
        r"(i|we) (can|will) .{0,50}"
        r"(issue|process|approve) .{0,50}refund",
    )
)

PAYMENT_CERTAINTY_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"payment (is|has been) (confirmed|successful|completed|verified)",
        r"order (is|has been) paid",
    )
)

RETURN_CONTRADICTION_PATTERNS: tuple[Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"lifetime (free )?returns?",
        r"(all|any|every) items? .{0,60}lifetime .{0,30}returns?",
        r"(you can|we accept|eligible to) .{0,60}"
        r"(30|60|90)[ -]?days? returns?",
    )
)


def matches_any(text: str, patterns: tuple[Pattern[str], ...]) -> bool:
    """Return True when any pattern matches the text."""
    return any(pattern.search(text) for pattern in patterns)
