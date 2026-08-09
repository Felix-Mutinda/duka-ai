"""CLI entrypoint for running Duka AI evaluation scenarios."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from core.config import load_app_config

from eval.report import render_report
from eval.runner import run_scenarios

logger = logging.getLogger("duka.eval")


def main() -> None:
    """Run scenarios and write a markdown report."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Run Duka AI evaluation scenarios.")

    parser.add_argument(
        "--suite",
        action="append",
        help="Suite name to run. Repeat for multiple suites.",
    )

    parser.add_argument(
        "--out",
        default="eval/reports/guarded-run.md",
        help="Output path for the markdown report.",
    )

    args = parser.parse_args()

    suites = tuple(args.suite) if args.suite else None
    results = run_scenarios(suites)

    if not results:
        logger.info("No scenarios found.")
        raise SystemExit(1)

    mode = load_app_config().app.mode
    report = render_report(results, mode=mode)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    logger.info("Wrote %s", out_path)

    if any(not result.passed for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
