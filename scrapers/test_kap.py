from scrapers.kapitalis import KapitalisScraper

scraper = KapitalisScraper(max_pages=1)
articles = scraper.scrape()

for a in articles[:3]:
    print(a.title)
    print(a.published_at)
    print(a.categories)
    print(a.content[:200])
    print("---")