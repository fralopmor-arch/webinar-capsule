import sys
import time
import argparse
import logging
from pathlib import Path
from .transcript import parse_video_id, get_transcript, transcribe_audio_fallback, get_video_title
from .sanitizer import sanitize_transcript
from .storage import save_transcript, save_summary, load_transcript, transcript_exists, SUMMARIES_DIR
from .summarizer import GeminiSummarizer

def setup_logging(verbose: bool, quiet: bool):
    level = logging.WARNING
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

def log_progress(msg: str, quiet: bool):
    if not quiet:
        print(f"[*] {msg}")

def run_pipeline(url: str, output_dir: str, model: str, languages: list, no_save: bool, quiet: bool):
    start_time = time.time()
    
    try:
        # 1. Parse URL
        log_progress("Parsing URL...", quiet)
        video_id = parse_video_id(url)
        log_progress(f"Found Video ID: {video_id}", quiet)
        
        # Get video title
        log_progress("Fetching video title...", quiet)
        title = get_video_title(video_id)
        
        # 2 & 3. Extract Transcript
        transcript_text = ""
        metadata = {}
        
        if not no_save and transcript_exists(video_id):
            log_progress(f"Found cached transcript for {video_id}, loading...", quiet)
            transcript_text = load_transcript(video_id)
            metadata = {'source': 'cache'}
        else:
            log_progress(f"Extracting primary transcript (languages: {', '.join(languages)})...", quiet)
            result = get_transcript(video_id, languages)
            
            if result:
                transcript_text = result['text']
                metadata = {
                    'language': result['language'],
                    'is_generated': result['is_generated'],
                    'source': 'youtube-transcript-api'
                }
            else:
                log_progress("No captions found via API. Falling back to audio transcription...", quiet)
                result = transcribe_audio_fallback(url)
                transcript_text = result['text']
                metadata = {
                    'language': result['language'],
                    'is_generated': result['is_generated'],
                    'source': 'faster-whisper'
                }
                
            # 4. Sanitize Text
            log_progress("Sanitizing transcript text...", quiet)
            transcript_text = sanitize_transcript(transcript_text)
            
            # 5. Save Transcript
            if not no_save:
                save_transcript(video_id, transcript_text, metadata)
                log_progress(f"Saved transcript to cache.", quiet)
                
        if not transcript_text:
            raise ValueError("Failed to obtain transcript text.")
            
        # 6. Summarize
        log_progress(f"Summarizing with {model}...", quiet)
        summarizer = GeminiSummarizer(model_name=model)
        summary = summarizer.generate_summary(transcript_text)
        
        # 7. Save & Display Summary
        if not no_save:
            summary_file = save_summary(video_id, summary, title=title, output_dir=output_dir)
            log_progress(f"Summary saved to {summary_file}", quiet)
            
        elapsed = time.time() - start_time
        log_progress(f"Pipeline completed in {elapsed:.1f} seconds.\n", quiet)
        
        if not quiet:
            print("=== SUMMARY ===")
            print(summary)
            print("===============\n")
            
    except Exception as e:
        if not quiet:
            print(f"\n[!] Error: {str(e)}", file=sys.stderr)
            if "FFmpeg" in str(e):
                print("    Suggestion: Install FFmpeg via 'winget install \"FFmpeg (Essentials Build)\"'", file=sys.stderr)
            elif "API_KEY" in str(e) or "400" in str(e) or "403" in str(e):
                print("    Suggestion: Check your GEMINI_API_KEY in the .env file.", file=sys.stderr)
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
