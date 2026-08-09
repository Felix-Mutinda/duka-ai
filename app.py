"""Duka AI Gradio entrypoint."""

from ui.interface import create_app

demo = create_app()
demo.queue()

if __name__ == "__main__":
    demo.launch()
