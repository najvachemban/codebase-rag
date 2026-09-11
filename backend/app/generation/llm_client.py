"""
Phase 5, Step 2: LLM client for answer generation (Gemini API).

Isolates the external LLM dependency behind one function, so the rest
of the system doesn't need to know which provider or SDK is in use.
"""

import os
import time
import logging

from app.core.config import settings
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

DEFAULT_MODEL = settings.llm_model  # Use model from .env

MAX_RETRIES = 3
INITIAL_BACKOFF_SECS = 1  # doubles each retry: 1s, 2s, 4s

_client = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        # Use the value from Settings (which reads .env)
        api_key = settings.llm_api_key
        if not api_key:
            raise RuntimeError("LLM_API_KEY not configured in .env or environment")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_answer(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to Gemini and return the generated text.

    Retries up to MAX_RETRIES times with exponential backoff on
    transient server errors (HTTP 500, 503).
    """

    client = _get_client()
    backoff = INITIAL_BACKOFF_SECS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        except genai_errors.ServerError as exc:
            if attempt == MAX_RETRIES:
                logger.error("Gemini API failed after %d attempts: %s", MAX_RETRIES, exc)
                raise
            logger.warning(
                "Gemini API returned server error (attempt %d/%d), "
                "retrying in %ds: %s",
                attempt, MAX_RETRIES, backoff, exc,
            )
            time.sleep(backoff)
            backoff *= 2