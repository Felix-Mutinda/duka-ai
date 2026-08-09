"""Tests for configuration loading."""

from core.config import get_app_settings, load_app_config


def test_app_settings_defaults(monkeypatch) -> None:
    """Default runtime settings should be guarded and auto."""
    monkeypatch.delenv("DUKA_MODE", raising=False)
    monkeypatch.delenv("DUKA_LLM_MODE", raising=False)
    monkeypatch.delenv("DUKA_MAX_RESPONSE_CHARS", raising=False)

    get_app_settings.cache_clear()
    settings = get_app_settings()

    assert settings.mode == "guarded"
    assert settings.llm_mode == "auto"
    assert settings.max_response_chars == 300


def test_load_missing_config_returns_defaults() -> None:
    """Missing YAML file should produce safe defaults."""
    get_app_settings.cache_clear()
    load_app_config.cache_clear()

    config = load_app_config("does-not-exist.yaml")

    assert config.app.mode == "guarded"
    assert config.app.llm_mode == "auto"
    assert config.demo.shop_name == "Demo Electronics Duka"
    assert config.guardrails.redact_pii is True
