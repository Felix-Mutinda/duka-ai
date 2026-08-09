"""Core typed schemas for Duka AI.

These schemas are intentionally small and explicit. They form the boundaries
between fixtures, tools, guardrails, pipeline state, and observability.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    """Create a readable prefixed identifier."""
    return f"{prefix}_{uuid4().hex[:12]}"


class RiskLevel(StrEnum):
    """Risk level used by routing and guardrails."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Confidence(StrEnum):
    """Confidence bucket for routing decisions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Intent(StrEnum):
    """Supported MVP intents."""

    ORDER_STATUS = "order_status"
    INVENTORY = "inventory"
    PAYMENT_STATUS = "payment_status"
    POLICY = "policy"
    FRAUD_OR_DISPUTE = "fraud_or_dispute"
    GREETING = "greeting"
    OUT_OF_SCOPE = "out_of_scope"
    UNCLEAR = "unclear"
    INJECTION_ATTEMPT = "injection_attempt"


class ActionType(StrEnum):
    """Final action taken by the pipeline."""

    RESPOND = "respond"
    BLOCK = "block"
    ESCALATE = "escalate"
    CLARIFY = "clarify"


class GateDecision(BaseModel):
    """Decision from the input gate."""

    blocked: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    reasons: list[str] = Field(default_factory=list)
    fallback_response: str | None = None

    @field_validator("reasons")
    @classmethod
    def unique_sorted_reasons(cls, value: list[str]) -> list[str]:
        """Deduplicate and sort reasons for stable traces."""
        return sorted(dict.fromkeys(value))


class RouteDecision(BaseModel):
    """Decision from the intent router."""

    intent: Intent
    confidence: Confidence
    risk_level: RiskLevel = RiskLevel.LOW
    requires_tool: bool = False
    requires_retrieval: bool = False
    requires_escalation: bool = False
    reason: str | None = None


class ToolCall(BaseModel):
    """A structured request to call a tool."""

    call_id: str = Field(default_factory=lambda: new_id("tool"))
    name: str = Field(min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result returned by a tool."""

    call_id: str | None = None
    name: str
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class RetrievedChunk(BaseModel):
    """A chunk retrieved from the knowledge base."""

    source: str
    section: str | None = None
    text: str
    score: float | None = None


class OutputGuardDecision(BaseModel):
    """Decision from the output guard."""

    allowed: bool
    reason: str | None = None
    fallback_response: str | None = None


class OutputGuardContext(BaseModel):
    """Context supplied to the output guard."""

    retrieved_texts: list[str] = Field(default_factory=list)
    payment_requires_human_review: bool = False


class Escalation(BaseModel):
    """Escalation payload for human review."""

    escalation_id: str = Field(default_factory=lambda: new_id("esc"))
    reason: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    summary: str
    suggested_next_steps: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TraceEvent(BaseModel):
    """One structured observability event."""

    trace_id: str
    node: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Product(BaseModel):
    """Product fixture schema."""

    product_id: str = Field(min_length=3)
    name: str = Field(min_length=1)
    category: str | None = None
    price_kes: int = Field(ge=0)
    stock: int = Field(ge=0)
    description: str | None = None

    @field_validator("product_id")
    @classmethod
    def normalize_product_id(cls, value: str) -> str:
        """Normalize product identifiers."""
        return value.strip().upper()


class Order(BaseModel):
    """Order fixture schema."""

    order_id: str
    status: str
    estimated_delivery: str | None = None
    items: list[str] = Field(default_factory=list)
    delivery_area: str | None = None
    payment_status: str

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, value: str) -> str:
        """Normalize and validate demo order identifiers."""
        normalized = value.strip().upper()
        if not normalized.startswith("DKA-"):
            msg = "order_id must start with DKA-"
            raise ValueError(msg)
        return normalized


class Payment(BaseModel):
    """Mock payment fixture schema."""

    reference: str
    order_id: str
    status: str
    amount_kes: int = Field(ge=0)
    requires_human_review: bool = False

    @field_validator("reference")
    @classmethod
    def normalize_reference(cls, value: str) -> str:
        """Normalize payment references."""
        return value.strip().upper()

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, value: str) -> str:
        """Normalize payment order identifiers."""
        normalized = value.strip().upper()
        if not normalized.startswith("DKA-"):
            msg = "order_id must start with DKA-"
            raise ValueError(msg)
        return normalized


class PolicyDocument(BaseModel):
    """A policy document loaded from the fixture knowledge base."""

    source: str
    title: str
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: str) -> str:
        """Policy documents must not be empty."""
        if not value.strip():
            msg = "Policy document body must not be empty."
            raise ValueError(msg)
        return value
