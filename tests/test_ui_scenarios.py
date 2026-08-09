"""Tests for UI demo scenarios."""

from ui.scenarios import UI_SCENARIOS


def test_ui_scenarios_are_not_empty() -> None:
    """The demo should include curated scenarios."""
    assert len(UI_SCENARIOS) >= 8


def test_ui_scenario_ids_are_unique() -> None:
    """Scenario IDs should be unique."""
    ids = [scenario.id for scenario in UI_SCENARIOS]

    assert len(ids) == len(set(ids))


def test_ui_scenario_labels_are_unique() -> None:
    """Scenario labels should be unique."""
    labels = [scenario.label for scenario in UI_SCENARIOS]

    assert len(labels) == len(set(labels))


def test_ui_scenarios_have_text() -> None:
    """Each scenario should have non-empty text."""
    for scenario in UI_SCENARIOS:
        assert scenario.text.strip()
