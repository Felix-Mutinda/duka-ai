"""Scenario loading for the Duka AI eval harness."""

from __future__ import annotations

import json
from pathlib import Path

from eval.schema import Scenario

SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"


def load_scenarios(
    suites: tuple[str, ...] | None = None,
) -> tuple[Scenario, ...]:
    """Load scenarios from JSONL files.

    Each file name becomes the suite name unless the scenario explicitly
    provides a suite.
    """
    if not SCENARIOS_DIR.exists():
        msg = f"Missing scenario directory: {SCENARIOS_DIR}"
        raise FileNotFoundError(msg)

    scenarios: list[Scenario] = []

    for path in sorted(SCENARIOS_DIR.glob("*.jsonl")):
        suite_name = path.stem

        if suites and suite_name not in suites:
            continue

        lines = path.read_text(encoding="utf-8").splitlines()

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as exc:
                msg = f"Invalid JSON in {path}:{line_number}"
                raise ValueError(msg) from exc

            data.setdefault("suite", suite_name)
            scenarios.append(Scenario.model_validate(data))

    return tuple(scenarios)
