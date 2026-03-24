"""
app.py — Gradio frontend for Paper-to-Podcast
"""

import os
import gradio as gr
from backend import run_pipeline


def handle_upload(pdf_file, progress=gr.Progress()):
    if pdf_file is None:
        return None, "Please upload a PDF file first."
    try:
        def update_progress(frac, msg):
            progress(frac, desc=msg)

        audio_path, summary = run_pipeline(
            pdf_path=pdf_file,
            progress_callback=update_progress,
        )
        return audio_path, summary

    except ValueError as e:
        return None, f"Error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


with gr.Blocks(title="Paper-to-Podcast", theme=gr.themes.Soft()) as app:

    gr.Markdown("# 🎙️ Paper-to-Podcast\nUpload a research paper PDF and get a podcast episode with two AI hosts.")

    pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
    generate_btn = gr.Button("Generate Podcast", variant="primary", size="lg")
    audio_output = gr.Audio(label="Your Podcast Episode", type="filepath")
    script_output = gr.Markdown()

    generate_btn.click(
        fn=handle_upload,
        inputs=[pdf_input],
        outputs=[audio_output, script_output],
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))