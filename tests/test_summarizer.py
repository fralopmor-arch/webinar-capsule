import pytest
from unittest.mock import patch, MagicMock
from src.youtube_summarizer.summarizer import DeepSeekSummarizer, GeminiSummarizer, should_retry_api_error
from openai import APIError, APIStatusError, RateLimitError, APIConnectionError, InternalServerError

def test_should_retry():
    # RateLimitError
    error_rate = MagicMock(spec=RateLimitError)
    assert should_retry_api_error(error_rate) == True

    # APIConnectionError
    error_conn = MagicMock(spec=APIConnectionError)
    assert should_retry_api_error(error_conn) == True

    # InternalServerError
    error_server = MagicMock(spec=InternalServerError)
    assert should_retry_api_error(error_server) == True

    # APIStatusError status codes
    error_429 = MagicMock(spec=APIStatusError)
    error_429.status_code = 429
    assert should_retry_api_error(error_429) == True
    
    error_500 = MagicMock(spec=APIStatusError)
    error_500.status_code = 500
    assert should_retry_api_error(error_500) == True
    
    error_400 = MagicMock(spec=APIStatusError)
    error_400.status_code = 400
    assert should_retry_api_error(error_400) == False
    
    assert should_retry_api_error(ValueError("test")) == False

@patch("src.youtube_summarizer.summarizer.openai.OpenAI")
def test_deepseek_summarizer_success(mock_openai_class, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy-key")
    
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a DeepSeek summary."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    summarizer = DeepSeekSummarizer(model_name="deepseek-chat")
    res = summarizer.generate_summary("Transcript text", target_language="es")
    
    assert res == "This is a DeepSeek summary."
    mock_client.chat.completions.create.assert_called_once()
    mock_openai_class.assert_called_once_with(api_key="dummy-key", base_url="https://api.deepseek.com")
