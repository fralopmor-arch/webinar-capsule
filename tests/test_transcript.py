import pytest
from src.youtube_summarizer.transcript import parse_video_id, get_transcript

def test_parse_video_id():
    # standard
    assert parse_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # mobile / share
    assert parse_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # with timestamp
    assert parse_video_id("https://youtu.be/dQw4w9WgXcQ?t=10") == "dQw4w9WgXcQ"
    # embed
    assert parse_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
def test_parse_invalid_id():
    with pytest.raises(ValueError):
        parse_video_id("https://www.youtube.com/watch?v=short")

from unittest.mock import patch, MagicMock
from youtube_transcript_api import TranscriptsDisabled

@patch("src.youtube_summarizer.transcript.YouTubeTranscriptApi")
def test_get_transcript_success(mock_api_class):
    mock_api_instance = MagicMock()
    mock_api_class.return_value = mock_api_instance
    
    mock_list = MagicMock()
    mock_api_instance.list.return_value = mock_list
    
    mock_transcript = MagicMock()
    mock_transcript.language = "en"
    mock_transcript.is_generated = False
    
    mock_snippet = MagicMock()
    mock_snippet.text = "Hello world"
    mock_transcript.fetch.return_value = [mock_snippet]
    
    mock_list.find_transcript.return_value = mock_transcript
    
    result = get_transcript("dQw4w9WgXcQ")
    
    assert result is not None
    assert result['text'] == "Hello world"
    assert result['language'] == "en"

@patch("src.youtube_summarizer.transcript.YouTubeTranscriptApi")
def test_get_transcript_fallback(mock_api_class):
    mock_api_instance = MagicMock()
    mock_api_class.return_value = mock_api_instance
    mock_api_instance.list.side_effect = TranscriptsDisabled("test")
    
    result = get_transcript("dQw4w9WgXcQ")
    assert result is None
