from __future__ import annotations

from typing import Any

import gradio as gr

from main import build_html_report, send_html_report


def process_uploaded_files(files: list[Any] | None) -> tuple[str, str]:
    """Process uploaded `.eml` files and return UI status plus HTML preview.

    Args:
        files: Gradio-uploaded file objects with local temp paths.

    Returns:
        A status message and the rendered HTML report.
    """
    if not files:
        return "Upload at least one .eml file.", ""

    html_report = build_html_report([file.name for file in files])
    try:
        send_html_report(html_report)
    except Exception as exc:
        return f"Processed {len(files)} file(s), but email sending failed: {exc}", html_report
    return f"Processed {len(files)} file(s) and sent the report email.", html_report


with gr.Blocks(title="Meter Reading Report") as demo:
    gr.Markdown("# Meter Reading Report")
    gr.Markdown("Upload one or more `.eml` files, then click **Process** to email the report and preview it here.")

    file_input = gr.File(
        label="Email Files",
        file_count="multiple",
        # file_types=[".eml"],
    )
    process_button = gr.Button("Process")
    status_output = gr.Textbox(label="Status", interactive=False)
    html_output = gr.HTML(label="Report Preview")

    process_button.click(
        fn=process_uploaded_files,
        inputs=file_input,
        outputs=[status_output, html_output],
    )


if __name__ == "__main__":
    # this code is always the same, the code here only runs when im running the file directly. 'name' here does NOT come from app, as in app.py
    # it is automatically set by python depending on where the code is being run.
    # it is also to prevent file from accidentally executing when we import a function from it for example.
    demo.launch()
