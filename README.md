# 🎙️ Paper-to-Podcast

Convert any research paper PDF into a lively podcast episode with two AI hosts — **Alex** and **Jamie** — using Groq (Llama 3), Edge TTS, and Gradio.

## Demo

Upload a PDF → get a full podcast MP3 with a generated transcript, all for free.

---

## Features

- 📄 **PDF text extraction** via `pdfplumber`
- 🤖 **AI script generation** using Groq's Llama 3.3 70B model
- 🗣️ **Dual-voice text-to-speech** via Microsoft Edge TTS (free, no API key needed)
- 🎵 **Audio merging** into a single MP3 with `pydub` + ffmpeg
- 🖥️ **Clean web UI** built with Gradio

---

## Project Structure

```
paper-to-podcast/
├── app.py          # Gradio frontend
├── backend.py      # Core pipeline logic
├── requirements.txt
└── .env            # Your API keys (not committed)
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/paper-to-podcast.git
cd paper-to-podcast
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install ffmpeg (Windows)

Download from [ffmpeg.org](https://ffmpeg.org/download.html) and extract it. Then update the path in `backend.py`:

```python
_FFMPEG_BIN = r"C:\path\to\ffmpeg\bin"
```

### 4. Set up your Groq API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 5. Run the app

```bash
python app.py
```

Open `http://127.0.0.1:7860` in your browser.

---

## Usage

1. Upload a **text-based PDF** (not a scanned image)
2. Click **Generate Podcast**
3. Wait ~1–2 minutes while the pipeline runs
4. Listen to your podcast episode and read the generated script

---

## Tech Stack

| Component | Library |
|-----------|---------|
| PDF Extraction | `pdfplumber` |
| LLM Script | `groq` (Llama 3.3 70B) |
| Text-to-Speech | `edge-tts` |
| Audio Merging | `pydub` + ffmpeg |
| Web UI | `gradio` |

---

## Notes

- Only **text-based PDFs** work (not scanned/image PDFs)
- The Groq free tier is sufficient for this project
- Edge TTS is completely free with no API key required

---

## License

MIT License
