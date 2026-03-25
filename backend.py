
"""
backend.py — All core logic for Paper-to-Podcast
=================================================
Handles:
  1. PDF text extraction   (pdfplumber)
  2. Podcast script generation (Groq / Llama 3)
  3. Text-to-speech per line   (edge-tts)
  4. Audio merging into one MP3 (pydub)
"""

import os
import asyncio
import tempfile
import threading

import pdfplumber
from groq import Groq
from pydub import AudioSegment
import edge_tts
from dotenv import load_dotenv

# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ─── ffmpeg path (Windows) ────────────────────────────────────────────────────
_FFMPEG_BIN = r"C:\Users\Madhu saravanan\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin"
if _FFMPEG_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _FFMPEG_BIN + os.pathsep + os.environ.get("PATH", "")
AudioSegment.converter = os.path.join(_FFMPEG_BIN, "ffmpeg.exe")
AudioSegment.ffprobe   = os.path.join(_FFMPEG_BIN, "ffprobe.exe")

# ─── Config ───────────────────────────────────────────────────────────────────
GROQ_MODEL      = "llama-3.3-70b-versatile"
MAX_PAPER_CHARS = 8000
HOST_ALEX_VOICE  = "en-US-GuyNeural"    # Run `edge-tts --list-voices` to explore
HOST_JAMIE_VOICE = "en-US-JennyNeural"

# ─────────────────────────────────────────────────────────────────────────────


# ── Step 1: PDF Extraction ───────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Read a PDF file and return all its text."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


# ── Step 2: Script Generation ────────────────────────────────────────────────

def generate_podcast_script(paper_text: str) -> str:
    """
    Send the paper text to Groq (Llama 3) and receive a
    conversational two-host podcast script.
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your-groq-key-here":
        raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")

    client = Groq(api_key=GROQ_API_KEY)

    truncated = paper_text[:MAX_PAPER_CHARS]
    if len(paper_text) > MAX_PAPER_CHARS:
        truncated += "\n\n[Paper continues — summarise based on the above]"

    prompt = f"""You are writing a podcast script for two friendly, enthusiastic hosts:
- Alex: the explainer — breaks down complex ideas simply, loves analogies
- Jamie: the curious one — asks great questions, connects ideas to real life

Your task: Read this research paper and turn it into a lively 5-minute podcast episode.

Rules:
1. Start with Alex giving an exciting intro hook (1-2 sentences)
2. Alternate between Alex and Jamie naturally — aim for 12-18 exchanges total
3. Explain the key findings in plain English — no jargon without explanation
4. Jamie should ask at least 2 "but why does that matter?" style questions
5. End with Jamie summarising the big takeaway in one sentence

Format EVERY line EXACTLY like this (no other text):
ALEX: [what Alex says]
JAMIE: [what Jamie says]

Here is the research paper:
---
{truncated}
---

Podcast script:"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Step 3: Script Parsing ───────────────────────────────────────────────────

def parse_script(script: str) -> list:
    """
    Parse the raw LLM script into a list of speaker turns.
    Returns: [{"host": "ALEX", "text": "..."}, ...]
    """
    lines = []
    for raw_line in script.strip().split("\n"):
        raw_line = raw_line.strip()
        if raw_line.upper().startswith("ALEX:"):
            text = raw_line[5:].strip()
            if text:
                lines.append({"host": "ALEX", "text": text})
        elif raw_line.upper().startswith("JAMIE:"):
            text = raw_line[6:].strip()
            if text:
                lines.append({"host": "JAMIE", "text": text})
    return lines


# ── Step 4: Text-to-Speech ───────────────────────────────────────────────────

async def _tts_async(text: str, voice: str, output_path: str):
    """Async: convert text to speech and save to file using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def text_to_speech(text: str, voice: str, output_path: str):
    """Synchronous wrapper for edge-tts.
    
    Runs the async TTS call in a brand-new thread so that asyncio.run()
    always gets a thread without a running event loop — safe inside Gradio.
    """
    result = {"error": None}

    def _run():
        try:
            asyncio.run(_tts_async(text, voice, output_path))
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join()

    if result["error"] is not None:
        raise result["error"]


# ── Step 5: Audio Merging ────────────────────────────────────────────────────

def generate_audio(script_lines: list) -> str:
    """
    Convert each script line to audio and merge into one MP3.
    Returns the path to the final merged MP3 file.
    """
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=450)  # ms gap between speakers

    tmp_dir = tempfile.gettempdir()

    for i, line in enumerate(script_lines):
        print(f"  Audio {i+1}/{len(script_lines)}: {line['host']}")

        voice = HOST_ALEX_VOICE if line["host"] == "ALEX" else HOST_JAMIE_VOICE
        tmp_path = os.path.join(tmp_dir, f"podcast_line_{i}.mp3")

        text_to_speech(line["text"], voice, tmp_path)

        segment = AudioSegment.from_file(tmp_path)
        combined += segment + pause
        os.remove(tmp_path)

    output_path = os.path.join(tmp_dir, "podcast_final.mp3")
    combined.export(output_path, format="mp3")
    return output_path


# ── Full Pipeline ────────────────────────────────────────────────────────────

def run_pipeline(pdf_path: str, progress_callback=None) -> tuple:
    """
    Full pipeline: PDF path → (audio_path, summary_text)
    progress_callback(fraction, message) is optional — used by the UI.
    """
    def progress(frac, msg):
        print(f"[{int(frac*100)}%] {msg}")
        if progress_callback:
            progress_callback(frac, msg)

    # Step 1
    progress(0.10, "Reading PDF...")
    paper_text = extract_text_from_pdf(pdf_path)
    if not paper_text:
        raise ValueError("Could not extract text. Use a text-based PDF (not a scanned image).")

    # Step 2
    progress(0.30, "Writing podcast script with Groq (Llama 3)...")
    script = generate_podcast_script(paper_text)

    # Step 3
    progress(0.50, "Parsing script...")
    lines = parse_script(script)
    if not lines:
        raise ValueError(f"Script parsing failed. Raw output:\n\n{script}")

    # Step 4 + 5
    progress(0.60, f"Generating voices for {len(lines)} lines (~30-60 seconds)...")
    audio_path = generate_audio(lines)

    script_display = "\n\n".join(f"**{l['host']}:** {l['text']}" for l in lines)
    summary = (
        f"Done!  |  Paper: {len(paper_text):,} chars  "
        f"|  {len(lines)} exchanges  "
        f"|  Groq + edge-tts (free)\n\n---\n\n{script_display}"
    )

    progress(1.0, "Done!")
    return audio_path, summary