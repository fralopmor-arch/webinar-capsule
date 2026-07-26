import re
import os
import tempfile
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

def parse_video_id(url: str) -> str:
    """Extracts the 11-character YouTube video ID from a URL."""
    # Common regex pattern
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|/|$)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    # URL parsing fallback
    parsed = urlparse(url)
    vid = None
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        vid = parsed.path.lstrip('/')
    elif parsed.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed.path == '/watch':
            vid = parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.path.startswith(('/embed/', '/v/')):
            vid = parsed.path.split('/')[2]
            
    if vid and len(vid) == 11:
        return vid
        
    raise ValueError(f"Could not extract video ID from URL: {url}")

def get_transcript(video_id: str, languages: list = None) -> dict:
    """
    Fetches transcript for a given video ID.
    Supports manual captions, auto-generated captions, and language translations.
    """
    if languages is None:
        languages = ['es', 'en', 'fr', 'de', 'it']
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)
        
        # 1. Try finding exact manual or generated transcript matching preferred languages
        try:
            transcript = transcript_list.find_transcript(languages)
        except Exception:
            # 2. Try finding ANY available transcript and translate it to preferred language
            try:
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    first_transcript = available_transcripts[0]
                    target_lang = languages[0] if languages else 'en'
                    if first_transcript.is_translatable:
                        transcript = first_transcript.translate(target_lang)
                    else:
                        transcript = first_transcript
                else:
                    return None
            except Exception:
                return None

        data = transcript.fetch()
        text = " ".join([entry.text for entry in data])
        
        return {
            'text': text,
            'language': getattr(transcript, 'language', 'en'),
            'is_generated': getattr(transcript, 'is_generated', True)
        }
    except Exception:
        return None



def transcribe_audio_fallback(url: str) -> dict:
    """
    Fallback method to download audio and transcribe using faster-whisper.
    """
    print(f"Warning: No captions found. Falling back to audio transcription (this may take 5-15 mins).")
    try:
        import yt_dlp
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError("yt-dlp and faster-whisper are required for fallback. Run: uv add yt-dlp faster-whisper")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Support YouTube cookies via file path (YOUTUBE_COOKIES_FILE) or raw cookie text string (YOUTUBE_COOKIES)
        cookies_file = os.getenv("YOUTUBE_COOKIES_FILE")
        cookies_text = os.getenv("YOUTUBE_COOKIES")
        
        if not cookies_file and cookies_text:
            lines = []
            for line in cookies_text.strip().strip("'").strip('"').replace('\\n', '\n').splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Split space or tab separated fields and re-join with tab for Netscape compliance
                parts = line.split()
                if len(parts) >= 7:
                    lines.append("\t".join(parts[:7]))
                elif len(parts) >= 6:
                    lines.append("\t".join(parts))

            if lines:
                cookie_content = "# Netscape HTTP Cookie File\n# http://curl.haxx.se/rfc/cookie_spec.html\n# This is a generated file! Do not edit.\n\n" + "\n".join(lines) + "\n"
                temp_cookie_path = os.path.join(tmpdir, "youtube_cookies.txt")
                with open(temp_cookie_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(cookie_content)
                cookies_file = temp_cookie_path



        ydl_opts = {
            'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
        }
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file

        download_success = False
        last_error = None

        # Try standard download first, then try with specific clients if blocked
        attempts = [
            {},
            {'extractor_args': {'youtube': {'player_client': ['android']}}},
            {'extractor_args': {'youtube': {'player_client': ['ios']}}},
        ]

        for extra in attempts:
            current_opts = ydl_opts.copy()
            current_opts.update(extra)
            try:
                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    ydl.download([url])
                download_success = True
                break
            except Exception as e:
                last_error = e
                continue





                
        if not download_success:
            raise RuntimeError(f"Failed to download audio: {last_error}")

            
        # Find whatever audio file format yt-dlp downloaded (e.g. .m4a, .webm, .ogg)
        downloaded_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.startswith("audio.")]
        if not downloaded_files:
            raise FileNotFoundError("Audio file not downloaded.")
        audio_path = downloaded_files[0]
            
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join(segment.text for segment in segments)
        
        return {
            'text': text,
            'language': info.language,
            'is_generated': True
        }

def get_video_title(video_id: str) -> str:
    """Fetches the video title using official YouTube Data API v3 or yt-dlp fallback."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=api_key)
            response = youtube.videos().list(part="snippet", id=video_id).execute()
            items = response.get("items", [])
            if items:
                return items[0]["snippet"]["title"]
        except Exception:
            pass

    try:
        import yt_dlp
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', video_id)
    except Exception:
        return video_id



