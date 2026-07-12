from pathlib import Path
from scrapers.rss import fetch_og_image

def test_extract_og_image():
    html = (Path(__file__).parent / "fixtures" / "article_with_og.html").read_text()
    assert fetch_og_image(html) == "https://x.tn/img.jpg"

def test_no_og_image_returns_none():
    assert fetch_og_image("<html><head></head><body>x</body></html>") is None
