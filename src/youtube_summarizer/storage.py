import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import create_client, Client

TRANSCRIPTS_DIR = Path("transcripts")
SUMMARIES_DIR = Path("summaries")

def get_supabase_client() -> Optional[Client]:
    """Returns a Supabase client if environment variables are present."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

def check_user_rate_limit(user_ip: str, max_requests: int = 3) -> bool:
    """Checks if the user has reached their maximum allowed request limit."""
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("user_requests").select("request_count").eq("ip_address", user_ip).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["request_count"] < max_requests
            return True
        except Exception:
            pass
    return True

def record_user_request(user_ip: str) -> int:
    """Increments the request count for a user IP in Supabase. Returns updated request count."""
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("user_requests").select("request_count").eq("ip_address", user_ip).execute()
            if res.data and len(res.data) > 0:
                current_count = res.data[0]["request_count"] + 1
                supabase.table("user_requests").update({"request_count": current_count, "last_request_at": datetime.now().isoformat()}).eq("ip_address", user_ip).execute()
                return current_count
            else:
                supabase.table("user_requests").insert({"ip_address": user_ip, "request_count": 1, "last_request_at": datetime.now().isoformat()}).execute()
                return 1
        except Exception:
            pass
    return 1


def transcript_exists(video_id: str) -> bool:
    """Checks if a transcript exists in Supabase or local cache."""
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("transcripts").select("id").eq("video_id", video_id).execute()
            if len(res.data) > 0:
                return True
        except Exception:
            pass
    return (TRANSCRIPTS_DIR / f"{video_id}.txt").exists()

def save_transcript(video_id: str, text: str, metadata: Optional[dict] = None, save_to_disk: bool = True) -> Optional[Path]:
    """Saves the raw transcript locally and to Supabase database if connected."""
    filepath = None
    if save_to_disk:
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        filepath = TRANSCRIPTS_DIR / f"{video_id}.txt"
        
        header = f"--- Video ID: {video_id} ---\n"
        header += f"--- Date: {datetime.now().isoformat()} ---\n"
        if metadata:
            for k, v in metadata.items():
                header += f"--- {k}: {v} ---\n"
        header += "-" * 30 + "\n\n"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header + text)

    # Supabase persistence (optional background backup if configured)
    supabase = get_supabase_client()
    if supabase:
        try:
            title = metadata.get("title") if metadata else None
            supabase.table("videos").upsert({"video_id": video_id, "title": title}, on_conflict="video_id").execute()
            
            lang = metadata.get("language", "en") if metadata else "en"
            supabase.table("transcripts").upsert(
                {"video_id": video_id, "language": lang, "content": text, "metadata": metadata or {}},
                on_conflict="video_id"
            ).execute()
        except Exception:
            pass
        
    return filepath

def load_transcript(video_id: str) -> str:
    """Loads a transcript from local disk cache or Supabase."""
    filepath = TRANSCRIPTS_DIR / f"{video_id}.txt"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        separator = "-" * 30 + "\n\n"
        if separator in content:
            return content.split(separator, 1)[1]
        return content

    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("transcripts").select("content").eq("video_id", video_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["content"]
        except Exception:
            pass

    raise FileNotFoundError(f"Transcript for {video_id} not found.")

def save_summary(video_id: str, summary: str, title: Optional[str] = None, output_dir: Optional[Path] = None, model: str = "deepseek-chat", save_to_disk: bool = True) -> Optional[Path]:
    """Saves the summary to local .md file and to Supabase database if connected."""
    filepath = None
    if save_to_disk:
        target_dir = Path(output_dir) if output_dir else SUMMARIES_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if title:
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
            clean_title = re.sub(r'\s+', "_", clean_title)
            clean_title = re.sub(r'_+', "_", clean_title).strip("_")
            filename = f"{clean_title}.md"
        else:
            filename = f"{video_id}_summary.md"
            
        filepath = target_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary)

    # Supabase persistence
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("videos").upsert({"video_id": video_id, "title": title}, on_conflict="video_id").execute()
            supabase.table("summaries").upsert(
                {"video_id": video_id, "model": model, "content": summary},
                on_conflict="video_id"
            ).execute()
        except Exception:
            pass
        
    return filepath





