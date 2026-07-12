# Spec — Tunisia Region Map (per-governorate news)

**Date:** 2026-07-12
**Status:** Draft for approval
**Depends on:** the Tunisia News Hub base (articles table, FastAPI, React) — PRs #3 (runnable stack + fallback) and #4 (Tuniscope UI). Builds on [`2026-07-11-tunisia-news-hub-design.md`](2026-07-11-tunisia-news-hub-design.md).

---

## 1. What & why

An interactive **choropleth map of Tunisia's 24 governorates**. Each governorate is shaded by news activity; clicking one drills into that region's news — article count, sentiment split, top topics, and the latest headlines — reusing the existing sentiment/topic/article components.

**Why it fits the product.** The hub's promise is "all Tunisian news in one place." A map answers a question no feed can: *what's happening where*. It turns the sentiment/topic data we already compute into a geographic story (e.g. "Sfax is trending negative on flooding; Sousse positive on tourism"), and it's a strong, demo-able differentiator for both the academic writeup (a new ML step: geo-tagging) and the product vision.

**Academic angle.** Region tagging is a genuine NLP sub-task (gazetteer NER + LLM disambiguation), with its own metrics (coverage %, tagged %, precision on a hand-labelled sample) that plug into the existing MLflow/monitoring story.

---

## 2. User stories

- As a reader, I open **Carte** (Map), see Tunisia shaded by article volume, and immediately spot the most active regions.
- I **click Sfax** → a side panel shows: N articles, sentiment donut, top 5 topics, latest 5 headlines (each opens the existing ArticleModal).
- I toggle the map metric between **Volume** and **Sentiment dominant** (which sentiment leads per region).
- Articles with no detectable region are grouped under **"National / non localisé"** and never silently dropped.

---

## 3. Data model

Add one nullable column (a region is a derived, optional attribute of an article):

```sql
-- db/migrations/002_region.sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS region TEXT;              -- canonical governorate slug, e.g. 'sfax'
CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region);
```

Also add to `db/schema.sql` so a fresh DB has it (matches the pattern used for `published_at`/`image_url`).

**Canonical regions.** 24 governorate slugs (ASCII, lowercase, no diacritics):
`tunis, ariana, ben-arous, manouba, nabeul, zaghouan, bizerte, beja, jendouba, kef, siliana, sousse, monastir, mahdia, sfax, kairouan, kasserine, sidi-bouzid, gabes, medenine, tataouine, gafsa, tozeur, kebili`.
`region IS NULL` ⇒ untagged / national.

A single source of truth `etl/regions.py::GOVERNORATES` holds slug → `{fr, ar, aliases[], geojson_id}` and is imported by tagging, API, and the GeoJSON id-matcher.

---

## 4. Region tagging (the ML step)

Two-tier, cheap-first. Runs as a pipeline step after extraction, before/with transform.

### Tier 1 — Gazetteer match (free, deterministic, covers most)
- Build a lookup from `GOVERNORATES`: governorate names + **major cities/delegations** + common **aliases**, in **French and Arabic** (e.g. sfax ← "Sfax", "صفاقس", "Sakiet Ezzit"; tunis ← "Tunis", "تونس", "La Marsa", "Le Bardo").
- Normalize (lowercase, strip diacritics, word-boundary regex) over `title + content`.
- Score by hit count + position (title hits weighted higher). If a clear winner ⇒ assign. Ties/multiple ⇒ Tier 2.
- Curated seed list (~150 place→governorate entries) lives in `etl/regions.py`; expandable.

### Tier 2 — LLM disambiguation (fallback, low volume)
- Only for articles with **0 or ambiguous** gazetteer hits.
- Reuse `etl/llm.complete` (Groq, `FAST_MODEL`) with a constrained prompt: "Quelle région/gouvernorat de Tunisie concerne cet article ? Réponds par un seul slug parmi [liste], ou 'national' si aucun." Validate the answer against the slug set; anything invalid ⇒ NULL.
- Keeps within free-tier limits because Tier 1 handles the bulk.

### Output
`tag_region(title, content) -> str | None`. Wired into the pipeline; writes `articles.region`. A backfill script tags existing rows (same pattern as the sentiment/image backfills already used).

**Metrics** (into `pipeline_metrics` + MLflow): `region_tagged_pct`, `region_llm_fallback_pct`, per-run region histogram. Optional: a small hand-labelled eval set (~50 articles) for precision.

---

## 5. API

```
GET /articles?region=sfax          # existing endpoint — add `region` filter (mirrors source/sentiment)
GET /articles/regions              # NEW — aggregate for the map
```

`/articles/regions` response (one row per governorate that has ≥1 article; regions with 0 still returned as 0 so the map colours them):
```json
[
  { "region": "sfax", "count": 12,
    "sentiments": { "positive": 3, "neutral": 5, "negative": 4 },
    "dominant": "negative" },
  ...
  { "region": null, "count": 7, "sentiments": {…}, "dominant": "neutral" }  // national bucket
]
```
Single grouped SQL query (`GROUP BY region` with `FILTER` counts) — cheap, no new deps. Region drill-down list reuses `/articles?region=…&limit=5`; topics reuse `/articles/topics` filtered client-side or a `?region=` param.

---

## 6. Frontend

New route/section **Carte** in the masthead nav (between Analyses and Assistant IA).

**Library:** `react-simple-maps` (SVG, lightweight, no runtime tiles, works offline behind the strict setup) + a **Tunisia governorates GeoJSON/TopoJSON** committed to `frontend/src/assets/tunisia-governorates.json` (source: geoBoundaries ADM1 / Natural Earth, simplified with mapshaper to keep it small). Each feature carries a `geojson_id` matched to a slug via `GOVERNORATES`.
- Fallback option if react-simple-maps disappoints: raw inline SVG paths (same GeoJSON, hand-rendered) — no extra dep.

**Map component (`RegionMap`)**
- Fetches `/articles/regions`, builds slug → metrics map.
- Choropleth fill: **Volume** (sequential brand-red scale by count) or **Sentiment** (green/grey/red by `dominant`) — a segmented toggle.
- Governorate: hover ⇒ tooltip (name + count + dominant sentiment); click ⇒ selects region.
- Accessibility: each path is a `<button>`-role, keyboard-focusable, `aria-label="Sfax — 12 articles"`; colour is never the only signal (tooltip + panel carry text). Respects reduced-motion.

**Drill-down panel (`RegionPanel`)** — slides in on select:
- Header: governorate name + count.
- Sentiment donut (reuse the Dashboard recharts Pie).
- Top topics (reuse the bar or a chip list).
- Latest 5 headlines → existing `ArticleCard`/`ArticleModal`.
- "National / non localisé" is selectable too (the `region IS NULL` bucket).

**Home teaser (optional):** a compact non-interactive map card on À la une linking to Carte.

---

## 7. Implementation plan (TDD, phased)

Each task: RED (failing test) → GREEN, fresh subagent + review, per the existing SDD flow.

**Phase R0 — data & gazetteer**
- R0.1 `etl/regions.py`: `GOVERNORATES` table + normalize helper. Tests: slug set == 24, alias lookup, diacritic-insensitive match.
- R0.2 migration `002_region.sql` + schema.sql; column + index.

**Phase R1 — tagging**
- R1.1 `tag_region()` Tier 1 gazetteer. Tests: known city → governorate; title-weighting; no-match → None; Arabic alias.
- R1.2 Tier 2 LLM fallback (mocked LLM in tests, slug-validation). Tests: valid slug passes, invalid/hallucinated → None.
- R1.3 pipeline wiring + `region` persisted in `save_articles`; backfill script for existing rows.
- R1.4 metrics: tagged %, fallback %.

**Phase R2 — API**
- R2.1 `region` filter on `/articles`. Tests: filter returns only that region; NULL handling.
- R2.2 `/articles/regions` aggregate. Tests: counts + sentiments + dominant + national bucket.

**Phase R3 — frontend**
- R3.1 add `react-simple-maps` + committed GeoJSON; `RegionMap` renders 24 shapes.
- R3.2 choropleth + Volume/Sentiment toggle + tooltip + keyboard a11y.
- R3.3 `RegionPanel` drill-down reusing charts + ArticleCard/Modal.
- R3.4 masthead nav entry + route; empty/loading states; responsive (map scales, panel becomes bottom sheet on mobile).

**Phase R4 — polish/QA**
- Reduced-motion, dark-mode map palette, contrast ≥3:1 on fills, tab order, mobile.

---

## 8. Decisions & risks

- **One region per article (v1).** Simpler model/UI. Multi-region (array + weights) is a documented v2.
- **GeoJSON licensing/accuracy.** Use an openly-licensed ADM1 source (geoBoundaries CC-BY / Natural Earth public domain); attribute in the repo. Simplify to keep bundle small (<100 KB).
- **Gazetteer coverage is the quality driver.** Untagged articles are a *visible* "National" bucket, not a silent drop — honest and still useful. Iterate the place list from real misses.
- **Free-tier budget.** Tier-1-first keeps LLM calls low; the region prompt uses `FAST_MODEL`. If volume grows, cache tagging by article (already persisted, tagged once).
- **Arabic content.** Aliases include Arabic; normalize handles both scripts. Sources are currently FR — Arabic mostly future-proofing.

## 9. Out of scope (v1)
Sub-governorate (delegation) granularity; multi-region articles; time-animated map; per-region alerts/subscriptions; map-based search.

## 10. Definition of done
Carte in the nav; 24 governorates render and shade by live data; click drills into real per-region sentiment/topics/headlines; untagged articles reachable via the National bucket; region tagging runs in the pipeline with metrics; tests green; works light/dark, desktop/mobile, keyboard.
