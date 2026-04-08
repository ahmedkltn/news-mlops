from typing import Optional
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, Article

class KapitalisScraper(BaseScraper):
    def __init__(self, max_pages: int = 5):
        super().__init__(
            source="kapitalis",
            base_url="https://kapitalis.com/tunisie/category/a-la-une",
            language="fr",
            max_pages=max_pages,
        )

    def get_article_urls(self, page: int) -> list[str]:
        url = f"{self.base_url}/page/{page}/"
        soup = self.fetch(url)
        if not soup:
            return []

        anchors = soup.select("article.post div h2.entry-title a")
        return [a["href"] for a in anchors if a.get("href")]

    def parse_article(self, url: str) -> Optional[Article]:
        soup = self.fetch(url)
        if not soup:
            return None

        title = self._get_title(soup)
        content = self._get_content(soup)
        categories = self._get_categories(soup)
        published_at = self._get_published_at(soup)

        if not title or not content:
            return None

        return Article(
            url=url,
            source=self.source,
            title=title,
            content=content,
            language=self.language,
            categories=categories,
            published_at=published_at,
        )

    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        tag = soup.select_one("h1.cmsmasters_post_title")
        return tag.get_text(strip=True) if tag else None

    def _get_content(self, soup: BeautifulSoup) -> Optional[str]:
        tag = soup.select_one(
            "article div.cmsmasters_post_content.entry-content"
        )
        if not tag:
            return None
        # Text only — strip all tags
        return " ".join(tag.get_text(separator=" ", strip=True).split())

    def _get_categories(self, soup: BeautifulSoup) -> list[str]:
        tags = soup.select("article span.cmsmasters_post_category a")
        return [t.get_text(strip=True) for t in tags]

    def _get_published_at(self, soup: BeautifulSoup) -> Optional[str]:
        tag = soup.select_one("article abbr.published")
        return tag.get("title") or tag.get_text(strip=True) if tag else None