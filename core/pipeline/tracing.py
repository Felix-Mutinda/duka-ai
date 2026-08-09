"""Trace event helpers for pipeline observability."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.schemas import TraceEvent


def trace_event(
    state: Mapping[str, Any],
    node: str,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    """Create a serialized trace event."""
    event = TraceEvent(
        trace_id=state.get("trace_id", "unknown"),
        node=node,
        message=message,
        details=details,
    )

    return event.model_dump(mode="json")
