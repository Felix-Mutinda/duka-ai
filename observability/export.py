"""Export helpers for owner-facing observability artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.pipeline.graph import run_pipeline

from observability.report import build_owner_report, render_owner_markdown


def write_owner_report(
    report: dict[str, Any],
    out_dir: Path | str,
    filename: str | None = None,
) -> Path:
    """Write an owner report as JSON."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    name = filename or f"{report.get('trace_id') or 'trace'}.json"

    if not name.endswith(".json"):
        name = f"{name}.json"

    path = out_path / name

    payload = json.dumps(report, indent=2, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8")

    return path


def write_owner_markdown(
    report: dict[str, Any],
    out_dir: Path | str,
    filename: str | None = None,
) -> Path:
    """Write an owner report as Markdown."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    name = filename or f"{report.get('trace_id') or 'trace'}.md"

    if not name.endswith(".md"):
        name = f"{name}.md"

    path = out_path / name
    path.write_text(render_owner_markdown(report), encoding="utf-8")

    return path


def export_pipeline_run(
    input_text: str,
    out_dir: Path | str,
    label: str | None = None,
) -> tuple[Path, Path]:
    """Run the pipeline and export JSON and Markdown owner reports."""
    result = run_pipeline(input_text)
    report = build_owner_report(result)

    json_name = f"{label}.json" if label else None
    markdown_name = f"{label}.md" if label else None

    json_path = write_owner_report(report, out_dir, filename=json_name)
    markdown_path = write_owner_markdown(
        report,
        out_dir,
        filename=markdown_name,
    )

    return json_path, markdown_path
