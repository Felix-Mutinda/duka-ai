"""Mock M-Pesa payment status tool."""

from __future__ import annotations

from typing import Any

from core.fixtures import FixtureNotFoundError, get_payment, load_payments
from pydantic import BaseModel, model_validator


class PaymentStatusArgs(BaseModel):
    """Arguments for mock payment status lookup."""

    reference: str | None = None
    order_id: str | None = None

    @model_validator(mode="after")
    def require_reference_or_order_id(self) -> PaymentStatusArgs:
        """Require at least one lookup key."""
        if not self.reference and not self.order_id:
            msg = "Provide either reference or order_id."
            raise ValueError(msg)

        return self


def payment_status(args: dict[str, Any]) -> dict[str, Any]:
    """Look up a mock payment status."""
    parsed = PaymentStatusArgs.model_validate(args)

    payment = None

    if parsed.reference:
        try:
            payment = get_payment(parsed.reference)
        except FixtureNotFoundError:
            payment = None

    if payment is None and parsed.order_id:
        normalized_order_id = parsed.order_id.strip().upper()

        for candidate in load_payments():
            if candidate.order_id == normalized_order_id:
                payment = candidate
                break

    if payment is None:
        return {"found": False}

    return {
        "found": True,
        "reference_masked": _mask_reference(payment.reference),
        "order_id": payment.order_id,
        "status": payment.status,
        "requires_human_review": payment.requires_human_review,
    }


def _mask_reference(reference: str) -> str:
    """Mask a payment reference for safe display."""
    if len(reference) <= 4:
        return "****"

    return f"{reference[:4]}****"
