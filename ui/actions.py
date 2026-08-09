"""UI session actions for the Duka AI demo.

These functions are intentionally UI-agnostic. They can be tested without
launching a Gradio server.
"""

from __future__ import annotations

from typing import Any

from core.pipeline.graph import run_pipeline
from core.schemas import new_id
from observability.report import (
    build_owner_report,
    render_owner_markdown,
    summarize_report,
)

ChatHistory = list[dict[str, str]]


def new_session() -> dict[str, Any]:
    """Create a new UI session."""
    return {
        "session_id": new_id("sess"),
        "history": [],
        "report": {},
        "summary": {},
        "markdown": "",
    }


def reset_session() -> tuple[
    dict[str, Any],
    ChatHistory,
    dict[str, Any],
    dict[str, Any],
    str,
]:
    """Reset the UI session."""
    session = new_session()

    return session, [], {}, {}, ""


def process_message(
    text: str,
    session: dict[str, Any] | None,
) -> tuple[
    dict[str, Any],
    ChatHistory,
    dict[str, Any],
    dict[str, Any],
    str,
]:
    """Process one customer message and build owner-facing artifacts."""
    session = dict(session or new_session())

    if not text.strip():
        return (
            session,
            list(session.get("history", [])),
            session.get("summary", {}),
            session.get("report", {}),
            session.get("markdown", ""),
        )

    result = run_pipeline(
        text,
        session_id=str(session.get("session_id") or new_id("sess")),
    )

    report = build_owner_report(result)
    summary = summarize_report(report)
    markdown = render_owner_markdown(report)

    history: ChatHistory = list(session.get("history", []))

    history.append(
        {
            "role": "user",
            "content": text,
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": str(result.get("final_response", "")),
        }
    )

    session.update(
        {
            "history": history,
            "report": report,
            "summary": summary,
            "markdown": markdown,
        }
    )

    return session, history, summary, report, markdown
