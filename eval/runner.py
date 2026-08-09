"""Scenario runner for the Duka AI eval harness."""

from __future__ import annotations

from typing import Any

from core.pipeline.graph import run_pipeline

from eval.scenarios import load_scenarios
from eval.schema import EvalResult, Scenario


def run_scenarios(
    suites: tuple[str, ...] | None = None,
) -> tuple[EvalResult, ...]:
    """Load and run evaluation scenarios."""
    scenarios = load_scenarios(suites)

    return tuple(run_scenario(scenario) for scenario in scenarios)


def run_scenario(scenario: Scenario) -> EvalResult:
    """Run one scenario through the pipeline and evaluate expectations."""
    result = run_pipeline(scenario.text)

    failures: list[str] = []

    actual_action = str(result.get("final_action") or "")
    actual_blocked = bool((result.get("gate") or {}).get("blocked", False))
    actual_intent = str((result.get("route") or {}).get("intent") or "")
    actual_tools = _tool_names(result.get("tool_results", []))
    actual_escalation = bool(result.get("escalation"))
    final_response = str(result.get("final_response") or "")

    if scenario.expected_action is not None and actual_action != scenario.expected_action:
        failures.append(f"expected action '{scenario.expected_action}', got '{actual_action}'")

    if scenario.expected_blocked is not None and actual_blocked != scenario.expected_blocked:
        failures.append(f"expected blocked '{scenario.expected_blocked}', got '{actual_blocked}'")

    if scenario.expected_intent is not None and actual_intent != scenario.expected_intent:
        failures.append(f"expected intent '{scenario.expected_intent}', got '{actual_intent}'")

    if scenario.expected_tools is not None:
        expected_tools = sorted(scenario.expected_tools)

        if actual_tools != expected_tools:
            failures.append(f"expected tools {expected_tools}, got {actual_tools}")

    if (
        scenario.expected_escalation is not None
        and actual_escalation != scenario.expected_escalation
    ):
        failures.append(
            f"expected escalation '{scenario.expected_escalation}', got '{actual_escalation}'"
        )

    lower_response = final_response.lower()

    for required in scenario.must_contain:
        if required.lower() not in lower_response:
            failures.append(f"response missing required text: '{required}'")

    for forbidden in scenario.must_not_contain:
        if forbidden.lower() in lower_response:
            failures.append(f"response contains forbidden text: '{forbidden}'")

    return EvalResult(
        scenario_id=scenario.id,
        suite=scenario.suite,
        passed=not failures,
        failures=failures,
        actual_action=actual_action or None,
        actual_intent=actual_intent or None,
        actual_tools=actual_tools,
        actual_blocked=actual_blocked,
        actual_escalation=actual_escalation,
        final_response=final_response,
    )


def _tool_names(tool_results: list[dict[str, Any]]) -> list[str]:
    """Extract sorted unique tool names from tool results."""
    names = {str(result.get("name")) for result in tool_results if result.get("name")}

    return sorted(names)
