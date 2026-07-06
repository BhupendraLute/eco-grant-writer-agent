"""Thread-safe Gemini LLM client with retry logic and response validation."""

import logging
import threading
import time

from google.genai import Client, types
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from grant_writer.config import LLM_MODEL, load_env

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thread-Safe Singleton Client
# ---------------------------------------------------------------------------

_client_lock = threading.Lock()
_gemini_client: Client | None = None


def get_client() -> Client:
    """Returns a thread-safe cached Gemini Client instance.

    Uses double-check locking to prevent race conditions while
    avoiding lock acquisition on every call after initialization.
    """
    global _gemini_client
    if _gemini_client is None:
        with _client_lock:
            if _gemini_client is None:
                load_env()
                _gemini_client = Client()
                logger.info("Initialized Gemini client")
    return _gemini_client


# ---------------------------------------------------------------------------
# LLM Call Wrapper with Retry & Validation
# ---------------------------------------------------------------------------

class LLMResponseError(Exception):
    """Raised when the LLM returns an invalid or empty response."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def generate(
    contents: str,
    *,
    model: str | None = None,
    config: types.GenerateContentConfig | None = None,
    tools: list | None = None,
    min_response_length: int = 10,
) -> types.GenerateContentResponse:
    """Calls the Gemini API with retry logic, latency tracking, and response validation.

    Args:
        contents: The prompt text to send to the model.
        model: Model identifier (defaults to config.LLM_MODEL).
        config: Optional GenerateContentConfig for response format, etc.
        tools: Optional list of tool functions for function calling.
        min_response_length: Minimum acceptable response length in characters.

    Returns:
        The raw GenerateContentResponse object.

    Raises:
        LLMResponseError: If the response text is empty or below min_response_length.
    """
    client = get_client()
    model_id = model or LLM_MODEL

    # Build config with tools if provided
    effective_config = config
    if tools and not config:
        effective_config = types.GenerateContentConfig(tools=tools)
    elif tools and config:
        # Merge tools into existing config
        effective_config = types.GenerateContentConfig(
            tools=tools,
            response_mime_type=getattr(config, "response_mime_type", None),
        )

    start_time = time.monotonic()
    response = None
    try:
        kwargs = {"model": model_id, "contents": contents}
        if effective_config:
            kwargs["config"] = effective_config
        response = client.models.generate_content(**kwargs)
    except Exception as exc:
        elapsed = time.monotonic() - start_time
        logger.error(
            "LLM call failed: model=%s elapsed=%.2fs error=%s",
            model_id,
            elapsed,
            exc,
        )

        # Fallback to gemini-3.5-flash if the primary model failed and it wasn't already gemini-3.5-flash
        if model_id != "gemini-3.5-flash":
            logger.info("Attempting fallback to gemini-3.5-flash...")
            try:
                fallback_kwargs = {"model": "gemini-3.5-flash", "contents": contents}
                if effective_config:
                    fallback_kwargs["config"] = effective_config
                response = client.models.generate_content(**fallback_kwargs)
                logger.info("Fallback to gemini-3.5-flash succeeded")
                model_id = "gemini-3.5-flash"
            except Exception as fallback_exc:
                logger.error("Fallback to gemini-3.5-flash also failed: %s", fallback_exc)

        # Fallback to gemini-3.1-flash-lite if still failed and it wasn't already gemini-3.1-flash-lite
        if response is None and model_id != "gemini-3.1-flash-lite":
            logger.info("Attempting fallback to gemini-3.1-flash-lite...")
            try:
                fallback_kwargs = {"model": "gemini-3.1-flash-lite", "contents": contents}
                if effective_config:
                    fallback_kwargs["config"] = effective_config
                response = client.models.generate_content(**fallback_kwargs)
                logger.info("Fallback to gemini-3.1-flash-lite succeeded")
                model_id = "gemini-3.1-flash-lite"
            except Exception as fallback_exc:
                logger.error("Fallback to gemini-3.1-flash-lite also failed: %s", fallback_exc)

        if response is None:
            # Check if OpenRouter fallback is configured
            import os
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                load_env()
                api_key = os.environ.get("OPENROUTER_API_KEY")

            if api_key:
                logger.info("Attempting OpenRouter fallback due to Gemini error...")
                try:
                    text = generate_openrouter(contents, config=effective_config)
                    response = MockResponse(text)
                except Exception as or_exc:
                    logger.error("OpenRouter fallback also failed: %s", or_exc)

            if response is None:
                raise exc

    elapsed = time.monotonic() - start_time
    response_text = (response.text or "").strip() if response.text else ""

    logger.info(
        "LLM call: model=%s elapsed=%.2fs response_len=%d has_function_calls=%s",
        model_id,
        elapsed,
        len(response_text),
        bool(response.function_calls),
    )

    # Skip length validation if the response contains function calls
    if not response.function_calls:
        if len(response_text) < min_response_length:
            raise LLMResponseError(
                f"LLM response too short ({len(response_text)} chars, min {min_response_length}). "
                f"Response: {response_text[:200]}"
            )

    return response


class MockResponse:
    """Mock Gemini GenerateContentResponse object for OpenRouter fallbacks."""

    def __init__(self, text: str):
        self.text = text
        self.function_calls = []


def generate_openrouter(contents: str, config: types.GenerateContentConfig | None = None) -> str:
    """Fallback generator that queries free models on OpenRouter via urllib."""
    import json
    import os
    import urllib.request
    import urllib.error

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment")

    # Free tier models to try in sequence (active OpenRouter slugs)
    models = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-4-31b-it:free",
        "meta-llama/llama-3.2-3b-instruct:free",
    ]

    prompt_str = str(contents)
    last_exc = None

    for model_name in models:
        try:
            logger.info("Querying OpenRouter fallback model: %s", model_name)

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt_str}],
            }

            # Handle JSON mode if requested by config
            if config and getattr(config, "response_mime_type", None) == "application/json":
                payload["response_format"] = {"type": "json_object"}

            data = json.dumps(payload).encode("utf-8")

            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/BhupendraLute/eco-grant-writer-agent",
                    "X-Title": "Eco Grant Writer Agent",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                resp_data = json.loads(response.read().decode("utf-8"))

            choices = resp_data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                if text:
                    logger.info("OpenRouter fallback success: model=%s", model_name)
                    return text

            raise ValueError(f"Empty completions returned from model {model_name}")

        except Exception as exc:
            logger.warning("OpenRouter fallback model %s failed: %s", model_name, exc)
            last_exc = exc

    if last_exc:
        raise last_exc
    raise ValueError("All OpenRouter models failed")



def generate_text(
    contents: str,
    *,
    model: str | None = None,
    min_response_length: int = 10,
) -> str:
    """Convenience wrapper that returns just the text from an LLM call."""
    response = generate(contents, model=model, min_response_length=min_response_length)
    return response.text.strip()


def generate_json(
    contents: str,
    *,
    model: str | None = None,
    min_response_length: int = 2,
) -> str:
    """Calls the LLM with JSON response mode and returns the raw JSON string."""
    config = types.GenerateContentConfig(response_mime_type="application/json")
    response = generate(contents, model=model, config=config, min_response_length=min_response_length)
    return response.text.strip()
