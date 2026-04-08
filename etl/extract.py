import logging
from scrapers.kapitalis import KapitalisScraper
from scrapers.base import Article

logger = logging.getLogger(__name__)

def run_extraction(max_pages: int = 5) -> list[Article]:
    scrapers = [
        KapitalisScraper(max_pages=max_pages),
    ]

    all_articles = []
    for scraper in scrapers:
        logger.info(f"Running scraper: {scraper.source}")
        articles = scraper.scrape()
        all_articles.extend(articles)
        logger.info(f"{scraper.source}: {len(articles)} articles")

    logger.info(f"Total articles extracted: {len(all_articles)}")
    return all_articles