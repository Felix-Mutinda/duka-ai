"""Inventory check tool."""

from __future__ import annotations

from typing import Any

from core.fixtures import load_products
from core.schemas import Product
from core.text import tokenize
from pydantic import BaseModel, Field


class InventoryCheckArgs(BaseModel):
    """Arguments for inventory checks."""

    product_query: str = Field(min_length=2)


def inventory_check(args: dict[str, Any]) -> dict[str, Any]:
    """Check inventory using fixture products."""
    parsed = InventoryCheckArgs.model_validate(args)

    products = load_products()
    matches: list[dict[str, Any]] = []

    for product in products:
        if product.category == "eval":
            continue

        if _product_matches(parsed.product_query, product):
            matches.append(
                {
                    "product_id": product.product_id,
                    "name": product.name,
                    "stock": product.stock,
                    "available": product.stock > 0,
                }
            )

    return {
        "found": bool(matches),
        "matches": matches[:3],
    }


def _product_matches(query: str, product: Product) -> bool:
    """Return True when the query appears to match the product."""
    query_tokens = {token for token in tokenize(query) if len(token) >= 3}

    if not query_tokens:
        return False

    haystacks = (
        product.name.lower(),
        (product.category or "").lower(),
        product.product_id.lower(),
    )

    return any(token in haystack for token in query_tokens for haystack in haystacks)
