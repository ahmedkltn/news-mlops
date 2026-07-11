from pathlib import Path
from scrapers.rss import parse_feed, _entry_to_article

FIXTURE = Path(__file__).parent / "fixtures" / "kapitalis_feed.xml"

def test_parse_feed_returns_articles():
    xml = FIXTURE.read_text(encoding="utf-8")
    articles = parse_feed(xml, source="kapitalis", language="fr")
    assert len(articles) > 0
    a = articles[0]
    assert a.title and a.content
    assert a.url.startswith("http")
    assert a.published_at is not None


def _entry(**over):
    e = {"title": "T", "link": "https://x.tn/a", "summary": "Corps de test",
         "tags": [{"term": "politique"}]}
    e.update(over)
    return e

def test_image_from_media_content():
    a = _entry_to_article(_entry(media_content=[{"url": "https://x.tn/img.jpg"}]),
                          source="s", language="fr")
    assert a is not None
    assert a.image_url == "https://x.tn/img.jpg"

def test_image_from_image_typed_link():
    a = _entry_to_article(_entry(links=[{"type": "image/jpeg", "href": "https://x.tn/p.jpg"}]),
                          source="s", language="fr")
    assert a.image_url == "https://x.tn/p.jpg"

def test_no_image_is_none():
    a = _entry_to_article(_entry(), source="s", language="fr")
    assert a.image_url is None
