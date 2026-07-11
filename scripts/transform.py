"""
Step 2 — Generate embeddings + sentiment for articles that don't have them yet.
Loads ML models once, processes in batches.

Usage:
    python -m scripts.transform
    python -m scripts.transform --batch-size 32
"""
import argparse
import logging
from etl.load import fetch_untransformed_articles, update_article_ml_fields
from etl.transform import _get_embedding_model, get_sentiments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(batch_size: int = 16):
    articles = fetch_untransformed_articles()

    if not articles:
        logger.info("No articles need transforming — all up to date.")
        return

    logger.info(f"=== TRANSFORM: {len(articles)} articles to process ===")

    # Load embedding model once
    model = _get_embedding_model()

    texts = [
        f"passage: {(a['title'] or '')} {(a['content'] or '')}".strip()
        for a in articles
    ]

    logger.info("Encoding embeddings in batch…")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=True,
    )

    logger.info("Running sentiment analysis…")
    sentiments = get_sentiments(
        [f"{a['title'] or ''} {a['content'] or ''}" for a in articles]
    )

    # Per-row DB write is acceptable here — batching the writes is out of scope.
    for i, article in enumerate(articles):
        update_article_ml_fields(
            article_id=article["id"],
            embedding=embeddings[i].tolist(),
            sentiment=sentiments[i],
        )
        if (i + 1) % 10 == 0:
            logger.info(f"  {i + 1}/{len(articles)} done")

    logger.info(f"=== TRANSFORM done: {len(articles)} articles updated ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    main(batch_size=args.batch_size)
