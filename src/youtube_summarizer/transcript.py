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
    Fetches the primary transcript for a given video ID.
    Returns a dict with 'text', 'language', and 'is_generated'.
    """
    if languages is None:
        languages = ['es', 'en', 'fr', 'de', 'it']
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)
        transcript = transcript_list.find_transcript(languages)
        
        data = transcript.fetch()
        text = " ".join([entry.text for entry in data])
        
        return {
            'text': text,
            'language': transcript.language,
            'is_generated': transcript.is_generated
        }
    except Exception as e:
        # Catch IP blocks or transcript unavailable exceptions to trigger Whisper fallback
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
            # Unescape newlines if user pasted single-line string with \n or quotes
            clean_cookies = cookies_text.strip().strip("'").strip('"').replace('\\n', '\n')
            if not clean_cookies.startswith("# Netscape"):
                clean_cookies = "# Netscape HTTP Cookie File\n" + clean_cookies
            
            temp_cookie_path = os.path.join(tmpdir, "youtube_cookies.txt")
            with open(temp_cookie_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(clean_cookies + "\n")
            cookies_file = temp_cookie_path


        # Array of fallback player clients for yt-dlp to bypass YouTube bot blocks
        client_options = [
            ['android_creator', 'android'],
            ['ios', 'mweb'],
            ['tvhtml5', 'web'],
            ['web']
        ]
        
        download_success = False
        last_error = None
        
        for clients in client_options:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': clients
                    }
                }
            }
            if cookies_file and os.path.exists(cookies_file):
                ydl_opts['cookiefile'] = cookies_file
                
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
    """Fetches the video title using yt-dlp."""
    try:
        import yt_dlp
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'tvhtml5', 'web']
                }
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', video_id)
    except Exception:
        return video_id


