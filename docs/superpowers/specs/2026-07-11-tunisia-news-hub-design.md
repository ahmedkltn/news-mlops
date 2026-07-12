# Tunisia News Hub — Design & Improvement Roadmap

**Date:** 2026-07-11
**Team:** 3 people
**Deadline:** 2 days for the core slice; remainder is a prioritized backlog
**Type:** School project framed as a mix of academic MLOps + real product

---

## 1. Product vision

**One place for all Tunisian news.** Instead of hopping between Facebook, Mosaïque, Kapitalis and a dozen other sites, the user opens one hub that aggregates every source, removes duplicate coverage, organizes stories by topic, and lets them search or ask questions in natural language.

Think **"Google News for Tunisia, plus an AI layer"** — multilingual (French, Arabic, English), with sentiment, topic clustering, cross-source story grouping, summaries, and a chat-over-the-news assistant.

The same backend serves **two faces**:

- **Public news reader** — friendly magazine-style UI (hero story, image cards, category tabs, trending sidebar, "Ask the news" chatbot). This is the product.
- **Analytics dashboard** — sentiment/topic trends over time, pipeline health, MLflow tracking. This is the academic / MLOps face.

**Signature feature:** *story clustering* — the same event covered by multiple outlets is grouped into one "story" card ("5 sources covered this"). This reuses the existing embeddings + pgvector, so it is cheap to build and is the feature that makes the product feel like a real aggregator rather than a list.

---

## 2. Current state (baseline)

Working today:

- **Scrape:** one source — Kapitalis (French), BeautifulSoup, polite delay, URL dedup.
- **Transform:** embeddings (`paraphrase-multilingual-MiniLM-L12-v2`, 384-d) + sentiment (`cardiffnlp/twitter-xlm-roberta-base-sentiment`).
- **Store:** Postgres + pgvector.
- **Cluster:** BERTopic (French).
- **API:** FastAPI — articles list / stats / topics, semantic search, pipeline trigger.
- **Frontend:** React + Vite, dark dashboard, 4 pages (Dashboard, Articles, Search, Pipeline), Recharts.
- **Orchestrate:** Prefect, daily cron 06:00 Africa/Tunis.

### Known gaps and bugs (found in code review)

| # | Issue | Impact |
|---|---|---|
| 1 | `scrapers/tap.py` is an empty stub | Only one real source |
| 2 | `published_at` is scraped but no DB column exists; load functions drop it | No real publish date; feeds sort by `scraped_at` (wrong for news) |
| 3 | `"passage: "` prefix is applied to `paraphrase-MiniLM` (that prefix is an E5 convention); search also prefixes queries with `passage:` instead of `query:` | Weaker retrieval than the model can give |
| 4 | Sentiment runs one article per loop while embeddings are batched | Slow transform |
| 5 | "MLOps" project but MLflow is commented out — no tracking, registry, or metric logging | Weak for the project's stated purpose |
| 6 | No Arabic sources | Half of Tunisia's news space is missing |
| 7 | No time-series of sentiment/topics | Core news-analytics feature absent |
| 8 | BERTopic refits from scratch each run; topic IDs change run-to-run | Topics not stable over time |
| 9 | Only `test_kap.py`; no pipeline/API tests, no CI | No safety net |
| 10 | New DB connection per request, no pool | Fine now, weak at scale |

---

## 3. Architecture decisions

### 3.1 Ingestion: RSS-first, HTML fallback

Most Tunisian sites run WordPress and expose a clean `/feed/` RSS with title, link, **pubDate**, content, and categories. Verified working feeds:

- Kapitalis — `https://kapitalis.com/tunisie/feed/`
- La Presse — `https://lapresse.tn/feed/`
- Business News — `https://www.businessnews.com.tn/rss.xml`

**Decision:** add a generic `RSSScraper(feed_url, source, language)` class alongside the existing `BaseScraper`. One class covers many sources, gives clean publish dates and categories for free, and is far more stable than per-site HTML selectors. Keep HTML scraping as the fallback for sources without a feed. Fetch `og:image` from the article page (or the RSS media tag) for card thumbnails.

**Alternatives considered:** (a) a hand-written HTML scraper per source — too brittle and slow to add sources; (b) a paid NewsAPI — does not cover Tunisian local outlets well and adds cost. RSS-first wins on speed, stability, and coverage.

### 3.2 Embedding model

**Decision:** switch to `intfloat/multilingual-e5-small` (still **384-d**, so no schema change) and use the correct `query:` / `passage:` prefixes. E5 is trained for retrieval and handles French, Arabic, and English, which the multilingual source plan requires. This fixes bug #3 and improves both semantic search and story clustering.

### 3.3 Two-faces frontend

**Decision:** keep the analytics dashboard, add a public **news reader** as the default landing experience. Magazine layout, light + dark themes, image cards, category tabs, hero story, trending sidebar, and an "Ask the news" chat panel. Right-to-left support is added when Arabic sources land (backlog).

### 3.4 Story clustering (signature feature)

**Decision:** after embedding, group articles whose cosine similarity exceeds a threshold within a rolling time window into a `story_id`. This is a lightweight pass over pgvector, independent of BERTopic (which stays for broad topics). Renders as "N sources covered this story."

---

## 4. Data model changes

```sql
-- articles: new columns
ALTER TABLE articles ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS image_url    TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS categories   TEXT[];
ALTER TABLE articles ADD COLUMN IF NOT EXISTS summary      TEXT;      -- GenAI TL;DR
ALTER TABLE articles ADD COLUMN IF NOT EXISTS story_id     INTEGER;   -- near-dup story cluster

-- entities from NER (P1)
CREATE TABLE IF NOT EXISTS entities (
    id          SERIAL PRIMARY KEY,
    article_id  INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    label       TEXT NOT NULL          -- PER / ORG / LOC / MISC
);

-- pipeline + model metrics for monitoring
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id           SERIAL PRIMARY KEY,
    run_at       TIMESTAMP DEFAULT NOW(),
    source       TEXT,
    articles_new INTEGER,
    n_topics     INTEGER,
    outlier_pct  REAL,
    sentiment_pos INTEGER,
    sentiment_neu INTEGER,
    sentiment_neg INTEGER,
    embed_model  TEXT
);
```

`published_at` also becomes the default sort key for the reader feed.

---

## 5. Workstreams and the 2-day plan

Everything selected cannot ship in two days. Each person owns one vertical that delivers a visible win. **P0 = must-have for the 2-day slice. P1/P2 = backlog.**

### Person A — Data pipeline & sources

- **P0:** `RSSScraper` generic class; wire 4 feeds (Kapitalis, La Presse, Business News, +1). Add `published_at`, `image_url`, `categories` columns + migration and store them. Scrape `og:image`. Upgrade `Article` to a **Pydantic** model with validation (non-empty title/content, valid URL, language detected) and keep URL dedup.
- **P1:** Arabic source(s) (Assabah / Al Chourouk) + language detection. Near-duplicate detection to skip re-published wire copy.
- **P2:** DVC data versioning; connection pooling.

### Person B — ML & MLOps

- **P0:** Swap to `multilingual-e5-small` with correct prefixes; **batch sentiment**; wire **MLflow** (uncomment compose, log transform + cluster metrics, register the BERTopic and embedding model versions); write `pipeline_metrics` rows each run; **LLM topic labels** (Claude Haiku) replacing raw BERTopic keyword names.
- **P1:** Stable topics via saved-model `.transform()`; NER pass into `entities`; embedding/topic **drift** metrics.
- **P2:** Prometheus + Grafana; model-registry promotion workflow.

### Person C — App, GenAI & UI

- **P0:** Redesign the reader into a **news-magazine layout** (light + dark, image cards, hero, category tabs, trending sidebar); **time-series** sentiment/topic chart on the dashboard; **`/summarize`** endpoint (Haiku TL;DR, cached to `summary` column) and **`/chat`** RAG endpoint over pgvector with an "Ask the news" UI.
- **P1:** Story-cluster cards ("N sources covered this"); entity explorer; RTL for Arabic.
- **P2:** Follow-topics personalization; email/push alerts; geolocation heatmap.

### Shared — quality

- **P0:** Each person writes `pytest` tests for their module (scraper parses a saved HTML/RSS fixture; transform prefix + batching; API endpoints). One **GitHub Actions** CI workflow runs lint + tests on push.

---

## 6. Success criteria

**2-day slice is done when:**

1. The pipeline ingests **4+ sources** via RSS with real `published_at` and thumbnails, and stored data passes Pydantic validation.
2. Semantic search uses **e5-small with correct prefixes**; a spot-check query returns clearly relevant articles.
3. **MLflow** shows at least one logged run with cluster + sentiment metrics and a registered model.
4. The **reader UI** looks like a news site (hero + image cards + category tabs), works in light and dark, and is mobile-responsive.
5. **Summaries** appear on article cards and the **"Ask the news"** chatbot answers from retrieved articles.
6. **CI is green** on `main` with tests for each module.

**Quick-win bugs fixed regardless (hours, high ROI):** #2 (`published_at` storage), #3 (embedding prefix), #1 (delete/implement `tap.py`), #4 (batch sentiment).

---

## 7. Risks

- **Scope vs. 2 days.** Mitigation: strict P0/P1/P2; verticals are independent so a slip in one does not block the others.
- **LLM cost/keys.** Summaries and chat need an API key; Haiku is cheap. Cache summaries in the `summary` column so each article is summarized once.
- **RSS coverage gaps.** Some sources lack a feed; HTML fallback and the existing Kapitalis scraper cover those.
- **Arabic complexity (NLP + RTL).** Deliberately P1, not P0, to protect the 2-day slice.

---

## 8. Backlog (post-2-day, prioritized)

1. Arabic sources + RTL UI + language detection.
2. Story-cluster cards and cross-source coverage view.
3. NER entity explorer + entity frequency charts.
4. Drift monitoring + Prometheus/Grafana + alerts.
5. Personalization (follow topics), notifications.
6. DVC data versioning; connection pooling; deployment.
