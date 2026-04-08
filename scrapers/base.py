import time
import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Article:
    url: str
    source: str
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    categories: list[str] = field(default_factory=list)
    published_at: Optional[str] = None

class BaseScraper(ABC):
    def __init__(self, source: str, base_url: str, language: str, max_pages: int = 5):
        self.source = source
        self.base_url = base_url
        self.language = language
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        })

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def polite_delay(self):
        time.sleep(random.uniform(1.5, 3.0))

    @abstractmethod
    def get_article_urls(self, page: int) -> list[str]:
        """Return list of article URLs from a listing page."""
        pass

    @abstractmethod
    def parse_article(self, url: str) -> Optional[Article]:
        """Parse a single article page and return an Article."""
        pass

    def scrape(self) -> list[Article]:
        articles = []
        seen_urls = set()

        for page in range(1, self.max_pages + 1):
            logger.info(f"[{self.source}] Scraping listing page {page}/{self.max_pages}")
            urls = self.get_article_urls(page)

            if not urls:
                logger.info(f"[{self.source}] No URLs found on page {page}, stopping.")
                break

            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                article = self.parse_article(url)
                if article:
                    articles.append(article)
                    logger.info(f"[{self.source}] Scraped: {article.title}")

                self.polite_delay()

            self.polite_delay()

        logger.info(f"[{self.source}] Done. {len(articles)} articles scraped.")
        return articles