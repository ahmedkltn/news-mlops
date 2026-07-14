import logging
from etl.llm import complete, model_for, FAST_MODEL

logger = logging.getLogger(__name__)

# LLM answers that start like these are meta-chatter about the task,
# not a topic title (e.g. "Je vais essayer de donner un titre…").
_META_PREFIXES = (
    "je vais", "je vois", "je peux", "voici", "voilà", "bien sûr",
    "d'accord", "ok", "certainement", "en me basant", "based on",
)
_MAX_WORDS = 6
_MAX_CHARS = 48


def _keyword_fallback(keywords: list[str], tid: int) -> str:
    words = [k.strip().title() for k in keywords[:2] if k.strip()]
    return " / ".join(words) if words else f"Topic {tid}"


def clean_label(text: str | None, keywords: list[str], tid: int) -> str:
    """Sanitize an LLM-proposed topic title; fall back to keywords when unusable."""
    if not text:
        return _keyword_fallback(keywords, tid)
    label = text.strip().splitlines()[0].strip('"«»\'. \t').strip()
    if (
        not label
        or label.lower().startswith(_META_PREFIXES)
        or len(label.split()) > _MAX_WORDS
        or len(label) > _MAX_CHARS
    ):
        return _keyword_fallback(keywords, tid)
    return label


def label_topics(topic_keywords: dict[int, list[str]]) -> dict[int, str]:
    model = model_for("labels", FAST_MODEL)
    labels_out = {}
    for tid, keywords in topic_keywords.items():
        kw = ", ".join(keywords[:8])
        try:
            text = complete(
                user=(
                    f"Ces mots-clés décrivent un thème d'actualité tunisienne : {kw}. "
                    f"Donne un titre de thème court (2-4 mots), en français, sans ponctuation finale. "
                    f"Réponds uniquement par le titre, sans phrase d'introduction."
                ),
                max_tokens=24,
                model=model,
            )
        except Exception as e:
            logger.warning(f"Label failed for topic {tid}: {e}")
            text = None
        labels_out[tid] = clean_label(text, keywords, tid)
    return labels_out
