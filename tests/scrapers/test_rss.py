from pathlib import Path
from scrapers.rss import parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "kapitalis_feed.xml"

def test_parse_feed_returns_articles():
    xml = FIXTURE.read_text(encoding="utf-8")
    articles = parse_feed(xml, source="kapitalis", language="fr")
    assert len(articles) > 0
    a = articles[0]
    assert a.title and a.content
    assert a.url.startswith("http")
    assert a.published_at is not None
