"""PII and sensitive-data detection/redaction helpers."""

from __future__ import annotations

from re import Match

from core.guardrails.patterns import EMAIL, PAYMENT_REFERENCE, PHONE


def contains_phone(text: str) -> bool:
    """Return True when the text contains a likely phone number."""
    return bool(PHONE.search(text))


def contains_email(text: str) -> bool:
    """Return True when the text contains a likely email address."""
    return bool(EMAIL.search(text))


def contains_payment_reference(text: str) -> bool:
    """Return True when the text contains a likely payment reference.

    Payment references are treated as sensitive even though they are not
    always personally identifiable information.
    """
    return bool(PAYMENT_REFERENCE.search(text))


def contains_pii(text: str) -> bool:
    """Return True when the text contains sensitive data."""
    return contains_phone(text) or contains_email(text) or contains_payment_reference(text)


def redact_text(text: str) -> str:
    """Redact likely sensitive values from text."""
    text = EMAIL.sub(_redact_email, text)
    text = PHONE.sub(_redact_phone, text)
    text = PAYMENT_REFERENCE.sub(_redact_payment_reference, text)
    return text


def _redact_phone(match: Match[str]) -> str:
    """Mask a phone number while preserving a small prefix and suffix."""
    digits = "".join(ch for ch in match.group(0) if ch.isdigit())

    if len(digits) <= 4:
        return "***"

    return f"{digits[:3]}*****{digits[-2:]}"


def _redact_email(match: Match[str]) -> str:
    """Mask an email address while preserving the domain."""
    email = match.group(0)
    local, domain = email.split("@", 1)

    if not local:
        return f"***@{domain}"

    return f"{local[0]}***@{domain}"


def _redact_payment_reference(match: Match[str]) -> str:
    """Mask a payment reference while preserving a small prefix."""
    value = match.group(0)

    if len(value) <= 4:
        return "****"

    return f"{value[:4]}****"
