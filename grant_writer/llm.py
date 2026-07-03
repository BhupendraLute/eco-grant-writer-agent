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
        raise

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
