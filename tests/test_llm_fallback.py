import pytest
from unittest.mock import MagicMock, patch
from grant_writer.llm import generate, LLMResponseError, MockResponse

def test_gemini_fallback_success():
    """Test that when the primary model fails, fallback to gemini-3.5-flash is triggered and succeeds."""
    mock_client = MagicMock()
    
    # We want generate_content to raise an exception on first call (primary model),
    # but succeed on the second call (fallback model).
    first_resp = MagicMock()
    first_resp.text = "Hello from fallback model"
    first_resp.function_calls = None
    
    call_count = 0
    def mock_generate_content(model, contents, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call fails
            raise Exception("Primary model 429 quota exhausted")
        # Second call succeeds
        return first_resp
        
    mock_client.models.generate_content.side_effect = mock_generate_content
    
    with patch("grant_writer.llm.get_client", return_value=mock_client):
        # Disable environment/OpenRouter config for fallback check
        with patch("os.environ.get", return_value=None):
            resp = generate("Hello", model="gemini-2.5-flash")
            assert resp.text == "Hello from fallback model"
            assert call_count == 2


def test_openrouter_fallback_success():
    """Test that when both primary model and gemini fallbacks fail, OpenRouter fallback is used."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API error")
    
    with patch("grant_writer.llm.get_client", return_value=mock_client):
        with patch("grant_writer.llm.generate_openrouter", return_value="Hello from OpenRouter") as mock_or:
            with patch("os.environ.get", return_value="fake-api-key"):
                resp = generate("Hello", model="gemini-2.5-flash")
                assert isinstance(resp, MockResponse)
                assert resp.text == "Hello from OpenRouter"
                mock_or.assert_called_once()


def test_all_fail():
    """Test that when both Gemini and OpenRouter fail, the original error is raised."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Primary Gemini Error")
    
    with patch("grant_writer.llm.get_client", return_value=mock_client):
        with patch("grant_writer.llm.generate_openrouter", side_effect=Exception("OpenRouter error")):
            with patch("os.environ.get", return_value="fake-api-key"):
                with pytest.raises(Exception, match="Primary Gemini Error"):
                    generate("Hello", model="gemini-2.5-flash")


def test_no_duplicate_gemini_fallbacks():
    """Test that we do not fallback to a model that was already tried as the primary model."""
    mock_client = MagicMock()
    called_models = []
    def mock_generate_content(model, contents, *args, **kwargs):
        called_models.append(model)
        raise Exception("Failed")
        
    mock_client.models.generate_content.side_effect = mock_generate_content
    
    with patch("grant_writer.llm.get_client", return_value=mock_client):
        with patch("os.environ.get", return_value=None):
            with pytest.raises(Exception):
                generate("Hello", model="gemini-3.5-flash")
            
            # The primary model was gemini-3.5-flash.
            # It should fallback to gemini-3.1-flash-lite, but NOT gemini-3.5-flash again.
            assert called_models == ["gemini-3.5-flash", "gemini-3.1-flash-lite"]
