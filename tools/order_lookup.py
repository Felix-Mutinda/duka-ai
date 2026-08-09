"""Order lookup tool."""

from __future__ import annotations

from typing import Any

from core.fixtures import FixtureNotFoundError, get_order
from pydantic import BaseModel, Field

from tools.base import ToolError


class OrderLookupArgs(BaseModel):
    """Arguments for order lookup."""

    order_id: str = Field(min_length=4)


def order_lookup(args: dict[str, Any]) -> dict[str, Any]:
    """Look up an order from fixture data."""
    parsed = OrderLookupArgs.model_validate(args)

    try:
        order = get_order(parsed.order_id)
    except FixtureNotFoundError as exc:
        raise ToolError(str(exc)) from exc

    return {
        "found": True,
        "order_id": order.order_id,
        "status": order.status,
        "estimated_delivery": order.estimated_delivery,
        "delivery_area": order.delivery_area,
        "payment_status": order.payment_status,
    }
