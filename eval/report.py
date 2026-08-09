"""Markdown reporting for the Duka AI eval harness."""

from __future__ import annotations

from eval.schema import EvalResult


def render_report(
    results: tuple[EvalResult, ...],
    mode: str = "guarded",
) -> str:
    """Render evaluation results as a markdown report."""
    total = len(results)
    passed = sum(result.passed for result in results)
    failed = total - passed

    lines: list[str] = []

    lines.append("# Duka AI evaluation report")
    lines.append("")
    lines.append(f"Mode: {mode}")
    lines.append(f"Total scenarios: {total}")
    lines.append(f"Passed: {passed}")
    lines.append(f"Failed: {failed}")
    lines.append("")

    lines.append("## Suites")
    lines.append("")
    lines.append("| Suite | Total | Passed | Failed |")
    lines.append("|---|---:|---:|---:|")

    suite_stats: dict[str, dict[str, int]] = {}

    for result in results:
        stats = suite_stats.setdefault(
            result.suite,
            {"total": 0, "passed": 0},
        )

        stats["total"] += 1

        if result.passed:
            stats["passed"] += 1

    for suite, stats in sorted(suite_stats.items()):
        suite_failed = stats["total"] - stats["passed"]

        lines.append(f"| {suite} | {stats['total']} | {stats['passed']} | {suite_failed} |")

    lines.append("")
    lines.append("## Failures")
    lines.append("")

    failures = [result for result in results if not result.passed]

    if not failures:
        lines.append("No failures.")
    else:
        for result in failures:
            lines.append(f"### {result.scenario_id}")
            lines.append("")

            for failure in result.failures:
                lines.append(f"- {failure}")

            lines.append("")

    return "\n".join(lines) + "\n"
