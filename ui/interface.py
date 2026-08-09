"""Gradio interface for the Duka AI demo."""

from __future__ import annotations

from typing import Any

import gradio as gr

from ui.actions import new_session, process_message, reset_session
from ui.scenarios import UI_SCENARIOS, UiScenario


def create_app() -> gr.Blocks:
    """Build the Duka AI Gradio demo."""
    with gr.Blocks(title="Duka AI") as demo:
        session_state = gr.State(None)

        gr.Markdown(
            """
            # Duka AI

            Simulated, guardrail-first shop assistant.

            The left panel shows the customer conversation.
            The right panel shows the owner-facing trace.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="Customer",
                    # type="messages",
                    height=420,
                    value=[],
                )

                user_input = gr.Textbox(
                    label="Customer message",
                    placeholder="Type a message",
                    lines=2,
                )

                with gr.Row():
                    send_button = gr.Button("Send", variant="primary")
                    reset_button = gr.Button("Reset")

                gr.Markdown("### Scenarios")

                scenario_buttons: list[tuple[UiScenario, gr.Button]] = []

                for scenario in UI_SCENARIOS:
                    button = gr.Button(scenario.label)
                    scenario_buttons.append((scenario, button))

            with gr.Column(scale=1):
                gr.Markdown("### Owner panel")

                summary_json = gr.JSON(
                    label="Summary",
                    value={},
                )

                with gr.Tabs():
                    with gr.Tab("Trace report"):
                        report_json = gr.JSON(
                            label="Trace report",
                            value={},
                        )

                    with gr.Tab("Markdown"):
                        markdown_panel = gr.Markdown("")

        outputs = [
            user_input,
            session_state,
            chatbot,
            summary_json,
            report_json,
            markdown_panel,
        ]

        def on_message(
            text: str,
            session: dict[str, Any] | None,
        ):
            session, history, summary, report, markdown = process_message(
                text,
                session,
            )

            return "", session, history, summary, report, markdown

        def on_reset():
            session, history, summary, report, markdown = reset_session()

            return "", session, history, summary, report, markdown

        def make_scenario_handler(text: str):
            def handler(session: dict[str, Any] | None):
                fresh_session = new_session()

                (
                    session,
                    history,
                    summary,
                    report,
                    markdown,
                ) = process_message(text, fresh_session)

                return "", session, history, summary, report, markdown

            return handler

        user_input.submit(
            on_message,
            inputs=[user_input, session_state],
            outputs=outputs,
        )

        send_button.click(
            on_message,
            inputs=[user_input, session_state],
            outputs=outputs,
        )

        reset_button.click(
            on_reset,
            inputs=[],
            outputs=outputs,
        )

        for scenario, button in scenario_buttons:
            button.click(
                make_scenario_handler(scenario.text),
                inputs=[session_state],
                outputs=outputs,
            )

    return demo
