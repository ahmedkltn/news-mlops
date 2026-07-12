from etl import extract

def test_scrapers_include_rss_feeds():
    scrapers = extract.build_scrapers(max_pages=1)
    sources = {s.source for s in scrapers}
    assert {"kapitalis", "lapresse", "businessnews"}.issubset(sources)
