"""Tests for observability redaction, reporting, and export."""

from __future__ import annotations

import json
from pathlib import Path

from core.pipeline.graph import run_pipeline
from observability.export import export_pipeline_run, write_owner_report
from observability.redaction import redact_structure
from observability.report import build_owner_report, summarize_report


def test_redact_structure_redacts_nested_sensitive_values() -> None:
    """Nested phones and emails should be redacted."""
    value = {
        "customer": {
            "phone": "0712345678",
        },
        "notes": [
            "Email jane@example.com",
        ],
    }

    redacted = redact_structure(value)
    serialized = json.dumps(redacted)

    assert "0712345678" not in serialized
    assert "jane@example.com" not in serialized


def test_build_owner_report_redacts_payment_reference() -> None:
    """Owner reports should not contain raw payment references."""
    result = run_pipeline("I paid na M-Pesa but my order is still pending. Reference QGH7XKLM21.")

    report = build_owner_report(result)
    serialized = json.dumps(report)

    assert "QGH7XKLM21" not in serialized
    assert report["final_action"] == "escalate"


def test_build_owner_report_contains_nodes() -> None:
    """Owner reports should include pipeline node traces."""
    result = run_pipeline("Where is order DKA-1042?")

    report = build_owner_report(result)

    nodes = [event["node"] for event in report["events"] if isinstance(event, dict)]

    assert "apply_input_gate" in nodes
    assert "execute_tools" in nodes


def test_summarize_report_fields() -> None:
    """Owner summaries should expose dashboard-friendly fields."""
    result = run_pipeline("Where is order DKA-1042?")

    report = build_owner_report(result)
    summary = summarize_report(report)

    assert summary["final_action"] == "respond"
    assert summary["blocked"] is False
    assert summary["escalated"] is False
    assert summary["tool_result_count"] >= 1
    assert "apply_input_gate" in summary["nodes"]


def test_write_owner_report(tmp_path: Path) -> None:
    """Owner reports should be writable as JSON."""
    result = run_pipeline("Where is order DKA-1042?")

    report = build_owner_report(result)
    path = write_owner_report(report, tmp_path, filename="order.json")

    assert path.exists()

    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded["final_action"] == "respond"
    assert loaded["input_redacted"]


def test_export_pipeline_run_creates_json_and_markdown(
    tmp_path: Path,
) -> None:
    """Pipeline export should create both JSON and Markdown artifacts."""
    json_path, markdown_path = export_pipeline_run(
        "Where is order DKA-1042?",
        tmp_path,
        label="order",
    )

    assert json_path.exists()
    assert markdown_path.exists()
    assert json_path.name == "order.json"
    assert markdown_path.name == "order.md"
