import logging
from scrapers.base import Article

logger = logging.getLogger(__name__)

SENTIMENT_MAP = {
    "positive": "positive",
    "neutral":  "neutral",
    "negative": "negative",
}

# ── Lazy singletons ────────────────────────────────────────────────────────────
# Models are heavy (~500 MB each). We load them only when first needed so that:
#   • the API can start without loading ML deps
#   • individual scripts only pay the cost for the step they run

_embedding_model = None
_sentiment_pipeline = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model…")
        _embedding_model = SentenceTransformer("intfloat/multilingual-e5-small")
    return _embedding_model


def _get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        import torch
        from transformers import pipeline
        logger.info("Loading sentiment model…")
        _sentiment_pipeline = pipeline(
            "text-classification",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            device=0 if torch.cuda.is_available() else -1,
            truncation=True,
            max_length=512,
        )
    return _sentiment_pipeline


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    """Embed a SEARCH QUERY (e5 'query:' prefix)."""
    model = _get_embedding_model()
    emb = model.encode(f"query: {text}", normalize_embeddings=True)
    return emb.tolist()


def get_passage_embedding(text: str) -> list[float]:
    """Embed a DOCUMENT (e5 'passage:' prefix)."""
    model = _get_embedding_model()
    emb = model.encode(f"passage: {text}", normalize_embeddings=True)
    return emb.tolist()


def get_sentiment(text: str) -> str:
    try:
        result = _get_sentiment_pipeline()(text[:1000])
        label = result[0]["label"].lower()
        return SENTIMENT_MAP.get(label, "neutral")
    except Exception as e:
        logger.warning(f"Sentiment failed: {e}")
        return "neutral"


def get_sentiments(texts: list[str]) -> list[str]:
    if not texts:
        return []
    try:
        pipe = _get_sentiment_pipeline()
        results = pipe([t[:1000] for t in texts], batch_size=16)
        return [SENTIMENT_MAP.get(r["label"].lower(), "neutral") for r in results]
    except Exception as e:
        logger.warning(f"Batch sentiment failed: {e}")
        return ["neutral"] * len(texts)


def transform_articles(articles: list[Article]) -> list[dict]:
    model = _get_embedding_model()

    texts = [
        f"passage: {(a.title or '')} {(a.content or '')}".strip()
        for a in articles
    ]

    logger.info(f"Encoding {len(texts)} articles in batch…")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=True,
    )

    sentiments = get_sentiments(
        [f"{a.title or ''} {a.content or ''}" for a in articles]
    )

    transformed = []
    for i, article in enumerate(articles):
        text = texts[i].replace("passage: ", "", 1)
        if not text.strip():
            continue

        sentiment = sentiments[i]

        transformed.append({
            "url":        article.url,
            "source":     article.source,
            "title":      article.title,
            "content":    article.content,
            "language":   article.language,
            "published_at": article.published_at,
            "embedding":  embeddings[i].tolist(),
            "sentiment":  sentiment,
            "topic_id":   None,
            "topic_label": None,
        })

    logger.info(f"Transformed {len(transformed)} articles")
    return transformed