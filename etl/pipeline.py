import logging
from etl.extract import run_extraction
from etl.transform import transform_articles
from etl.load import save_articles
from etl.metrics import record_pipeline_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBED_MODEL = "intfloat/multilingual-e5-small"

def run_pipeline(max_pages: int = 5) -> dict:
    logger.info("=== Pipeline started ===")

    # Extract
    logger.info("Step 1: Extraction")
    articles = run_extraction(max_pages=max_pages)
    if not articles:
        logger.warning("No articles extracted, stopping.")
        return {"extracted": 0, "transformed": 0, "loaded": 0}

    # Transform
    logger.info("Step 2: Transform")
    transformed = transform_articles(articles)

    # Load
    logger.info("Step 3: Load")
    saved = save_articles(transformed)

    # Metrics (never break the pipeline on a write failure)
    try:
        sentiment_pos = sum(1 for a in transformed if a.get("sentiment") == "positive")
        sentiment_neu = sum(1 for a in transformed if a.get("sentiment") == "neutral")
        sentiment_neg = sum(1 for a in transformed if a.get("sentiment") == "negative")
        record_pipeline_metrics({
            "source": "all",
            "articles_new": saved,
            "n_topics": None,
            "outlier_pct": None,
            "sentiment_pos": sentiment_pos,
            "sentiment_neu": sentiment_neu,
            "sentiment_neg": sentiment_neg,
            "embed_model": EMBED_MODEL,
        })
    except Exception as e:
        logger.warning(f"Failed to record pipeline metrics: {e}")

    result = {
        "extracted": len(articles),
        "transformed": len(transformed),
        "loaded": saved,
    }
    logger.info(f"=== Pipeline done: {result} ===")
    return result

if __name__ == "__main__":
    run_pipeline(max_pages=1)