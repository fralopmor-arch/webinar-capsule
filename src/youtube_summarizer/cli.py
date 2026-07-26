import sys
import io
import time
import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.theme import Theme

from .transcript import parse_video_id, get_transcript, transcribe_audio_fallback, get_video_title
from .sanitizer import sanitize_transcript
from .storage import save_transcript, save_summary, load_transcript, transcript_exists, SUMMARIES_DIR
from .summarizer import GeminiSummarizer

# Reconfigure stdout/stderr encoding to UTF-8 on Windows to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

# Define a professional color theme
custom_theme = Theme({
    "info": "bold cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "progress": "dim white",
})

console = Console(theme=custom_theme)
err_console = Console(theme=custom_theme, stderr=True)

def setup_logging(verbose: bool, quiet: bool):
    level = logging.WARNING
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

def run_pipeline(url: str, output_dir: str, model: str, languages: list, no_save: bool, quiet: bool):
    start_time = time.time()
    
    if not quiet:
        console.print(Panel(
            f"[bold white]YouTube Summarizer[/]\n[progress]Model: {model} | Languages: {', '.join(languages)}[/]",
            border_style="cyan",
            title="[bold cyan]YouTube Webinar Capsule[/]",
            title_align="left"
        ))

    try:
        # 1. Parse URL
        if not quiet:
            console.print("🔍 [info]Parsing YouTube URL...[/]")
        video_id = parse_video_id(url)
        if not quiet:
            console.print(f"   [success]Found Video ID:[/] [bold white]{video_id}[/]")
        
        # Get video title
        title = video_id
        if not quiet:
            with console.status("[progress]Fetching video title...", spinner="dots"):
                title = get_video_title(video_id)
            console.print(f"🎥 [success]Video Title:[/] [bold white]\"{title}\"[/]")
        else:
            title = get_video_title(video_id)
        
        # 2 & 3. Extract Transcript
        transcript_text = ""
        metadata = {}
        
        if not no_save and transcript_exists(video_id):
            if not quiet:
                console.print(f"💾 [info]Found cached transcript for {video_id}, loading...[/]")
            transcript_text = load_transcript(video_id)
            metadata = {'source': 'cache'}
        else:
            if not quiet:
                status_text = f"[progress]Extracting primary transcript ({', '.join(languages)})...[/]"
                with console.status(status_text, spinner="dots"):
                    result = get_transcript(video_id, languages)
            else:
                result = get_transcript(video_id, languages)
            
            if result:
                transcript_text = result['text']
                metadata = {
                    'language': result['language'],
                    'is_generated': result['is_generated'],
                    'source': 'youtube-transcript-api'
                }
                if not quiet:
                    console.print(f"📄 [success]Retrieved YouTube captions[/] [dim]({result['language']})[/]")
            else:
                if not quiet:
                    console.print("⚠️  [warning]No captions found via API. Falling back to audio transcription...[/]")
                    status_text = "[progress]Downloading audio and transcribing via Whisper (this may take a few minutes)...[/]"
                    with console.status(status_text, spinner="dots"):
                        result = transcribe_audio_fallback(url)
                else:
                    result = transcribe_audio_fallback(url)
                
                transcript_text = result['text']
                metadata = {
                    'language': result['language'],
                    'is_generated': result['is_generated'],
                    'source': 'faster-whisper'
                }
                if not quiet:
                    console.print(f"📄 [success]Generated transcript using audio fallback[/] [dim]({result['language']})[/]")
                
            # 4. Sanitize Text
            if not quiet:
                console.print("🧹 [info]Sanitizing transcript text...[/]")
            transcript_text = sanitize_transcript(transcript_text)
            
            # 5. Save Transcript
            if not no_save:
                save_transcript(video_id, transcript_text, metadata)
                if not quiet:
                    console.print("💾 [success]Saved transcript to local cache.[/]")
                
        if not transcript_text:
            raise ValueError("Failed to obtain transcript text.")
            
        # 6. Summarize
        if not quiet:
            status_text = f"[progress]Generating summary with Gemini ({model})...[/]"
            with console.status(status_text, spinner="dots"):
                summarizer = GeminiSummarizer(model_name=model)
                summary = summarizer.generate_summary(transcript_text)
        else:
            summarizer = GeminiSummarizer(model_name=model)
            summary = summarizer.generate_summary(transcript_text)
        
        # 7. Save & Display Summary
        if not no_save:
            summary_file = save_summary(video_id, summary, title=title, output_dir=output_dir)
            if not quiet:
                console.print(f"✨ [success]Summary saved to:[/] [bold cyan]{summary_file}[/]")
            
        elapsed = time.time() - start_time
        if not quiet:
            console.print(f"\n[success]Pipeline completed in {elapsed:.1f} seconds.[/]\n")
            
            console.print(Panel(
                Markdown(summary),
                border_style="green",
                title="[bold green]Generated Summary[/]",
                title_align="center"
            ))
            
    except Exception as e:
        if not quiet:
            err_console.print(f"\n[bold red]Error:[/] [error]{str(e)}[/]")
            if "FFmpeg" in str(e):
                err_console.print("\n[warning]Suggestion: Install FFmpeg via 'winget install \"FFmpeg (Essentials Build)\"'[/]")
            elif "API_KEY" in str(e) or "400" in str(e) or "403" in str(e):
                err_console.print("\n[warning]Suggestion: Check your GEMINI_API_KEY in the .env file.[/]")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="YouTube Video Summarizer using Gemini")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output-dir", default=str(SUMMARIES_DIR), help="Directory to save summaries (default: summaries/)")
    parser.add_argument("--model", default="gemini-3.1-flash-lite", help="Gemini model to use (default: gemini-3.1-flash-lite)")
    parser.add_argument("--language", default="es,en,fr,de,it", help="Comma-separated language codes for captions (default: es,en,fr,de,it)")
    parser.add_argument("--no-save", action="store_true", help="Do not save transcript or summary to disk")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--quiet", action="store_true", help="Suppress all progress output and only show errors")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose, args.quiet)
    
    languages = [lang.strip() for lang in args.language.split(',')]
    
    run_pipeline(
        url=args.url,
        output_dir=args.output_dir,
        model=args.model,
        languages=languages,
        no_save=args.no_save,
        quiet=args.quiet
    )

if __name__ == "__main__":
    main()

