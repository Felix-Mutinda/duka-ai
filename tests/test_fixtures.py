"""Tests for fixture loading and referential integrity."""

import pytest
from core.fixtures import (
    FixtureNotFoundError,
    get_order,
    get_payment,
    get_product,
    load_orders,
    load_payments,
    load_policy_documents,
    load_products,
)


def test_products_load_and_are_unique() -> None:
    """Products should load and have unique identifiers."""
    products = load_products()

    assert len(products) >= 3

    product_ids = [product.product_id for product in products]
    assert len(product_ids) == len(set(product_ids))


def test_orders_load_and_are_unique() -> None:
    """Orders should load and have unique identifiers."""
    orders = load_orders()

    assert len(orders) >= 2

    order_ids = [order.order_id for order in orders]
    assert len(order_ids) == len(set(order_ids))


def test_payments_load_and_are_unique() -> None:
    """Payments should load and have unique references."""
    payments = load_payments()

    assert len(payments) >= 2

    references = [payment.reference for payment in payments]
    assert len(references) == len(set(references))


def test_orders_reference_known_products() -> None:
    """Every order item should reference a known product."""
    product_ids = {product.product_id for product in load_products()}

    for order in load_orders():
        for item in order.items:
            assert item in product_ids


def test_payments_reference_known_orders() -> None:
    """Every payment should reference a known order."""
    order_ids = {order.order_id for order in load_orders()}

    for payment in load_payments():
        assert payment.order_id in order_ids


def test_policy_documents_load() -> None:
    """Policy documents should load with non-empty bodies."""
    documents = load_policy_documents()

    assert len(documents) >= 4

    sources = {document.source for document in documents}

    assert "policies/returns.md" in sources
    assert "policies/shipping.md" in sources
    assert "policies/warranty.md" in sources
    assert "policies/mpesa.md" in sources

    for document in documents:
        assert document.title
        assert document.body.strip()


def test_mpesa_policy_requires_escalation_when_uncertain() -> None:
    """The M-Pesa policy should contain the escalation rule."""
    documents = {document.source: document for document in load_policy_documents()}
    mpesa = documents["policies/mpesa.md"]

    assert "escalate" in mpesa.body.lower()


def test_indirect_injection_fixture_exists() -> None:
    """The evaluation fixture for indirect injection should exist."""
    products = {product.product_id: product for product in load_products()}

    assert "PRD-EVAL-INJECTION" in products

    injection_product = products["PRD-EVAL-INJECTION"]
    assert injection_product.category == "eval"
    assert injection_product.description is not None
    assert "lifetime free returns" in injection_product.description.lower()


def test_get_product_returns_product() -> None:
    """Product lookup should work with normalized identifiers."""
    product = get_product("prd-001")

    assert product.product_id == "PRD-001"
    assert product.name == "Oraimo FreePods Pro"


def test_get_order_returns_order() -> None:
    """Order lookup should work with normalized identifiers."""
    order = get_order("dka-1042")

    assert order.order_id == "DKA-1042"
    assert order.status == "out_for_delivery"


def test_get_payment_returns_payment() -> None:
    """Payment lookup should work with normalized references."""
    payment = get_payment("qgh7xklm21")

    assert payment.reference == "QGH7XKLM21"
    assert payment.order_id == "DKA-1043"
    assert payment.requires_human_review is True


def test_get_product_unknown_raises() -> None:
    """Unknown product lookup should raise a fixture error."""
    with pytest.raises(FixtureNotFoundError):
        get_product("PRD-UNKNOWN")


def test_get_order_unknown_raises() -> None:
    """Unknown order lookup should raise a fixture error."""
    with pytest.raises(FixtureNotFoundError):
        get_order("DKA-UNKNOWN")


def test_get_payment_unknown_raises() -> None:
    """Unknown payment lookup should raise a fixture error."""
    with pytest.raises(FixtureNotFoundError):
        get_payment("UNKNOWN123")
