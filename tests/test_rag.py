"""Tests for policy retrieval."""

from rag.retriever import search_policies


def test_search_returns_return_policy() -> None:
    """Return questions should retrieve the return policy."""
    results = search_policies("Can I return an item?")

    assert results
    assert any("7 days" in chunk.text for chunk in results)


def test_search_returns_mpesa_policy() -> None:
    """M-Pesa questions should retrieve the payment policy."""
    results = search_policies("M-Pesa payment pending")

    assert results
    assert any("M-Pesa" in chunk.text for chunk in results)


def test_search_empty_query_returns_empty() -> None:
    """Empty queries should return no results."""
    assert search_policies("") == ()
