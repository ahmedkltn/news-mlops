import logging
from scrapers.kapitalis import KapitalisScraper
from scrapers.rss import RSSScraper
from scrapers.base import Article

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("lapresse",     "https://lapresse.tn/feed/",                 "fr"),
    ("businessnews", "https://www.businessnews.com.tn/rss.xml",   "fr"),
    ("kapitalis",    "https://kapitalis.com/tunisie/feed/",       "fr"),
    ("mosaique",     "https://www.mosaiquefm.net/fr/rss",         "fr"),
]

def build_scrapers(max_pages: int = 5):
    scrapers = [RSSScraper(s, url, lang) for (s, url, lang) in RSS_FEEDS]
    # Keep the HTML scraper for deeper Kapitalis pagination if desired:
    # scrapers.append(KapitalisScraper(max_pages=max_pages))
    return scrapers

def run_extraction(max_pages: int = 5) -> list[Article]:
    all_articles = []
    for scraper in build_scrapers(max_pages):
        logger.info(f"Running scraper: {scraper.source}")
        try:
            articles = scraper.scrape()
        except Exception as e:
            logger.error(f"{scraper.source} failed: {e}")
            continue
        all_articles.extend(articles)
        logger.info(f"{scraper.source}: {len(articles)} articles")
    logger.info(f"Total articles extracted: {len(all_articles)}")
    return all_articles