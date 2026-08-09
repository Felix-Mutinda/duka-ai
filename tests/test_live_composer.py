"""Tests for the optional live composer and mock fallback."""

from core.config import load_app_config
from core.llm.live import (
    LiveComposerError,
    live_compose,
    should_use_live_composer,
)
from core.pipeline import nodes


def test_should_use_live_false_without_api_key(monkeypatch) -> None:
    """Auto mode should fall back to mock without an API key."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    load_app_config.cache_clear()

    assert should_use_live_composer() is False


def test_live_compose_raises_without_api_key(monkeypatch) -> None:
    """Live compose should raise when no API key is configured."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    load_app_config.cache_clear()

    try:
        live_compose({"input_text": "Hello"})
        raise AssertionError("Expected LiveComposerError")
    except LiveComposerError:
        pass


def test_compose_response_falls_back_to_mock_when_live_fails(
    monkeypatch,
) -> None:
    """If live composition fails, the mock composer should be used."""
    monkeypatch.setattr(nodes, "should_use_live_composer", lambda: True)

    def fail_live(state):
        raise LiveComposerError("boom")

    monkeypatch.setattr(nodes, "live_compose", fail_live)

    state = {
        "trace_id": "trace_test",
        "normalized_text": "Hello there.",
        "route": {
            "intent": "greeting",
            "confidence": "medium",
            "risk_level": "low",
        },
        "tool_results": [],
        "retrieved_chunks": [],
        "trace": [],
    }

    update = nodes.compose_response(state)

    assert update["composer_mode"] == "mock_fallback"
    assert "hello" in update["draft_response"].lower()


def test_compose_response_uses_live_when_available(monkeypatch) -> None:
    """When live succeeds, composer_mode should be live."""
    monkeypatch.setattr(nodes, "should_use_live_composer", lambda: True)
    monkeypatch.setattr(
        nodes,
        "live_compose",
        lambda state: "Hello! How can I help?",
    )

    state = {
        "trace_id": "trace_test",
        "normalized_text": "Hello there.",
        "route": {
            "intent": "greeting",
            "confidence": "medium",
            "risk_level": "low",
        },
        "tool_results": [],
        "retrieved_chunks": [],
        "trace": [],
    }

    update = nodes.compose_response(state)

    assert update["composer_mode"] == "live"
    assert update["draft_response"] == "Hello! How can I help?"
