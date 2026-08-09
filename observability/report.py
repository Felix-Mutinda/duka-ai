"""Owner-facing report builders for Duka AI pipeline runs."""

from __future__ import annotations

import json
from typing import Any

from core.guardrails.pii import redact_text

from observability.redaction import redact_structure


def build_owner_report(state: dict[str, Any]) -> dict[str, Any]:
    """Build a redacted owner-facing report from pipeline state."""
    return {
        "schema_version": 1,
        "session_id": str(state.get("session_id", "")),
        "trace_id": str(state.get("trace_id", "")),
        "input_redacted": redact_text(str(state.get("input_text", ""))),
        "final_action": str(state.get("final_action", "")),
        "final_response_redacted": redact_text(str(state.get("final_response", ""))),
        "payment_requires_human_review": bool(state.get("payment_requires_human_review", False)),
        "gate": redact_structure(state.get("gate", {})),
        "route": redact_structure(state.get("route", {})),
        "tool_requests": redact_structure(state.get("tool_requests", [])),
        "tool_results": redact_structure(state.get("tool_results", [])),
        "retrieved_chunks": redact_structure(state.get("retrieved_chunks", [])),
        "output_guard": redact_structure(state.get("output_guard", {})),
        "escalation": redact_structure(state.get("escalation", {})),
        "events": redact_structure(state.get("trace", [])),
    }


def summarize_report(report: dict[str, Any]) -> dict[str, Any]:
    """Build a compact summary for dashboard panels."""
    events = report.get("events", [])

    nodes = [
        str(event.get("node")) for event in events if isinstance(event, dict) and event.get("node")
    ]

    return {
        "session_id": report.get("session_id"),
        "trace_id": report.get("trace_id"),
        "final_action": report.get("final_action"),
        "blocked": bool((report.get("gate") or {}).get("blocked", False)),
        "escalated": bool(report.get("escalation")),
        "payment_requires_human_review": bool(report.get("payment_requires_human_review", False)),
        "tool_result_count": len(report.get("tool_results", [])),
        "retrieved_chunk_count": len(report.get("retrieved_chunks", [])),
        "nodes": nodes,
    }


def render_owner_markdown(report: dict[str, Any]) -> str:
    """Render a redacted owner-facing markdown trace."""
    summary = summarize_report(report)

    lines: list[str] = []

    lines.append("# Duka AI owner trace")
    lines.append("")
    lines.append(f"Session: `{summary.get('session_id')}`")
    lines.append(f"Trace: `{summary.get('trace_id')}`")
    lines.append(f"Final action: `{summary.get('final_action')}`")
    lines.append(f"Blocked: `{summary.get('blocked')}`")
    lines.append(f"Escalated: `{summary.get('escalated')}`")
    lines.append(f"Payment review required: `{summary.get('payment_requires_human_review')}`")
    lines.append("")

    lines.append("## Nodes")
    lines.append("")

    for node in summary.get("nodes", []):
        lines.append(f"- {node}")

    lines.append("")
    lines.append("## Input")
    lines.append("")
    lines.append(str(report.get("input_redacted") or "(empty)"))

    lines.append("")
    lines.append("## Final response")
    lines.append("")
    lines.append(str(report.get("final_response_redacted") or "(empty)"))

    lines.append("")
    lines.append("## Gate")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report.get("gate", {}), indent=2, sort_keys=True))
    lines.append("```")

    lines.append("")
    lines.append("## Route")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report.get("route", {}), indent=2, sort_keys=True))
    lines.append("```")

    lines.append("")
    lines.append("## Output guard")
    lines.append("")
    lines.append("```json")
    lines.append(
        json.dumps(
            report.get("output_guard", {}),
            indent=2,
            sort_keys=True,
        )
    )
    lines.append("```")

    lines.append("")
    lines.append("## Escalation")
    lines.append("")

    escalation = report.get("escalation") or {}

    if escalation:
        lines.append("```json")
        lines.append(json.dumps(escalation, indent=2, sort_keys=True))
        lines.append("```")
    else:
        lines.append("No escalation.")

    lines.append("")

    return "\n".join(lines)
