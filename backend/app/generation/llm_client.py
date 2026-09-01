"""
Phase 5, Step 2: LLM client for answer generation (Gemini API).

Isolates the external LLM dependency behind one function, so the rest
of the system doesn't need to know which provider or SDK is in use.
"""

import os
from app.core.config import settings
from google import genai

DEFAULT_MODEL = settings.llm_model  # Use model from .env

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

    If the LLM API key is not set, return a placeholder response.
    """

    client = _get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text