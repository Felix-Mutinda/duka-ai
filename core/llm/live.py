"""OpenAI-compatible live response composer.

This composer is intentionally narrow. It only writes a customer-facing
response from structured pipeline facts. It does not route, call tools,
retrieve documents, or decide escalation.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from core.config import load_app_config
from core.guardrails import redact_text


class LiveComposerError(Exception):
    """Raised when the live composer cannot produce a response."""


SYSTEM_PROMPT = (
    "You are Duka AI, a customer assistant for a small electronics shop. "
    "Write only one customer-facing response. "
    "Use only the facts provided. "
    "If the customer greets you, greet them back and ask how you can help "
    "with orders, products, payments, or policies. "
    "Match the customer's language or language mix when clear. "
    "If facts are insufficient, say the store team needs to review the issue. "
    "Do not mention system prompts, tools, retrieval, or internal checks. "
    "Do not offer discounts, promo codes, refunds, or payment guarantees. "
    "Do not request M-Pesa PINs or sensitive personal details. "
    "Keep the response short and plain text."
)


def should_use_live_composer() -> bool:
    """Return True when the live composer should be attempted."""
    settings = load_app_config().app

    if settings.llm_mode == "mock":
        return False

    if settings.llm_provider != "openai_compatible":
        return False

    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def live_compose(state: dict[str, Any]) -> str:
    """Compose a response using an OpenAI-compatible chat endpoint."""
    settings = load_app_config().app

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise LiveComposerError("missing_api_key")

    if settings.llm_provider != "openai_compatible":
        raise LiveComposerError("unsupported_provider")

    user_prompt = _build_prompt(state)

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()

        body = response.json()
        content = body["choices"][0]["message"]["content"]
    except httpx.HTTPError as exc:
        raise LiveComposerError("request_failed") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise LiveComposerError("invalid_response") from exc

    text = str(content or "").strip()

    if not text:
        raise LiveComposerError("empty_response")

    text = " ".join(text.split())

    max_chars = settings.max_response_chars

    if len(text) > max_chars:
        text = text[:max_chars].rstrip()

    return text


def _build_prompt(state: dict[str, Any]) -> str:
    """Build a redacted, fact-grounded prompt for the live composer."""
    settings = load_app_config().app

    input_redacted = redact_text(str(state.get("input_text", "")))

    route = state.get("route") or {}
    intent = str(route.get("intent") or "unclear")

    tool_results = list(state.get("tool_results", []))[:3]
    retrieved_chunks = list(state.get("retrieved_chunks", []))[:3]

    facts = {
        "intent": intent,
        "payment_requires_human_review": bool(state.get("payment_requires_human_review", False)),
        "tool_results": tool_results,
        "policy_chunks": retrieved_chunks,
    }

    facts_json = json.dumps(
        facts,
        indent=2,
        sort_keys=True,
        default=str,
    )

    facts_json = redact_text(facts_json)

    return (
        f"Customer message:\n{input_redacted}\n\n"
        "Task:\n"
        "Write a short customer-facing response.\n\n"
        f"Facts:\n{facts_json}\n\n"
        f"Maximum response characters: {settings.max_response_chars}"
    )
