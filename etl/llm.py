"""Provider-agnostic chat client for the GenAI features.

Any OpenAI-compatible provider works — swap by env vars only, no code change:

  Groq (default — free tier, highest RPD, no card):
    LLM_BASE_URL=https://api.groq.com/openai/v1
    LLM_MODEL=llama-3.3-70b-versatile
  Google Gemini (best French, long context; free tier):
    LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
    LLM_MODEL=gemini-2.5-flash
  OpenRouter (aggregator; free :free models, low RPD):
    LLM_BASE_URL=https://openrouter.ai/api/v1
    LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free

Set LLM_API_KEY to the chosen provider's key. Get one at:
  Groq https://console.groq.com/keys · Gemini https://aistudio.google.com/apikey
"""
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

_client_singleton = None


def _client():
    global _client_singleton
    if _client_singleton is None:
        from openai import OpenAI
        _client_singleton = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL),
            api_key=os.getenv("LLM_API_KEY"),
            default_headers={"X-Title": "Tunisia News Hub"},
        )
    return _client_singleton


def complete(user: str, system: str | None = None, max_tokens: int = 512) -> str:
    """One-shot chat completion. Returns the assistant text (stripped)."""
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    resp = _client().chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
