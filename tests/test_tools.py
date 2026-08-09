"""Tests for Duka AI tools."""

from core.schemas import ToolCall
from tools.registry import call_tool


def test_order_lookup_success() -> None:
    """Order lookup should return structured order data."""
    result = call_tool(
        ToolCall(
            name="order_lookup",
            args={"order_id": "DKA-1042"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is True
    assert result.data["status"] == "out_for_delivery"


def test_order_lookup_unknown_order() -> None:
    """Unknown orders should fail safely."""
    result = call_tool(
        ToolCall(
            name="order_lookup",
            args={"order_id": "DKA-9999"},
        )
    )

    assert result.ok is False
    assert result.error is not None


def test_inventory_check_in_stock() -> None:
    """Inventory lookup should detect in-stock products."""
    result = call_tool(
        ToolCall(
            name="inventory_check",
            args={"product_query": "Oraimo FreePods Pro"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is True
    assert result.data["matches"][0]["available"] is True


def test_inventory_check_out_of_stock() -> None:
    """Inventory lookup should detect out-of-stock products."""
    result = call_tool(
        ToolCall(
            name="inventory_check",
            args={"product_query": "Anker PowerBank"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is True
    assert result.data["matches"][0]["available"] is False


def test_inventory_check_excludes_eval_products() -> None:
    """Evaluation fixtures should not be surfaced to customers."""
    result = call_tool(
        ToolCall(
            name="inventory_check",
            args={"product_query": "Test Speaker"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is False


def test_payment_status_by_reference_pending_review() -> None:
    """Pending payment references should require human review."""
    result = call_tool(
        ToolCall(
            name="payment_status",
            args={"reference": "QGH7XKLM21"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is True
    assert result.data["requires_human_review"] is True
    assert "QGH7XKLM21" not in result.data["reference_masked"]


def test_payment_status_by_order_completed() -> None:
    """Completed payments should not require human review."""
    result = call_tool(
        ToolCall(
            name="payment_status",
            args={"order_id": "DKA-1042"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is True
    assert result.data["requires_human_review"] is False


def test_payment_status_not_found() -> None:
    """Unknown payment references should return found=False."""
    result = call_tool(
        ToolCall(
            name="payment_status",
            args={"reference": "ZZZ123456"},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["found"] is False


def test_payment_status_requires_reference_or_order() -> None:
    """Payment lookup should require at least one lookup key."""
    result = call_tool(
        ToolCall(
            name="payment_status",
            args={},
        )
    )

    assert result.ok is False


def test_knowledge_base_search_returns_policy_chunks() -> None:
    """Knowledge base search should return sourced policy chunks."""
    result = call_tool(
        ToolCall(
            name="knowledge_base_search",
            args={"query": "return policy", "top_k": 3},
        )
    )

    assert result.ok is True
    assert result.data is not None
    assert len(result.data["results"]) >= 1
    assert result.data["results"][0]["source"]


def test_unknown_tool_fails_safely() -> None:
    """Unknown tools should return structured errors."""
    result = call_tool(
        ToolCall(
            name="unknown_tool",
            args={},
        )
    )

    assert result.ok is False
    assert result.error is not None


def test_invalid_tool_args_fail_safely() -> None:
    """Invalid tool arguments should return structured errors."""
    result = call_tool(
        ToolCall(
            name="order_lookup",
            args={},
        )
    )

    assert result.ok is False
    assert result.error is not None
