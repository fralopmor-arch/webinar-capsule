import pytest
from unittest.mock import patch, MagicMock
from src.youtube_summarizer.cli import run_pipeline

@patch("src.youtube_summarizer.cli.transcript_exists")
@patch("src.youtube_summarizer.cli.get_video_title")
@patch("src.youtube_summarizer.cli.GeminiSummarizer")
@patch("src.youtube_summarizer.cli.get_transcript")
@patch("src.youtube_summarizer.cli.save_transcript")
@patch("src.youtube_summarizer.cli.save_summary")
def test_run_pipeline_success(mock_save_summary, mock_save_transcript, mock_get_transcript, mock_summarizer_class, mock_get_video_title, mock_transcript_exists, tmp_path, monkeypatch):
    # Setup mocks
    mock_transcript_exists.return_value = False
    mock_get_video_title.return_value = "Mock Title"
    mock_get_transcript.return_value = {
        'text': "This is a mock transcript.",
        'language': 'en',
        'is_generated': False
    }
    
    mock_summarizer = MagicMock()
    mock_summarizer.generate_summary.return_value = "Mock summary"
    mock_summarizer_class.return_value = mock_summarizer
    
    # Run pipeline
    run_pipeline(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir=str(tmp_path),
        model="gemini-3.1-flash-lite",
        languages=["en"],
        no_save=False,
        quiet=True
    )
    
    # Assertions
    mock_get_video_title.assert_called_once_with("dQw4w9WgXcQ")
    mock_get_transcript.assert_called_once_with("dQw4w9WgXcQ", ["en"])
    mock_summarizer.generate_summary.assert_called_once_with("This is a mock transcript.")
    mock_save_transcript.assert_called_once()
    mock_save_summary.assert_called_once_with("dQw4w9WgXcQ", "Mock summary", title="Mock Title", output_dir=str(tmp_path))


