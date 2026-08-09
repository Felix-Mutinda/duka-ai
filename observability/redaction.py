"""Redaction helpers for owner-facing observability artifacts."""

from __future__ import annotations

from typing import Any

from core.guardrails.pii import redact_text

SENSITIVE_KEY_MARKERS = (
    "reference",
    "phone",
    "email",
    "pii",
    "pin",
)


def redact_structure(value: Any) -> Any:
    """Recursively redact likely sensitive values in structured data."""
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, dict):
        return {str(key): _redact_dict_item(key, item) for key, item in value.items()}

    if isinstance(value, list):
        return [redact_structure(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_structure(item) for item in value)

    return value


def _redact_dict_item(key: Any, value: Any) -> Any:
    """Redact dictionary values whose keys look sensitive."""
    key_text = str(key).lower()

    if any(marker in key_text for marker in SENSITIVE_KEY_MARKERS):
        if isinstance(value, str):
            return redact_text(value)

        return redact_structure(value)

    return redact_structure(value)
