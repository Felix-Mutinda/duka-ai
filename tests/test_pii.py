"""Tests for PII detection and redaction."""

from core.guardrails.pii import contains_pii, redact_text


def test_contains_phone() -> None:
    """Phone numbers should be detected as sensitive."""
    assert contains_pii("Call 0712345678") is True


def test_contains_email() -> None:
    """Email addresses should be detected as sensitive."""
    assert contains_pii("Email jane@example.com") is True


def test_contains_payment_reference() -> None:
    """Payment references should be detected as sensitive."""
    assert contains_pii("Ref QGH7XKLM21") is True


def test_order_id_is_not_treated_as_pii() -> None:
    """Order identifiers should not be treated as PII."""
    assert contains_pii("Order DKA-1042") is False


def test_product_id_is_not_treated_as_pii() -> None:
    """Product identifiers should not be treated as PII."""
    assert contains_pii("PRD-001") is False


def test_redact_phone() -> None:
    """Phone numbers should be masked."""
    redacted = redact_text("Call 0712345678")

    assert "0712345678" not in redacted
    assert "071*****78" in redacted


def test_redact_email() -> None:
    """Email addresses should be masked while preserving the domain."""
    redacted = redact_text("Email jane@example.com")

    assert "jane@example.com" not in redacted
    assert "@example.com" in redacted


def test_redact_payment_reference() -> None:
    """Payment references should be masked."""
    redacted = redact_text("Ref QGH7XKLM21")

    assert "QGH7XKLM21" not in redacted
    assert "QGH7****" in redacted


def test_redact_mixed_sensitive_text() -> None:
    """Redaction should handle multiple sensitive values."""
    text = "Contact jane@example.com or 0712345678. Ref QGH7XKLM21."
    redacted = redact_text(text)

    assert "jane@example.com" not in redacted
    assert "0712345678" not in redacted
    assert "QGH7XKLM21" not in redacted
    assert "DKA-1042" not in redacted
