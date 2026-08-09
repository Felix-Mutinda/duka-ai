"""Tests for the Duka AI evaluation harness."""

from eval.report import render_report
from eval.runner import run_scenario, run_scenarios
from eval.scenarios import load_scenarios


def test_scenarios_load_and_are_unique() -> None:
    """Scenarios should load with unique IDs."""
    scenarios = load_scenarios()

    assert len(scenarios) >= 10

    ids = [scenario.id for scenario in scenarios]
    assert len(ids) == len(set(ids))


def test_known_benign_scenario_passes() -> None:
    """A known benign scenario should pass."""
    scenarios = {scenario.id: scenario for scenario in load_scenarios(("benign",))}

    result = run_scenario(scenarios["order-status-en"])

    assert result.passed, result.failures


def test_known_redteam_scenario_passes() -> None:
    """A known red-team scenario should pass."""
    scenarios = {scenario.id: scenario for scenario in load_scenarios(("redteam",))}

    result = run_scenario(scenarios["direct-injection"])

    assert result.passed, result.failures


def test_report_renders() -> None:
    """The markdown report should render suite results."""
    results = run_scenarios(("benign",))
    report = render_report(results)

    assert "# Duka AI evaluation report" in report
    assert "benign" in report
    assert "Total scenarios" in report


def test_all_scenarios_pass() -> None:
    """All committed scenarios should pass against the current pipeline."""
    results = run_scenarios()

    failures = [(result.scenario_id, result.failures) for result in results if not result.passed]

    assert not failures
