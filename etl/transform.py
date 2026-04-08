import logging
import torch
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from scrapers.base import Article

logger = logging.getLogger(__name__)

# Load models once at module level — avoid reloading on every call
EMBEDDING_MODEL = SentenceTransformer("intfloat/multilingual-e5-large")

SENTIMENT_PIPELINE = pipeline(
    "text-classification",
    model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
    device=0 if torch.cuda.is_available() else -1,
    truncation=True,
    max_length=512,
)

SENTIMENT_MAP = {
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}

def get_embedding(text: str) -> list[float]:
    prompt = f"passage: {text}"
    embedding = EMBEDDING_MODEL.encode(prompt, normalize_embeddings=True)
    return embedding.tolist()

def get_sentiment(text: str) -> str:
    try:
        # Truncate to avoid token limit issues
        result = SENTIMENT_PIPELINE(text[:1000])
        label = result[0]["label"].upper()
        return SENTIMENT_MAP.get(label, "neutral")
    except Exception as e:
        logger.warning(f"Sentiment failed: {e}")
        return "neutral"

def transform_articles(articles: list[Article]) -> list[dict]:
    transformed = []

    # Batch encode all texts at once — much faster than one by one
    texts = [
        f"passage: {(a.title or '')} {(a.content or '')}".strip()
        for a in articles
    ]

    logger.info(f"Encoding {len(texts)} articles in batch...")
    embeddings = EMBEDDING_MODEL.encode(
        texts,
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=True,
    )

    for i, article in enumerate(articles):
        text = texts[i].replace("passage: ", "", 1)
        if not text.strip():
            continue

        sentiment = get_sentiment(f"{article.title or ''} {article.content or ''}"[:1000])

        transformed.append({
            "url": article.url,
            "source": article.source,
            "title": article.title,
            "content": article.content,
            "language": article.language,
            "published_at": article.published_at,
            "embedding": embeddings[i].tolist(),
            "sentiment": sentiment,
            "topic_id": None,
            "topic_label": None,
        })

    logger.info(f"Transformed {len(transformed)} articles")
    return transformed