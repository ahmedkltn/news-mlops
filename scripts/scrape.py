"""
Step 1 — Scrape articles and save raw to DB (no ML, runs fast).

Usage:
    python -m scripts.scrape
    python -m scripts.scrape --pages 10
"""
import argparse
import logging
from etl.extract import run_extraction
from etl.load import save_raw_articles

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(max_pages: int = 5):
    logger.info(f"=== SCRAPE: fetching up to {max_pages} pages ===")
    articles = run_extraction(max_pages=max_pages)

    if not articles:
        logger.warning("No articles found.")
        return

    saved = save_raw_articles(articles)
    logger.info(f"=== SCRAPE done: {len(articles)} scraped, {saved} new in DB ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=5)
    args = parser.parse_args()
    main(max_pages=args.pages)
