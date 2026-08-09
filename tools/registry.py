"""Tool registry and execution wrapper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.schemas import ToolCall, ToolResult
from pydantic import ValidationError

from tools.base import ToolError
from tools.inventory_check import inventory_check
from tools.knowledge_base_search import knowledge_base_search
from tools.order_lookup import order_lookup
from tools.payment_status import payment_status

_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "order_lookup": order_lookup,
    "inventory_check": inventory_check,
    "payment_status": payment_status,
    "knowledge_base_search": knowledge_base_search,
}


def call_tool(tool_call: ToolCall) -> ToolResult:
    """Call a registered tool and return a structured result."""
    handler = _HANDLERS.get(tool_call.name)

    if handler is None:
        return ToolResult(
            call_id=tool_call.call_id,
            name=tool_call.name,
            ok=False,
            error=f"Unknown tool: {tool_call.name}",
        )

    try:
        data = handler(tool_call.args)
    except (ToolError, ValidationError, ValueError) as exc:
        return ToolResult(
            call_id=tool_call.call_id,
            name=tool_call.name,
            ok=False,
            error=str(exc),
        )

    return ToolResult(
        call_id=tool_call.call_id,
        name=tool_call.name,
        ok=True,
        data=data,
    )
