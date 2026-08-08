"""Fixture loading for the simulated Duka AI shop.

This module loads deterministic local fixtures and validates them using
typed schemas. It intentionally avoids databases and external services.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.schemas import Order, Payment, PolicyDocument, Product

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
POLICY_DIR = DATA_DIR / "policies"


class FixtureNotFoundError(Exception):
    """Raised when a requested fixture does not exist."""


def _read_json(path: Path) -> Any:
    """Read a JSON fixture file."""
    if not path.exists():
        msg = f"Missing fixture file: {path}"
        raise FileNotFoundError(msg)

    return json.loads(path.read_text(encoding="utf-8"))


def _markdown_title(text: str, fallback: str) -> str:
    """Extract the first markdown heading as a title."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()

    return fallback


@lru_cache
def load_products() -> tuple[Product, ...]:
    """Load and validate product fixtures."""
    raw = _read_json(DATA_DIR / "products.json")

    if not isinstance(raw, list):
        msg = "products.json must contain a JSON array."
        raise ValueError(msg)

    return tuple(Product.model_validate(item) for item in raw)


@lru_cache
def load_orders() -> tuple[Order, ...]:
    """Load and validate order fixtures."""
    raw = _read_json(DATA_DIR / "orders.json")

    if not isinstance(raw, list):
        msg = "orders.json must contain a JSON array."
        raise ValueError(msg)

    return tuple(Order.model_validate(item) for item in raw)


@lru_cache
def load_payments() -> tuple[Payment, ...]:
    """Load and validate mock payment fixtures."""
    raw = _read_json(DATA_DIR / "payments.json")

    if not isinstance(raw, list):
        msg = "payments.json must contain a JSON array."
        raise ValueError(msg)

    return tuple(Payment.model_validate(item) for item in raw)


@lru_cache
def load_policy_documents() -> tuple[PolicyDocument, ...]:
    """Load markdown policy documents in deterministic order."""
    if not POLICY_DIR.exists():
        msg = f"Missing policy directory: {POLICY_DIR}"
        raise FileNotFoundError(msg)

    documents: list[PolicyDocument] = []

    for path in sorted(POLICY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = _markdown_title(text, path.stem.replace("_", " ").title())
        source = f"policies/{path.name}"

        documents.append(
            PolicyDocument(
                source=source,
                title=title,
                body=text,
            )
        )

    return tuple(documents)


@lru_cache
def product_index() -> dict[str, Product]:
    """Return products keyed by normalized product_id."""
    return {product.product_id: product for product in load_products()}


@lru_cache
def order_index() -> dict[str, Order]:
    """Return orders keyed by normalized order_id."""
    return {order.order_id: order for order in load_orders()}


@lru_cache
def payment_index() -> dict[str, Payment]:
    """Return payments keyed by normalized reference."""
    return {payment.reference: payment for payment in load_payments()}


def get_product(product_id: str) -> Product:
    """Return a product by identifier."""
    normalized = product_id.strip().upper()

    try:
        return product_index()[normalized]
    except KeyError as exc:
        msg = f"Unknown product_id: {normalized}"
        raise FixtureNotFoundError(msg) from exc


def get_order(order_id: str) -> Order:
    """Return an order by identifier."""
    normalized = order_id.strip().upper()

    try:
        return order_index()[normalized]
    except KeyError as exc:
        msg = f"Unknown order_id: {normalized}"
        raise FixtureNotFoundError(msg) from exc


def get_payment(reference: str) -> Payment:
    """Return a mock payment by reference."""
    normalized = reference.strip().upper()

    try:
        return payment_index()[normalized]
    except KeyError as exc:
        msg = f"Unknown payment reference: {normalized}"
        raise FixtureNotFoundError(msg) from exc
