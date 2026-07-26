import os
import pytest
from pathlib import Path
from src.youtube_summarizer.storage import (
    save_transcript, load_transcript, transcript_exists,
    save_summary
)

def test_transcript_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("src.youtube_summarizer.storage.TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr("src.youtube_summarizer.storage.get_supabase_client", lambda: None)
    
    video_id = "test_vid_123"
    text = "This is a test transcript."
    
    assert not transcript_exists(video_id)
    
    save_transcript(video_id, text, {"source": "test"}, save_to_disk=True)
    assert transcript_exists(video_id)
    
    loaded = load_transcript(video_id)
    assert loaded == text

def test_summary_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("src.youtube_summarizer.storage.SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr("src.youtube_summarizer.storage.get_supabase_client", lambda: None)
    
    video_id = "test_vid_123"
    text = "This is a summary."
    
    path = save_summary(video_id, text, save_to_disk=True)
    assert path is not None
    assert path.exists()
    assert path.read_text(encoding="utf-8") == text

