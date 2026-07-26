import pytest
from src.youtube_summarizer.sanitizer import sanitize_transcript

def test_sanitize_empty():
    assert sanitize_transcript("") == ""
    assert sanitize_transcript(None) == ""

def test_sanitize_tags():
    raw = "[Music] Hello (Applause) World!"
    assert sanitize_transcript(raw) == "Hello World!"

def test_sanitize_whitespace():
    raw = "  Hello \u200b   World \n \n "
    assert sanitize_transcript(raw) == "Hello World"
