"""Provider-agnostic chat client for the GenAI features.

Any OpenAI-compatible provider works — swap by env vars only, no code change:

  Groq (default — free tier, highest RPD, no card):
    LLM_BASE_URL=https://api.groq.com/openai/v1
  Google Gemini (best French, long context; free tier):
    LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
  OpenRouter (aggregator; free :free models, low RPD):
    LLM_BASE_URL=https://openrouter.ai/api/v1

Set LLM_API_KEY to the chosen provider's key. Get one at:
  Groq https://console.groq.com/keys · Gemini https://aistudio.google.com/apikey

Per-feature models keep the free-tier limits comfortable: summaries and topic
labels default to a fast/cheap model, chat to a higher-quality one. Override
any of them independently:
  LLM_MODEL_SUMMARY, LLM_MODEL_LABELS, LLM_MODEL_CHAT  — per feature
  LLM_MODEL                                            — force one model for all
Precedence: LLM_MODEL_<FEATURE>  >  LLM_MODEL  >  the per-feature code default.
"""
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
# Higher-quality default (chat); FAST is the cheap/high-throughput default
# for bulk work (summaries, labels). Both are Groq free-tier models.
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FAST_MODEL = "llama-3.1-8b-instant"

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


def model_for(feature: str, default: str) -> str:
    """Resolve the model for a feature.

    LLM_MODEL_<FEATURE>  >  LLM_MODEL  >  `default`.
    """
    return (
        os.getenv(f"LLM_MODEL_{feature.upper()}")
        or os.getenv("LLM_MODEL")
        or default
    )


def complete(user: str, system: str | None = None, max_tokens: int = 512,
             model: str | None = None) -> str:
    """One-shot chat completion. Returns the assistant text (stripped)."""
    model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
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
