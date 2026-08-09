"""Typed application configuration for Duka AI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Runtime settings loaded from environment variables.

    Environment variables are prefixed with DUKA_.
    Example:
        DUKA_MODE=guarded
        DUKA_LLM_MODE=auto
    """

    model_config = SettingsConfigDict(
        env_prefix="DUKA_",
        env_file=".env",
        extra="ignore",
    )

    mode: Literal["guarded", "naive"] = "guarded"
    llm_mode: Literal["mock", "live", "auto"] = "auto"
    llm_provider: Literal["mock", "openai_compatible"] = "openai_compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = Field(default=5.0, gt=0)
    llm_max_tokens: int = Field(default=220, gt=0)
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_response_chars: int = Field(default=300, gt=0)


class DemoSettings(BaseModel):
    """Settings that describe the simulated demo shop."""

    shop_name: str = "Demo Electronics Duka"
    channel: str = "whatsapp_sim"


class GuardrailSettings(BaseModel):
    """Feature flags for guardrail behavior."""

    redact_pii: bool = True
    block_discount_promises: bool = True
    block_policy_override: bool = True


class AppConfig(BaseModel):
    """Full application configuration."""

    app: AppSettings
    demo: DemoSettings
    guardrails: GuardrailSettings


@lru_cache
def get_app_settings() -> AppSettings:
    """Return cached runtime settings."""
    return AppSettings()


@lru_cache
def load_app_config(path: str | Path = "config.yaml") -> AppConfig:
    """Load application config from YAML and environment.

    If the YAML file is missing, return safe defaults.
    """
    file_path = Path(path)
    data: dict[str, Any] = {}

    if file_path.exists():
        loaded = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            msg = f"Config file {file_path} must contain a YAML mapping."
            raise ValueError(msg)
        data = loaded

    app_data = data.get("app", {})
    demo_data = data.get("demo", {})
    guardrail_data = data.get("guardrails", {})

    app_settings = AppSettings(**app_data)
    demo_settings = DemoSettings.model_validate(demo_data)
    guardrail_settings = GuardrailSettings.model_validate(guardrail_data)

    return AppConfig(
        app=app_settings,
        demo=demo_settings,
        guardrails=guardrail_settings,
    )
