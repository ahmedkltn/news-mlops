import logging
import feedparser
from typing import Optional
from scrapers.base import BaseScraper, Article

logger = logging.getLogger(__name__)


def fetch_og_image(html: str) -> Optional[str]:
    from bs4 import BeautifulSoup
    tag = BeautifulSoup(html, "lxml").find("meta", property="og:image")
    return tag.get("content") if tag and tag.get("content") else None


def _entry_to_article(entry, source: str, language: str) -> Optional[Article]:
    title = entry.get("title")
    link = entry.get("link")
    # Some feeds (e.g. Mosaïque FM) put a short caption in <content> and the
    # real teaser in <summary>. Take whichever carries more text.
    from bs4 import BeautifulSoup
    content_raw = entry["content"][0].get("value", "") if entry.get("content") else ""
    summary_raw = entry.get("summary", "")
    content_txt = " ".join(BeautifulSoup(content_raw, "lxml").get_text(" ").split())
    summary_txt = " ".join(BeautifulSoup(summary_raw, "lxml").get_text(" ").split())
    content = content_txt if len(content_txt) >= len(summary_txt) else summary_txt

    categories = [t.get("term") for t in entry.get("tags", []) if t.get("term")]
    published_at = entry.get("published") or entry.get("updated")

    image_url = None
    if entry.get("media_content"):
        image_url = entry["media_content"][0].get("url")
    elif entry.get("links"):
        for l in entry["links"]:
            if (l.get("type") or "").startswith("image"):
                image_url = l.get("href"); break

    if not link or not title or not content:
        return None
    try:
        return Article(url=link, source=source, title=title, content=content,
                       language=language, categories=categories,
                       published_at=published_at, image_url=image_url)
    except Exception as e:
        logger.warning(f"[{source}] skip entry: {e}")
        return None


def parse_feed(xml: str, source: str, language: str) -> list[Article]:
    feed = feedparser.parse(xml)
    out = [_entry_to_article(e, source, language) for e in feed.entries]
    return [a for a in out if a]


class RSSScraper(BaseScraper):
    def __init__(self, source: str, feed_url: str, language: str):
        super().__init__(source=source, base_url=feed_url, language=language, max_pages=1)
        self.feed_url = feed_url

    def get_article_urls(self, page: int) -> list[str]:
        return []  # not used — RSS scrape is overridden below

    def parse_article(self, url: str):
        return None

    def _enrich_image(self, article: Article) -> None:
        """Best-effort og:image from the article page when the feed has none."""
        if article.image_url:
            return
        try:
            resp = self.session.get(article.url, timeout=8)
            if resp.ok:
                article.image_url = fetch_og_image(resp.text)
        except Exception as e:  # network/parse issues must not break the scrape
            logger.debug(f"[{self.source}] og:image fetch failed for {article.url}: {e}")

    def scrape(self) -> list[Article]:
        resp = self.session.get(self.feed_url, timeout=15)
        resp.raise_for_status()
        articles = parse_feed(resp.text, self.source, self.language)
        for article in articles:
            self._enrich_image(article)
        n_img = sum(1 for a in articles if a.image_url)
        logger.info(f"[{self.source}] RSS: {len(articles)} articles, {n_img} with image")
        return articles
