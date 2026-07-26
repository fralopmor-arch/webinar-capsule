# YouTube Summarizer

A robust command-line tool that extracts transcripts from YouTube videos and generates highly structured, concise summaries using the Google Gemini AI.

## Features
- **URL Parsing**: Automatically extracts video IDs from all standard YouTube URL formats.
- **Smart Captions**: Uses `youtube-transcript-api` to pull high-quality captions, prioritizing multiple languages (es, en, fr, de, it).
- **Audio Fallback**: Automatically falls back to downloading audio and using `faster-whisper` for videos with disabled captions.
- **Gemini Integration**: Uses `gemini-3.1-flash-lite` with exponential backoff and retry logic for robust, high-quality summaries.
- **Caching**: Saves raw transcripts locally to avoid redundant API calls.

## Installation

This project uses `uv` for lightning-fast dependency management.

1. Clone this repository or open the project folder.
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Install system dependencies:
   If you want the Audio Fallback feature to work, you must install `ffmpeg` on your system.
   - **Windows**: `winget install "FFmpeg (Essentials Build)"`
   - **Mac**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key_here...
   ```

## Usage

You can run the script using `uv run` to automatically handle the virtual environment.

**Basic Usage:**
```bash
uv run youtube-summarizer "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Advanced Usage:**
```bash
uv run youtube-summarizer "https://youtu.be/dQw4w9WgXcQ" \
    --output-dir my_summaries/ \
    --model gemini-3.5-flash \
    --language en,es \
    --verbose
```

### CLI Arguments
- `url`: (Required) The YouTube video URL.
- `--output-dir`: Where to save summaries (default: `summaries/`).
- `--model`: Gemini model to use (default: `gemini-3.1-flash-lite`).
- `--language`: Comma-separated languages to prioritize (default: `es,en,fr,de,it`).
- `--no-save`: Disable caching transcripts and saving summaries to disk.
- `--verbose`: Enable debug logging.
- `--quiet`: Suppress progress output and only show errors.

## Troubleshooting

- **`ValueError: GEMINI_API_KEY not set`**: Ensure you have created a `.env` file and added your Google Gemini API key.
- **`Audio file not downloaded` / Whisper failure**: Ensure you have installed `ffmpeg` globally on your OS.
- **`429 Resource Exhausted`**: The tool has built-in retry logic, but if this persists, check your Gemini API quota.
