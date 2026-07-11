# Tunisia News Hub — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current single-source news-mlops app into a multi-source Tunisia news hub with better retrieval, MLflow tracking, GenAI features, and a friendly news-reader UI — scoped to a 2-day, 3-person build.

**Architecture:** Keep the existing FastAPI + Postgres/pgvector + Prefect + React stack. Add a generic RSS ingestion layer beside the current HTML scraper, fix the embedding model, wire MLflow, add Claude-powered summaries/chat/topic-labels, and add a magazine-style reader on top of the existing analytics dashboard. Work splits into a shared **Phase 0 foundation** (blocking) then three parallel tracks — **A: data/sources**, **B: ML/MLOps**, **C: app/GenAI/UI**.

**Tech Stack:** Python 3.11+, FastAPI, psycopg2, pgvector, sentence-transformers, BERTopic, Prefect 3, MLflow, `anthropic` SDK, feedparser, Pydantic v2, React + Vite, Recharts, Docker Compose, pytest, GitHub Actions.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-11-tunisia-news-hub-design.md`.
- Embedding model is `intfloat/multilingual-e5-small` — **384 dimensions**, so the `articles.embedding vector(384)` column is unchanged. Query text is prefixed `"query: "`; document text is prefixed `"passage: "`.
- Claude model for all GenAI is `claude-haiku-4-5` (high-volume, cost-sensitive student project). SDK: `anthropic`, client `anthropic.Anthropic()`, credentials from `ANTHROPIC_API_KEY`. Non-streaming calls use `max_tokens` ≤ 1024.
- DB access follows the existing pattern: `from etl.load import get_connection`, one connection per call, `cur.close()` + `conn.close()` in a `finally`.
- New Python deps go in `requirements.txt`. New env vars go in `.env` and are documented in `README.md`.
- Tests use `pytest`; put them under `tests/` mirroring the module path. Network/LLM calls in tests are mocked — never hit the live web or the Anthropic API in a test.
- Follow existing code style: module-level `logger = logging.getLogger(__name__)`, lazy model loading, type hints on public functions.

## Shared Interfaces (all tracks depend on these)

New/changed `articles` columns: `published_at TIMESTAMP`, `image_url TEXT`, `categories TEXT[]`, `summary TEXT`, `story_id INTEGER`. New tables: `entities`, `pipeline_metrics` (see Task F1).

Key function signatures other tasks rely on:

```python
# etl/transform.py
def get_embedding(text: str) -> list[float]         # prefixes "query: ", used for SEARCH queries
def get_passage_embedding(text: str) -> list[float] # prefixes "passage: ", used for documents
def get_sentiments(texts: list[str]) -> list[str]   # BATCHED sentiment, returns one label per input

# scrapers/rss.py
class RSSScraper(BaseScraper):
    def __init__(self, source: str, feed_url: str, language: str): ...
    # inherited .scrape() returns list[Article] with published_at, categories, image_url set

# etl/labels.py
def label_topics(topic_keywords: dict[int, list[str]]) -> dict[int, str]  # LLM topic labels

# etl/metrics.py
def record_pipeline_metrics(m: dict) -> None   # insert one row into pipeline_metrics

# api/routes/genai.py
GET  /genai/summary/{article_id} -> {"summary": str}
POST /genai/chat  body {"q": str}  -> {"answer": str, "sources": [{"id","title","url"}]}
# api/routes/articles.py
GET  /articles/timeline?days=30 -> [{"date","positive","neutral","negative"}]
```

`Article` (scrapers/base.py) gains `image_url: Optional[str] = None` and keeps `categories: list[str]` and `published_at: Optional[str]`.

---

# Phase 0 — Foundation (BLOCKING, do first)

These unblock all three tracks. One person can land them in the first ~3 hours while others read the plan. Each track branches off after F1–F4 are merged.

### Task F1: Database migration for new columns and tables

**Files:**
- Create: `db/migrations/001_news_hub.sql`
- Modify: `db/schema.sql` (append the same columns/tables so fresh DBs match)
- Test: `tests/db/test_migration.py`

**Interfaces:**
- Produces: the columns and tables listed in Shared Interfaces.

- [ ] **Step 1: Write the migration SQL**

Create `db/migrations/001_news_hub.sql`:

```sql
-- 001_news_hub.sql — additive migration, safe to run on an existing DB
ALTER TABLE articles ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS image_url    TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS categories   TEXT[];
ALTER TABLE articles ADD COLUMN IF NOT EXISTS summary      TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS story_id     INTEGER;

CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_story ON articles(story_id);

CREATE TABLE IF NOT EXISTS entities (
    id          SERIAL PRIMARY KEY,
    article_id  INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    label       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id            SERIAL PRIMARY KEY,
    run_at        TIMESTAMP DEFAULT NOW(),
    source        TEXT,
    articles_new  INTEGER,
    n_topics      INTEGER,
    outlier_pct   REAL,
    sentiment_pos INTEGER,
    sentiment_neu INTEGER,
    sentiment_neg INTEGER,
    embed_model   TEXT
);
```

- [ ] **Step 2: Mirror the columns into `db/schema.sql`**

Add the five `published_at`/`image_url`/`categories`/`summary`/`story_id` columns to the `CREATE TABLE articles` block in `db/schema.sql`, and append the two new `CREATE TABLE` statements + indexes, so a container built from scratch has the same schema. (The `docker-entrypoint-initdb.d/schema.sql` mount only runs on an empty volume.)

- [ ] **Step 3: Apply the migration to the running DB**

Run: `make db` (if not already up), then
`docker exec -i news_postgres psql -U news_user -d news_db < db/migrations/001_news_hub.sql`
Expected: `ALTER TABLE` / `CREATE TABLE` / `CREATE INDEX` lines, no errors.

- [ ] **Step 4: Write a test that asserts the columns exist**

Create `tests/db/test_migration.py`:

```python
import os, pytest, psycopg2
from etl.load import get_connection

REQUIRED = {"published_at", "image_url", "categories", "summary", "story_id"}

@pytest.mark.integration
def test_articles_has_new_columns():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'articles'
    """)
    cols = {r[0] for r in cur.fetchall()}
    cur.close(); conn.close()
    assert REQUIRED.issubset(cols), f"missing: {REQUIRED - cols}"
```

- [ ] **Step 5: Run the test**

Run: `pytest tests/db/test_migration.py -v`
Expected: PASS (requires the DB up; mark `-m integration` so CI can skip it).

- [ ] **Step 6: Commit**

```bash
git add db/migrations/001_news_hub.sql db/schema.sql tests/db/test_migration.py
git commit -m "feat(db): add news-hub columns, entities + pipeline_metrics tables"
```

### Task F2: Pydantic Article model with validation

**Files:**
- Modify: `scrapers/base.py:13-21` (the `Article` dataclass)
- Test: `tests/scrapers/test_article_model.py`

**Interfaces:**
- Produces: `Article` as a Pydantic v2 model with `image_url`, validation that title+content are non-empty, and `.model_dump()` available. Consumed by every scraper and by `etl/transform.py`.

- [ ] **Step 1: Write the failing test**

Create `tests/scrapers/test_article_model.py`:

```python
import pytest
from pydantic import ValidationError
from scrapers.base import Article

def test_valid_article():
    a = Article(url="https://x.tn/1", source="kapitalis",
                title="Titre", content="Corps de l'article", language="fr")
    assert a.image_url is None
    assert a.categories == []

def test_empty_title_rejected():
    with pytest.raises(ValidationError):
        Article(url="https://x.tn/1", source="s", title="  ", content="body", language="fr")

def test_empty_content_rejected():
    with pytest.raises(ValidationError):
        Article(url="https://x.tn/1", source="s", title="t", content="", language="fr")
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pytest tests/scrapers/test_article_model.py -v`
Expected: FAIL (current `Article` is a dataclass that does not validate).

- [ ] **Step 3: Convert `Article` to Pydantic**

Replace the dataclass in `scrapers/base.py` (keep the imports `from typing import Optional`; add `from pydantic import BaseModel, field_validator`):

```python
class Article(BaseModel):
    url: str
    source: str
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    categories: list[str] = []
    published_at: Optional[str] = None
    image_url: Optional[str] = None

    @field_validator("title", "content")
    @classmethod
    def _non_empty(cls, v):
        if v is None or not v.strip():
            raise ValueError("must be non-empty")
        return v.strip()
```

Remove the now-unused `from dataclasses import dataclass, field` import. Add `pydantic` to `requirements.txt`.

- [ ] **Step 4: Verify existing attribute access still works**

`etl/transform.py` and `etl/load.py` read `a.url`, `a.title`, etc. — Pydantic models expose the same attribute access, so no change is needed there. `save_raw_articles` uses `hasattr(a, "url")` which stays true.

- [ ] **Step 5: Run the test**

Run: `pytest tests/scrapers/test_article_model.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scrapers/base.py requirements.txt tests/scrapers/test_article_model.py
git commit -m "feat(scrapers): make Article a validated Pydantic model with image_url"
```

### Task F3: Fix embeddings — switch to e5-small with correct prefixes

**Files:**
- Modify: `etl/transform.py:17-51` and `:64-78`
- Modify: `api/routes/search.py` (uses `get_embedding` — now correct for queries)
- Test: `tests/etl/test_embeddings.py`

**Interfaces:**
- Produces: `get_embedding(text)` (query prefix), `get_passage_embedding(text)` (passage prefix), both returning 384-length lists. `transform_articles` uses the passage prefix.

- [ ] **Step 1: Write the failing test**

Create `tests/etl/test_embeddings.py`:

```python
from etl import transform

def test_query_and_passage_dims():
    q = transform.get_embedding("politique en Tunisie")
    p = transform.get_passage_embedding("La politique en Tunisie évolue.")
    assert len(q) == 384
    assert len(p) == 384

def test_prefixes_differ(monkeypatch):
    seen = {}
    class FakeModel:
        def encode(self, text, **kw):
            seen["text"] = text
            import numpy as np
            return np.zeros(384)
    monkeypatch.setattr(transform, "_get_embedding_model", lambda: FakeModel())
    transform.get_embedding("x")
    assert seen["text"].startswith("query: ")
    transform.get_passage_embedding("y")
    assert seen["text"].startswith("passage: ")
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pytest tests/etl/test_embeddings.py -v`
Expected: FAIL (`get_passage_embedding` does not exist; current `get_embedding` uses `passage:`).

- [ ] **Step 3: Update the model and prefixes**

In `etl/transform.py`, change the model name and split the two prefixes:

```python
def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model…")
        _embedding_model = SentenceTransformer("intfloat/multilingual-e5-small")
    return _embedding_model


def get_embedding(text: str) -> list[float]:
    """Embed a SEARCH QUERY (e5 'query:' prefix)."""
    model = _get_embedding_model()
    emb = model.encode(f"query: {text}", normalize_embeddings=True)
    return emb.tolist()


def get_passage_embedding(text: str) -> list[float]:
    """Embed a DOCUMENT (e5 'passage:' prefix)."""
    model = _get_embedding_model()
    emb = model.encode(f"passage: {text}", normalize_embeddings=True)
    return emb.tolist()
```

In `transform_articles`, build `texts` with the `passage: ` prefix (it already does) and keep the batched `model.encode(texts, ...)` call — that path is correct once the model is e5.

- [ ] **Step 4: Run the test**

Run: `pytest tests/etl/test_embeddings.py -v`
Expected: PASS. (First run downloads the model — a few minutes once.)

- [ ] **Step 5: Re-embed existing rows**

Existing embeddings were made with the old model. Clear and recompute:
`docker exec -i news_postgres psql -U news_user -d news_db -c "UPDATE articles SET embedding = NULL;"`
then `make transform`. Expected: log line "Transformed N articles".

- [ ] **Step 6: Commit**

```bash
git add etl/transform.py tests/etl/test_embeddings.py
git commit -m "fix(etl): use multilingual-e5-small with correct query/passage prefixes"
```

### Task F4: Batch the sentiment pass

**Files:**
- Modify: `etl/transform.py:54-61` and `:80-101`
- Test: `tests/etl/test_sentiment.py`

**Interfaces:**
- Produces: `get_sentiments(texts: list[str]) -> list[str]` returning one label per input, in order. `transform_articles` calls it once for the whole batch.

- [ ] **Step 1: Write the failing test**

Create `tests/etl/test_sentiment.py`:

```python
from etl import transform

def test_get_sentiments_batched(monkeypatch):
    def fake_pipeline():
        def run(texts, **kw):
            return [{"label": "Positive"} for _ in texts]
        return run
    monkeypatch.setattr(transform, "_get_sentiment_pipeline", fake_pipeline)
    out = transform.get_sentiments(["a", "b", "c"])
    assert out == ["positive", "positive", "positive"]
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pytest tests/etl/test_sentiment.py -v`
Expected: FAIL (`get_sentiments` does not exist).

- [ ] **Step 3: Add the batched function**

In `etl/transform.py` add:

```python
def get_sentiments(texts: list[str]) -> list[str]:
    if not texts:
        return []
    try:
        pipe = _get_sentiment_pipeline()
        results = pipe([t[:1000] for t in texts], batch_size=16)
        return [SENTIMENT_MAP.get(r["label"].lower(), "neutral") for r in results]
    except Exception as e:
        logger.warning(f"Batch sentiment failed: {e}")
        return ["neutral"] * len(texts)
```

In `transform_articles`, replace the per-article `get_sentiment(...)` loop: compute
`sentiments = get_sentiments([f"{a.title or ''} {a.content or ''}" for a in articles])`
once before the loop, then use `sentiments[i]` per article. Keep the single-item `get_sentiment` for any callers, or delete it if unused (grep first).

- [ ] **Step 4: Run the test**

Run: `pytest tests/etl/test_sentiment.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/transform.py tests/etl/test_sentiment.py
git commit -m "perf(etl): batch sentiment inference instead of per-article loop"
```

### Task F5: Remove dead stub, wire MLflow into compose, add env docs

**Files:**
- Delete: `scrapers/tap.py` (empty stub) — or leave a `# TODO` note if a real TAP scraper is planned in backlog
- Modify: `docker-compose.yml:37-50` (uncomment the mlflow service) and add a `mlflow_data` volume
- Modify: `.env` and `README.md` (document `ANTHROPIC_API_KEY`, `MLFLOW_TRACKING_URI`)

**Interfaces:**
- Produces: a reachable MLflow at `http://localhost:5000` (and `http://mlflow:5000` inside compose), consumed by Track B.

- [ ] **Step 1: Delete the empty stub**

Run: `git rm scrapers/tap.py` (it is 0 lines; `etl/extract.py` does not import it).

- [ ] **Step 2: Uncomment the MLflow service**

In `docker-compose.yml`, uncomment the `mlflow:` block (lines 37–50) and add `mlflow_data:` under `volumes:`. Confirm the `api` service already sets `MLFLOW_TRACKING_URI: http://mlflow:5000` (it does).

- [ ] **Step 3: Document env vars**

Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
MLFLOW_TRACKING_URI=http://localhost:5000
```
Add a short "GenAI + tracking" note to `README.md` listing both, and add MLflow to the URL table (`http://localhost:5000`).

- [ ] **Step 4: Verify MLflow starts**

Run: `docker-compose up -d mlflow` then open `http://localhost:5000`.
Expected: the MLflow UI loads.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: drop empty tap stub, enable mlflow service, document env vars"
```

---

# Track A — Data pipeline & sources (Person A)

Branch off after Phase 0. Delivers 4+ sources with real dates, thumbnails, and validation.

### Task A1: Generic RSS scraper

**Files:**
- Create: `scrapers/rss.py`
- Create: `tests/scrapers/fixtures/kapitalis_feed.xml` (a saved real feed — download once with `curl -A "Mozilla/5.0" https://kapitalis.com/tunisie/feed/ -o tests/scrapers/fixtures/kapitalis_feed.xml`)
- Test: `tests/scrapers/test_rss.py`
- Modify: `requirements.txt` (add `feedparser`)

**Interfaces:**
- Consumes: `Article` (F2), `BaseScraper` (`scrapers/base.py`).
- Produces: `RSSScraper(source, feed_url, language)` whose `.scrape()` returns `list[Article]` with `title`, `content`, `published_at`, `categories`, and (when present) `image_url` populated.

- [ ] **Step 1: Write the failing test against a saved fixture**

Create `tests/scrapers/test_rss.py`:

```python
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
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pytest tests/scrapers/test_rss.py -v`
Expected: FAIL (`scrapers.rss` does not exist).

- [ ] **Step 3: Implement the RSS scraper**

Create `scrapers/rss.py`:

```python
import logging
import feedparser
from typing import Optional
from scrapers.base import BaseScraper, Article

logger = logging.getLogger(__name__)


def _entry_to_article(entry, source: str, language: str) -> Optional[Article]:
    title = entry.get("title")
    link = entry.get("link")
    # Prefer full content, fall back to summary
    content = ""
    if entry.get("content"):
        content = entry["content"][0].get("value", "")
    content = content or entry.get("summary", "")
    # Strip HTML tags
    from bs4 import BeautifulSoup
    content = " ".join(BeautifulSoup(content, "lxml").get_text(" ").split())

    categories = [t.get("term") for t in entry.get("tags", []) if t.get("term")]
    published_at = entry.get("published") or entry.get("updated")

    image_url = None
    if entry.get("media_content"):
        image_url = entry["media_content"][0].get("url")
    elif entry.get("links"):
        for l in entry["links"]:
            if l.get("type", "").startswith("image"):
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

    def scrape(self) -> list[Article]:
        resp = self.session.get(self.feed_url, timeout=15)
        resp.raise_for_status()
        articles = parse_feed(resp.text, self.source, self.language)
        logger.info(f"[{self.source}] RSS: {len(articles)} articles")
        return articles
```

- [ ] **Step 4: Run the test**

Run: `pytest tests/scrapers/test_rss.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/rss.py tests/scrapers/test_rss.py requirements.txt
git commit -m "feat(scrapers): generic RSS scraper with dates, categories, images"
```

### Task A2: og:image fallback for feeds without media tags

**Files:**
- Modify: `scrapers/rss.py` (add `fetch_og_image`)
- Test: `tests/scrapers/test_og_image.py` + `tests/scrapers/fixtures/article_with_og.html`

**Interfaces:**
- Produces: `fetch_og_image(html: str) -> Optional[str]`, used to backfill `image_url` when the feed has none.

- [ ] **Step 1: Write the failing test**

Create `tests/scrapers/fixtures/article_with_og.html` containing
`<html><head><meta property="og:image" content="https://x.tn/img.jpg"></head><body>hi</body></html>`
and `tests/scrapers/test_og_image.py`:

```python
from pathlib import Path
from scrapers.rss import fetch_og_image

def test_extract_og_image():
    html = (Path(__file__).parent / "fixtures" / "article_with_og.html").read_text()
    assert fetch_og_image(html) == "https://x.tn/img.jpg"

def test_no_og_image_returns_none():
    assert fetch_og_image("<html><head></head><body>x</body></html>") is None
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pytest tests/scrapers/test_og_image.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement**

Add to `scrapers/rss.py`:

```python
def fetch_og_image(html: str) -> Optional[str]:
    from bs4 import BeautifulSoup
    tag = BeautifulSoup(html, "lxml").find("meta", property="og:image")
    return tag.get("content") if tag and tag.get("content") else None
```

(Wiring it into a live backfill is optional for P0 — the function + test is the deliverable; call it from the scraper only if a target feed lacks images.)

- [ ] **Step 4: Run the test** — Run: `pytest tests/scrapers/test_og_image.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/rss.py tests/scrapers/test_og_image.py tests/scrapers/fixtures/article_with_og.html
git commit -m "feat(scrapers): og:image extraction helper"
```

### Task A3: Register RSS feeds in extraction

**Files:**
- Modify: `etl/extract.py`
- Test: `tests/etl/test_extract_sources.py`

**Interfaces:**
- Consumes: `RSSScraper` (A1), existing `KapitalisScraper`.
- Produces: `run_extraction` now aggregates several sources.

- [ ] **Step 1: Write the failing test**

Create `tests/etl/test_extract_sources.py`:

```python
from etl import extract

def test_scrapers_include_rss_feeds():
    scrapers = extract.build_scrapers(max_pages=1)
    sources = {s.source for s in scrapers}
    assert {"kapitalis", "lapresse", "businessnews"}.issubset(sources)
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/etl/test_extract_sources.py -v` — Expected: FAIL (`build_scrapers` does not exist).

- [ ] **Step 3: Add a `build_scrapers` factory and use it**

Rewrite `etl/extract.py`:

```python
import logging
from scrapers.kapitalis import KapitalisScraper
from scrapers.rss import RSSScraper
from scrapers.base import Article

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("lapresse",     "https://lapresse.tn/feed/",                 "fr"),
    ("businessnews", "https://www.businessnews.com.tn/rss.xml",   "fr"),
    ("kapitalis",    "https://kapitalis.com/tunisie/feed/",       "fr"),
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
```

- [ ] **Step 4: Run the test** — Run: `pytest tests/etl/test_extract_sources.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/extract.py tests/etl/test_extract_sources.py
git commit -m "feat(etl): aggregate multiple RSS sources in extraction"
```

### Task A4: Persist published_at, image_url, categories

**Files:**
- Modify: `etl/load.py:98-144` (`save_articles`) and `etl/transform.py:90-101` (the dict it builds)
- Test: `tests/etl/test_load_fields.py`

**Interfaces:**
- Consumes: F1 columns.
- Produces: `save_articles` writes the new fields; `transform_articles` passes them through.

- [ ] **Step 1: Write the failing test**

Create `tests/etl/test_load_fields.py`:

```python
from etl import load

def test_save_articles_sql_includes_new_columns(monkeypatch):
    captured = {}
    class FakeCur:
        rowcount = 1
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def commit(self): ...
        def rollback(self): ...
        def close(self): ...
    def fake_execute_values(cur, query, rows):
        captured["query"] = query; captured["rows"] = rows
    monkeypatch.setattr(load, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(load, "execute_values", fake_execute_values)
    load.save_articles([{
        "url": "u", "source": "s", "title": "t", "content": "c", "language": "fr",
        "topic_id": None, "topic_label": None, "sentiment": "neutral",
        "embedding": [0.0], "published_at": "2026-07-11", "image_url": "i",
        "categories": ["a"],
    }])
    assert "published_at" in captured["query"]
    assert "image_url" in captured["query"]
    assert "categories" in captured["query"]
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/etl/test_load_fields.py -v` — Expected: FAIL.

- [ ] **Step 3: Extend the INSERT**

In `etl/load.py` `save_articles`, add `published_at`, `image_url`, `categories` to the row tuple and the column list, and to the `ON CONFLICT ... DO UPDATE SET` clause. Example row + query fragment:

```python
rows = [(
    a["url"], a["source"], a["title"], a["content"], a["language"],
    a.get("topic_id"), a.get("topic_label"), a.get("sentiment"), a.get("embedding"),
    a.get("published_at"), a.get("image_url"), a.get("categories"),
) for a in articles]

query = """
    INSERT INTO articles (
        url, source, title, content, language,
        topic_id, topic_label, sentiment, embedding,
        published_at, image_url, categories
    ) VALUES %s
    ON CONFLICT (url) DO UPDATE SET
        topic_id=EXCLUDED.topic_id, topic_label=EXCLUDED.topic_label,
        sentiment=EXCLUDED.sentiment, embedding=EXCLUDED.embedding,
        published_at=EXCLUDED.published_at, image_url=EXCLUDED.image_url,
        categories=EXCLUDED.categories
"""
```

In `etl/transform.py`, add `"published_at": article.published_at, "image_url": article.image_url, "categories": article.categories` to the dict appended in `transform_articles`.

- [ ] **Step 4: Run the test** — Run: `pytest tests/etl/test_load_fields.py -v` — Expected: PASS.

- [ ] **Step 5: End-to-end check**

Run `make scrape && make transform`, then
`docker exec -i news_postgres psql -U news_user -d news_db -c "SELECT source, published_at, image_url IS NOT NULL AS has_img FROM articles LIMIT 5;"`
Expected: rows from multiple sources with non-null `published_at`.

- [ ] **Step 6: Commit**

```bash
git add etl/load.py etl/transform.py tests/etl/test_load_fields.py
git commit -m "feat(etl): persist published_at, image_url, categories"
```

---

# Track B — ML & MLOps (Person B)

Branch off after Phase 0. Delivers MLflow tracking, monitoring metrics, and LLM topic labels.

### Task B1: Log clustering run to MLflow

**Files:**
- Modify: `etl/cluster.py:104-111` (after `update_topics`)
- Test: `tests/etl/test_cluster_mlflow.py`

**Interfaces:**
- Produces: an MLflow run per clustering, logging `n_topics`, `outlier_pct`, `min_cluster_size`, `embed_model`, and registering the saved BERTopic model dir as an artifact.

- [ ] **Step 1: Write the failing test**

Create `tests/etl/test_cluster_mlflow.py`:

```python
from etl import cluster

def test_log_clustering_metrics_called(monkeypatch):
    calls = {}
    class FakeMlflow:
        def set_tracking_uri(self, u): ...
        def set_experiment(self, n): ...
        def start_run(self):
            class Ctx:
                def __enter__(s): return s
                def __exit__(s, *a): return False
            return Ctx()
        def log_params(self, p): calls["params"] = p
        def log_metrics(self, m): calls["metrics"] = m
        def log_artifacts(self, path): calls["artifacts"] = path
    monkeypatch.setattr(cluster, "mlflow", FakeMlflow(), raising=False)
    cluster.log_clustering_run(n_topics=5, outlier_pct=0.2, min_cluster_size=3)
    assert calls["metrics"]["n_topics"] == 5
    assert calls["params"]["embed_model"] == "intfloat/multilingual-e5-small"
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/etl/test_cluster_mlflow.py -v` — Expected: FAIL.

- [ ] **Step 3: Add the logging helper and call it**

At the top of `etl/cluster.py` add `import os` (present) and a module-level `mlflow = None` placeholder, then:

```python
def log_clustering_run(n_topics: int, outlier_pct: float, min_cluster_size: int):
    global mlflow
    if mlflow is None:
        import mlflow as _mlflow
        mlflow = _mlflow
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("news-clustering")
    with mlflow.start_run():
        mlflow.log_params({"embed_model": "intfloat/multilingual-e5-small",
                           "min_cluster_size": min_cluster_size})
        mlflow.log_metrics({"n_topics": n_topics, "outlier_pct": outlier_pct})
        mlflow.log_artifacts("models/bertopic_model")
```

In `run_clustering`, after `update_topics(...)`, compute `outlier_pct = topics.count(-1) / max(len(topics), 1)` and call
`log_clustering_run(len(topic_labels), outlier_pct, min_cluster_size)` inside a `try/except` (never fail the pipeline if MLflow is down — log a warning).

- [ ] **Step 4: Run the test** — Run: `pytest tests/etl/test_cluster_mlflow.py -v` — Expected: PASS.

- [ ] **Step 5: Live check**

`make cluster` (needs ≥10 embedded articles + MLflow up), then open `http://localhost:5000` → experiment `news-clustering` shows a run with `n_topics`.

- [ ] **Step 6: Commit**

```bash
git add etl/cluster.py tests/etl/test_cluster_mlflow.py
git commit -m "feat(mlops): log clustering runs + register model to MLflow"
```

### Task B2: Write pipeline_metrics rows for monitoring

**Files:**
- Create: `etl/metrics.py`
- Modify: `etl/pipeline.py` (record after load)
- Test: `tests/etl/test_metrics.py`

**Interfaces:**
- Produces: `record_pipeline_metrics(m: dict) -> None` inserting into `pipeline_metrics`. `m` keys: `source, articles_new, n_topics, outlier_pct, sentiment_pos, sentiment_neu, sentiment_neg, embed_model`.

- [ ] **Step 1: Write the failing test**

Create `tests/etl/test_metrics.py`:

```python
from etl import metrics

def test_record_pipeline_metrics_inserts(monkeypatch):
    captured = {}
    class FakeCur:
        def execute(self, q, params): captured["q"] = q; captured["params"] = params
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def commit(self): ...
        def close(self): ...
    monkeypatch.setattr(metrics, "get_connection", lambda: FakeConn())
    metrics.record_pipeline_metrics({"source": "all", "articles_new": 3})
    assert "INSERT INTO pipeline_metrics" in captured["q"]
    assert captured["params"][0] == "all"
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/etl/test_metrics.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement**

Create `etl/metrics.py`:

```python
import logging
from etl.load import get_connection

logger = logging.getLogger(__name__)

def record_pipeline_metrics(m: dict) -> None:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO pipeline_metrics
            (source, articles_new, n_topics, outlier_pct,
             sentiment_pos, sentiment_neu, sentiment_neg, embed_model)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (m.get("source"), m.get("articles_new"), m.get("n_topics"),
          m.get("outlier_pct"), m.get("sentiment_pos"), m.get("sentiment_neu"),
          m.get("sentiment_neg"), m.get("embed_model")))
    conn.commit(); cur.close(); conn.close()
    logger.info(f"Recorded pipeline metrics: {m}")
```

In `etl/pipeline.py`, after `save_articles`, count sentiments from `transformed` and call `record_pipeline_metrics({...})` inside a `try/except`.

- [ ] **Step 4: Run the test** — Run: `pytest tests/etl/test_metrics.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/metrics.py etl/pipeline.py tests/etl/test_metrics.py
git commit -m "feat(mlops): record per-run pipeline metrics for monitoring"
```

### Task B3: LLM topic labels via Claude Haiku

**Files:**
- Create: `etl/labels.py`
- Modify: `etl/cluster.py` (use labels for `topic_label`)
- Test: `tests/etl/test_labels.py`
- Modify: `requirements.txt` (add `anthropic`)

**Interfaces:**
- Produces: `label_topics(topic_keywords: dict[int, list[str]]) -> dict[int, str]` mapping topic_id → a short human label.

- [ ] **Step 1: Write the failing test (mock Anthropic)**

Create `tests/etl/test_labels.py`:

```python
from etl import labels

def test_label_topics_maps_ids(monkeypatch):
    class FakeText:
        type = "text"; text = "Politique nationale"
    class FakeMsg:
        content = [FakeText()]
    class FakeMessages:
        def create(self, **kw): return FakeMsg()
    class FakeClient:
        messages = FakeMessages()
    monkeypatch.setattr(labels, "_client", lambda: FakeClient())
    out = labels.label_topics({0: ["tunisie", "gouvernement", "loi"]})
    assert out[0] == "Politique nationale"
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/etl/test_labels.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement**

Create `etl/labels.py`:

```python
import logging
logger = logging.getLogger(__name__)

_client_singleton = None
def _client():
    global _client_singleton
    if _client_singleton is None:
        import anthropic
        _client_singleton = anthropic.Anthropic()
    return _client_singleton

def label_topics(topic_keywords: dict[int, list[str]]) -> dict[int, str]:
    client = _client()
    labels_out = {}
    for tid, keywords in topic_keywords.items():
        kw = ", ".join(keywords[:8])
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=24,
                messages=[{"role": "user", "content":
                    f"Ces mots-clés décrivent un thème d'actualité tunisienne : {kw}. "
                    f"Donne un titre de thème court (2-4 mots), en français, sans ponctuation finale."}],
            )
            labels_out[tid] = next(
                (b.text.strip() for b in msg.content if b.type == "text"), f"Topic {tid}")
        except Exception as e:
            logger.warning(f"Label failed for topic {tid}: {e}")
            labels_out[tid] = f"Topic {tid}"
    return labels_out
```

In `etl/cluster.py`, after building `topic_labels` from BERTopic keyword names, derive keyword lists per topic via `topic_model.get_topic(tid)` (returns `[(word, score), ...]`), call `label_topics({tid: [w for w,_ in topic_model.get_topic(tid)]})`, and use the returned labels in `update_topics`. Wrap in `try/except` and fall back to the raw BERTopic names on failure. Add `anthropic` to `requirements.txt`.

- [ ] **Step 4: Run the test** — Run: `pytest tests/etl/test_labels.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/labels.py etl/cluster.py requirements.txt tests/etl/test_labels.py
git commit -m "feat(ml): human-readable topic labels via Claude Haiku"
```

---

# Track C — App, GenAI & UI (Person C)

Branch off after Phase 0 (needs F1 columns + F3 embeddings). Delivers summaries, RAG chat, a timeline endpoint, and the friendly reader UI.

### Task C1: Article summary endpoint (cached)

**Files:**
- Create: `api/routes/genai.py`
- Modify: `api/main.py` (register the router)
- Test: `tests/api/test_genai_summary.py`

**Interfaces:**
- Produces: `GET /genai/summary/{article_id}` → `{"summary": str}`; caches the result in `articles.summary`.

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_genai_summary.py`:

```python
from fastapi.testclient import TestClient
import api.routes.genai as genai
from api.main import app

def test_summary_returns_cached(monkeypatch):
    # DB returns an already-cached summary → no LLM call
    class FakeCur:
        def execute(self, q, p=None): self._q = q
        def fetchone(self): return ("Résumé en cache", "titre", "corps")
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def commit(self): ...
        def close(self): ...
    monkeypatch.setattr(genai, "get_connection", lambda: FakeConn())
    client = TestClient(app)
    r = client.get("/genai/summary/1")
    assert r.status_code == 200
    assert r.json()["summary"] == "Résumé en cache"
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/api/test_genai_summary.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement the router**

Create `api/routes/genai.py`:

```python
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from etl.load import get_connection

logger = logging.getLogger(__name__)
router = APIRouter()

_client_singleton = None
def _client():
    global _client_singleton
    if _client_singleton is None:
        import anthropic
        _client_singleton = anthropic.Anthropic()
    return _client_singleton

@router.get("/summary/{article_id}")
def summary(article_id: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT summary, title, content FROM articles WHERE id=%s", (article_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        raise HTTPException(404, "Article not found")
    cached, title, content = row
    if cached:
        cur.close(); conn.close()
        return {"summary": cached}
    msg = _client().messages.create(
        model="claude-haiku-4-5", max_tokens=160,
        messages=[{"role": "user", "content":
            f"Résume cet article tunisien en 2 phrases claires, en français :\n\n{title}\n{content[:2000]}"}])
    text = next((b.text.strip() for b in msg.content if b.type == "text"), "")
    cur.execute("UPDATE articles SET summary=%s WHERE id=%s", (text, article_id))
    conn.commit(); cur.close(); conn.close()
    return {"summary": text}


class ChatBody(BaseModel):
    q: str

@router.post("/chat")
def chat(body: ChatBody):
    # implemented in Task C2
    raise HTTPException(501, "not implemented")
```

Register in `api/main.py`:
```python
from api.routes import pipeline, articles, search, genai
app.include_router(genai.router, prefix="/genai", tags=["genai"])
```

- [ ] **Step 4: Run the test** — Run: `pytest tests/api/test_genai_summary.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/routes/genai.py api/main.py tests/api/test_genai_summary.py
git commit -m "feat(api): article summary endpoint cached to DB"
```

### Task C2: RAG chat endpoint ("Ask the news")

**Files:**
- Modify: `api/routes/genai.py` (implement `chat`)
- Test: `tests/api/test_genai_chat.py`

**Interfaces:**
- Consumes: `get_embedding` (F3), pgvector.
- Produces: `POST /genai/chat` `{"q": str}` → `{"answer": str, "sources": [{"id","title","url"}]}`.

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_genai_chat.py`:

```python
from fastapi.testclient import TestClient
import api.routes.genai as genai
from api.main import app

def test_chat_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(genai, "get_embedding", lambda q: [0.0] * 384, raising=False)
    class FakeCur:
        def execute(self, q, p=None): ...
        def fetchall(self): return [(1, "Titre A", "https://x.tn/a", "corps a")]
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def close(self): ...
    monkeypatch.setattr(genai, "get_connection", lambda: FakeConn())
    class FakeText: type="text"; text="Réponse fondée sur les sources."
    class FakeMsg: content=[FakeText()]
    monkeypatch.setattr(genai, "_client",
        lambda: type("C", (), {"messages": type("M", (), {"create": lambda s, **k: FakeMsg()})()})())
    client = TestClient(app)
    r = client.post("/genai/chat", json={"q": "Que se passe-t-il en Tunisie ?"})
    assert r.status_code == 200
    assert r.json()["sources"][0]["title"] == "Titre A"
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/api/test_genai_chat.py -v` — Expected: FAIL (`chat` returns 501).

- [ ] **Step 3: Implement `chat`**

Replace the `chat` stub in `api/routes/genai.py`. Import at top: `from etl.transform import get_embedding`.

```python
@router.post("/chat")
def chat(body: ChatBody):
    emb = get_embedding(body.q)
    emb_str = f"[{','.join(map(str, emb))}]"
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT id, title, url, content
        FROM articles
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (emb_str,))
    rows = cur.fetchall(); cur.close(); conn.close()
    context = "\n\n".join(f"[{i+1}] {r[1]}\n{r[3][:800]}" for i, r in enumerate(rows))
    msg = _client().messages.create(
        model="claude-haiku-4-5", max_tokens=512,
        system="Tu réponds aux questions sur l'actualité tunisienne en te basant "
               "UNIQUEMENT sur les articles fournis. Cite les numéros de source. "
               "Si l'info manque, dis-le.",
        messages=[{"role": "user", "content": f"Articles:\n{context}\n\nQuestion: {body.q}"}])
    answer = next((b.text.strip() for b in msg.content if b.type == "text"), "")
    return {"answer": answer,
            "sources": [{"id": r[0], "title": r[1], "url": r[2]} for r in rows]}
```

- [ ] **Step 4: Run the test** — Run: `pytest tests/api/test_genai_chat.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/routes/genai.py tests/api/test_genai_chat.py
git commit -m "feat(api): RAG chat over articles via pgvector + Claude"
```

### Task C3: Sentiment-over-time endpoint

**Files:**
- Modify: `api/routes/articles.py` (add `/timeline`)
- Test: `tests/api/test_timeline.py`

**Interfaces:**
- Produces: `GET /articles/timeline?days=30` → `[{"date","positive","neutral","negative"}]`, grouped by `published_at::date` (fall back to `scraped_at` when null).

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_timeline.py`:

```python
from fastapi.testclient import TestClient
import api.routes.articles as articles
from api.main import app

def test_timeline_shape(monkeypatch):
    class FakeCur:
        def execute(self, q, p=None): self._q = q
        def fetchall(self): return [("2026-07-10", 3, 2, 1)]
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def close(self): ...
    monkeypatch.setattr(articles, "get_connection", lambda: FakeConn())
    client = TestClient(app)
    r = client.get("/articles/timeline?days=30")
    assert r.status_code == 200
    assert r.json()[0]["positive"] == 3
```

- [ ] **Step 2: Run it to confirm it fails** — Run: `pytest tests/api/test_timeline.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement**

Add to `api/routes/articles.py` (place BEFORE the `/{article_id}` route so the path isn't captured by it):

```python
@router.get("/timeline")
def timeline(days: int = Query(30, le=365)):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(published_at::date, scraped_at::date) AS d,
               COUNT(*) FILTER (WHERE sentiment='positive') AS pos,
               COUNT(*) FILTER (WHERE sentiment='neutral')  AS neu,
               COUNT(*) FILTER (WHERE sentiment='negative') AS neg
        FROM articles
        WHERE COALESCE(published_at, scraped_at) >= NOW() - (%s || ' days')::interval
        GROUP BY d ORDER BY d
    """, (days,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return [{"date": str(r[0]), "positive": r[1], "neutral": r[2], "negative": r[3]}
            for r in rows]
```

- [ ] **Step 4: Run the test** — Run: `pytest tests/api/test_timeline.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/routes/articles.py tests/api/test_timeline.py
git commit -m "feat(api): sentiment-over-time timeline endpoint"
```

### Task C4: Reader UI — magazine layout with images

**Files:**
- Create: `frontend/src/pages/Reader.jsx` + `Reader.module.css`
- Create: `frontend/src/components/HeroCard.jsx`
- Modify: `frontend/src/App.jsx` (make `/` the Reader, move dashboard to `/dashboard`)
- Modify: `frontend/src/components/Sidebar.jsx` (add Reader link), `frontend/src/index.css` (light+dark tokens)

> Note: the frontend has no test harness. These tasks are verified by running the app (Step "Verify"), not by unit tests — that matches the existing codebase, which ships no frontend tests.

**Interfaces:**
- Consumes: `GET /articles/?limit=…` (has `image_url`, `published_at`, `topic_label`, `sentiment`), `GET /articles/topics`.

- [ ] **Step 1: Build the Reader page**

Create `frontend/src/pages/Reader.jsx`: fetch `client.get('/articles/', { params: { limit: 21 } })`; render the first article in a full-width `HeroCard` (large image, title, source, date, sentiment badge) and the rest in a responsive card grid (`ArticleCard`, reused). Add a category/source tab bar across the top that filters the grid client-side. Open articles in the existing `ArticleModal`. On modal open, fetch `GET /genai/summary/{id}` and show the TL;DR at the top (wired in C5 if you prefer to batch UI work).

Concrete grid CSS (add to `Reader.module.css`):
```css
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
.hero { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; margin-bottom: 28px; }
.hero img, .card img { width: 100%; height: 100%; object-fit: cover; border-radius: 12px; }
@media (max-width: 720px) { .hero { grid-template-columns: 1fr; } }
```

- [ ] **Step 2: Add light + dark theme tokens**

In `frontend/src/index.css`, define CSS variables for both themes and default to the system preference:
```css
:root { --bg:#f7f7f5; --card:#fff; --text:#1a1a1a; --muted:#666; --accent:#c1440e; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#0d0d0f; --card:#161618; --text:#f1f5f9; --muted:#94a3b8; --accent:#f97316; }
}
```
Point existing component styles at these variables where they currently hardcode dark hexes (Dashboard can keep its own look).

- [ ] **Step 3: Route the Reader as the landing page**

In `frontend/src/App.jsx`, set `path="/"` to `<Reader />`, move the dashboard to `path="/dashboard"`, and add a "Reader" + "Dashboard" entry to `Sidebar.jsx`.

- [ ] **Step 4: Verify by running**

Run: `make api` (terminal 1) and `make frontend` (terminal 2); open `http://localhost:5173`.
Expected: a magazine layout with a hero story, image cards, working source/category tabs, in light and dark mode; clicking a card opens the modal.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Reader.jsx frontend/src/pages/Reader.module.css \
        frontend/src/components/HeroCard.jsx frontend/src/App.jsx \
        frontend/src/components/Sidebar.jsx frontend/src/index.css
git commit -m "feat(ui): magazine-style news reader with images, tabs, light+dark"
```

### Task C5: "Ask the news" chat panel + timeline chart + summaries in modal

**Files:**
- Create: `frontend/src/pages/Chat.jsx` + `Chat.module.css`
- Modify: `frontend/src/pages/Dashboard.jsx` (add a timeline `LineChart`)
- Modify: `frontend/src/components/ArticleModal.jsx` (show the summary)
- Modify: `frontend/src/App.jsx` + `Sidebar.jsx` (add `/chat` route + link)

**Interfaces:**
- Consumes: `POST /genai/chat`, `GET /articles/timeline`, `GET /genai/summary/{id}`.

- [ ] **Step 1: Chat page**

Create `frontend/src/pages/Chat.jsx`: a simple message list + input; on submit `client.post('/genai/chat', { q })`, render the answer and a "Sources" list linking each `source.url`. Add the `/chat` route and a "Ask the news" sidebar link.

- [ ] **Step 2: Timeline chart on the dashboard**

In `Dashboard.jsx`, fetch `client.get('/articles/timeline', { params: { days: 30 } })` and render a Recharts `LineChart` with three series (positive/neutral/negative) using the existing `SENTIMENT_COLORS`.

- [ ] **Step 3: Summary in the article modal**

In `ArticleModal.jsx`, on mount fetch `GET /genai/summary/{article.id}` and render the returned text as a highlighted "TL;DR" block above the content (show a small "Résumé…" spinner while loading).

- [ ] **Step 4: Verify by running**

Open `http://localhost:5173/chat`, ask a question → see an answer + clickable sources. Open the dashboard → see the sentiment timeline. Open any article → see the TL;DR.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Chat.jsx frontend/src/pages/Chat.module.css \
        frontend/src/pages/Dashboard.jsx frontend/src/components/ArticleModal.jsx \
        frontend/src/App.jsx frontend/src/components/Sidebar.jsx
git commit -m "feat(ui): ask-the-news chat, sentiment timeline, article TL;DR"
```

---

# Shared — Quality gate

### Task Q1: CI workflow running the test suite

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `tests/__init__.py` and package `__init__.py` files as needed; `pytest.ini`

**Interfaces:**
- Produces: green CI on push/PR: install deps, run `pytest -m "not integration"`, run frontend `npm run build`.

- [ ] **Step 1: Add pytest config that excludes DB-integration tests by default**

Create `pytest.ini`:
```ini
[pytest]
markers =
    integration: tests that need a live Postgres
addopts = -m "not integration"
```

- [ ] **Step 2: Add the CI workflow**

Create `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt pytest
      - run: pytest -m "not integration" -q
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci && npm run build
```

- [ ] **Step 3: Run the suite locally first**

Run: `pytest -q`
Expected: all non-integration tests pass. Fix any import errors (missing `__init__.py`, etc.).

- [ ] **Step 4: Commit and push to see CI run**

```bash
git add .github/workflows/ci.yml pytest.ini tests/**/__init__.py
git commit -m "ci: run pytest + frontend build on push"
```

---

## Coverage map (spec → tasks)

| Spec item | Task(s) |
|---|---|
| RSS-first multi-source ingestion | A1, A3 |
| published_at / image_url / categories stored | F1, A4 |
| e5-small + correct prefixes | F3 |
| Batched sentiment | F4 |
| MLflow tracking + registry | F5, B1 |
| Monitoring metrics (pipeline_metrics) | F1, B2 |
| LLM topic labels | B3 |
| Article summaries (cached) | C1, C5 |
| RAG "ask the news" chat | C2, C5 |
| Sentiment time-series | C3, C5 |
| Friendly magazine reader UI (light+dark) | C4 |
| Pydantic validation | F2 |
| Tests + CI | every task's tests, Q1 |
| Delete dead tap stub | F5 |

## Deferred to backlog (NOT in this plan)

Arabic sources + RTL, NER/entities population, story-cluster grouping (`story_id`), drift metrics + Prometheus/Grafana, DVC, connection pooling, personalization/alerts. Columns/tables for these (`story_id`, `entities`) are created in F1 so the backlog work needs no further migration.
