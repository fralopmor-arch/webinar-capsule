import pytest
from unittest.mock import patch, MagicMock
from src.youtube_summarizer.summarizer import GeminiSummarizer, should_retry_api_error
from google.genai.errors import APIError

def test_should_retry():
    error_429 = MagicMock(spec=APIError)
    error_429.code = 429
    assert should_retry_api_error(error_429) == True
    
    error_500 = MagicMock(spec=APIError)
    error_500.code = 500
    assert should_retry_api_error(error_500) == True
    
    error_400 = MagicMock(spec=APIError)
    error_400.code = 400
    assert should_retry_api_error(error_400) == False
    
    assert should_retry_api_error(ValueError("test")) == False

@patch("src.youtube_summarizer.summarizer.genai.Client")
def test_summarizer_success(mock_client_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "This is a summary."
    mock_client.models.generate_content.return_value = mock_response
    
    summarizer = GeminiSummarizer()
    res = summarizer.generate_summary("Transcript text")
    
    assert res == "This is a summary."
    mock_client.models.generate_content.assert_called_once()
