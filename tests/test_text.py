"""Tests for text token normalization."""

from core.text import tokenize


def test_tokenize_normalizes_return_variants() -> None:
    """Return variants should normalize to the same token."""
    tokens = tokenize("return returns returned")

    assert tokens == ["return", "return", "return"]


def test_tokenize_normalizes_policy_plural() -> None:
    """Plural policies should normalize to policy."""
    assert tokenize("policies") == ["policy"]


def test_tokenize_normalizes_days() -> None:
    """Plural days should normalize to day."""
    assert tokenize("7 days") == ["7", "day"]
