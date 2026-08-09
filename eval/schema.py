"""Evaluation schema for Duka AI scenarios and results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExpectedAction = Literal["respond", "block", "escalate", "clarify"]


class Scenario(BaseModel):
    """One evaluation scenario."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=3)
    suite: str = "general"
    text: str = Field(min_length=1)

    expected_action: ExpectedAction | None = None
    expected_intent: str | None = None
    expected_tools: list[str] | None = None
    expected_blocked: bool | None = None
    expected_escalation: bool | None = None

    must_contain: list[str] = Field(default_factory=list)
    must_not_contain: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class EvalResult(BaseModel):
    """Result of running one scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    suite: str
    passed: bool
    failures: list[str] = Field(default_factory=list)

    actual_action: str | None = None
    actual_intent: str | None = None
    actual_tools: list[str] = Field(default_factory=list)
    actual_blocked: bool = False
    actual_escalation: bool = False

    final_response: str | None = None
