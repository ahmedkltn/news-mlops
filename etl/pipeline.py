import logging
from etl.extract import run_extraction
from etl.transform import transform_articles
from etl.load import save_articles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    result = {
        "extracted": len(articles),
        "transformed": len(transformed),
        "loaded": saved,
    }
    logger.info(f"=== Pipeline done: {result} ===")
    return result

if __name__ == "__main__":
    run_pipeline(max_pages=1)