"""LLM-based theme classification.

BERTopic clustering needs the (network-blocked) embedding model, so themes
come from the Groq LLM instead: each article is placed in one fixed category.
Stored in articles.topic_label (name) + topic_id (index) so the existing
/articles/topics + filter endpoints work unchanged.
"""
from etl.regions import normalize

THEMES = [
    "Politique", "Économie", "Sport", "Société", "International",
    "Culture", "Sécurité", "Santé", "Environnement", "Technologie",
]

_THEME_BY_NORM = {normalize(t): t for t in THEMES}


def theme_id(theme: str) -> int:
    return THEMES.index(theme) if theme in THEMES else len(THEMES) - 1


def _match(out: str) -> str | None:
    n = normalize(out)
    if n in _THEME_BY_NORM:
        return _THEME_BY_NORM[n]
    for norm, theme in _THEME_BY_NORM.items():
        if norm in n:
            return theme
    return None


def classify_theme(title: str, content: str = "") -> str:
    """Return one THEME for the article (defaults to 'Société')."""
    from etl.llm import complete, FAST_MODEL
    prompt = (
        "Classe cet article de presse tunisien dans UNE seule catégorie parmi : "
        f"{', '.join(THEMES)}.\nRéponds uniquement par le nom exact de la "
        f"catégorie, sans ponctuation.\n\nTitre : {title}\n{(content or '')[:400]}"
    )
    try:
        out = complete(user=prompt, max_tokens=8, model=FAST_MODEL)
    except Exception:
        return "Société"
    return _match(out) or "Société"
