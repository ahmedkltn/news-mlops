# Editorial defense deck (v2) — design

**Date:** 2026-07-14
**Status:** approved by Ahmed (brainstorming session)
**Replaces:** `presentation/index.html` / `News-Insight-slides.pdf` as the deck to present. The old files stay in the repo untouched.

## Problem

The current 19-slide deck follows the earlier assertion-evidence spec, but Ahmed's verdict after review: it reads AI-generated and shallow. Three specific complaints:

1. **Too sparse.** One-line headline plus one visual per slide carries no reasoning. The deck never shows *why* a component was chosen or what the real numbers are, so it does not demonstrate the team's understanding.
2. **Template look.** White background, navy accent, centered uniform boxes — recognizably a generated template.
3. **Abstract diagrams.** Box-and-arrow graphics feel generic; no real evidence (actual metrics, real MLflow/Prefect runs, code).

The narrative order (problem → product → architecture → contributions) is fine and is kept.

## Decisions made

| Question | Decision |
|---|---|
| Who builds it | Claude, in this repo (not Canva, not claude.ai/design) |
| Style | Editorial newspaper — the deck looks like Tuniscope itself |
| Length | ~15 dense slides, no filler section dividers |
| Approach | New deck from scratch (`presentation/index-v2.html`); old deck untouched |
| Language | English; note that the product UI is French |

## Slide outline (15 slides)

Every slide uses the newspaper layout: red small-caps kicker (`PART N · SECTION`), serif assertion headline, evidence (figure / table / diagram), and a WHY margin note carrying the reasoning. Every number on a slide comes from a real query or a real capture.

1. **Title** — Tuniscope-style front page: masthead, project title, team (Ahmed Klabi, Mariem Smadhi, Hichem Sboui), supervisor (Sawssen Jalel), TEK-UP, edition date, and a small "in this edition" index strip (replaces the agenda slide).
2. **Problem** — "Tunisian news is scattered, unsearchable, unmeasured." Evidence: the real source sites. WHY margin: who needs this (readers, analysts) and what they cannot do today (search by meaning, see mood, see regions).
3. **What we built** — one pipeline: collect → understand → serve. Real stat strip: 60 articles · 4 scrapers · 5 models · 24 governorates · 1 `docker-compose up`. (Counts re-verified at build time.)
4. **Product: unified feed** — `shot-home.png` as Fig. 1; every card tagged source + topic + mood.
5. **Product: analytics + map** — `shot-dashboard.png` + `shot-map.png`; real sentiment split (currently 45% neg / 28% neu / 27% pos) and top themes.
6. **Product: search + assistant** — `shot-search.png` + `shot-chat.png`; search by meaning, answers cite sources.
7. **Architecture** — redrawn editorial diagram with labeled arrows and glosses. WHY margin: why one `articles` table, why pgvector instead of a dedicated vector DB.
8. **Collection reality** — 4 scrapers, Kapitalis HTML deep-crawl fallback, dedup `ON CONFLICT (url)` → idempotent re-runs. Honest ops note: only 3 of 4 feeds delivered rows in the current window.
9. **Enrichment models** — table: e5-small (384-dim embedding), XLM-RoBERTa (sentiment), Groq LLM (theme, 1 of 10), gazetteer + LLM (region → governorate); each row has output + WHY chosen (multilingual FR/AR, CPU-cheap, fixed label space...).
10. **Topic discovery** — BERTopic clusters → LLM names topics → MLflow logs the run. Evidence: real MLflow run screenshot; 9 topics in the current corpus.
11. **Orchestration + monitoring** — Prefect: cron 06:00 Africa/Tunis, HTTP trigger, retries 2×/60s. Evidence: real Prefect UI run screenshot + the first real `pipeline_metrics` row (the table is empty today; we trigger a run during the build to populate it, and say so honestly on the slide).
12. **RAG mechanics** — question → e5 embed → `cosine <=>` top-5 → Groq reads only those 5 → cited answer. Evidence: the actual SQL snippet + a real chat answer. WHY: grounding beats fine-tuning for freshness and cost.
13. **Engineering & reproducibility** — 5 containers with names and ports, single `articles` table schema chips, test count from pytest. Text treatment, no logo wall.
14. **Contributions** — 4 claims with evidence pointers + honest limits (60-article / 2-day corpus, French-first) + condensed future work.
15. **Thanks / Q&A** — back-page style.

## Visual system

- **Paper** warm white `#faf9f7`; **ink** near-black `#1a1a1a`; **accent** Tuniscope red — exact hex read from `frontend/` CSS at build time. One accent only.
- **Type:** serif display for headlines (Playfair Display, Georgia fallback) matching Tuniscope's masthead look; sans body; mono for code, ports, SQL. Small-caps red kickers.
- **Structure:** double-rule masthead on every slide; hairline column rules; folio footer `News Insight · soutenance · N/15`.
- **Figures:** screenshots framed by hairline rules, small-caps `Fig. N` captions, one-line italic gloss under each.
- **Diagrams:** rebuilt in the same style — ink boxes, red labeled arrows (`new rows →`, `store →`, `cosine <=> →`), a plain-language gloss beside every technical term.
- **Banned:** gradients, drop shadows, emojis, rounded SaaS cards, logo walls, decorative blobs.

## Evidence plan

1. Trigger one pipeline run (Prefect HTTP trigger) so `pipeline_metrics` gets its first real row and MLflow gets a fresh run.
2. Capture with Playwright: MLflow run page (`:5000`), Prefect flow-run page (`:4200`).
3. Reuse the 5 existing app screenshots in `presentation/img/` (captured 2026-07-13, still current).
4. Re-run the DB queries at build time; slides show only queried numbers, never invented ones.

## Tooling & output

- New file `presentation/index-v2.html`, same `show(n)` slide mechanism as the old deck.
- Render every slide with Playwright at 1400×820 and eyeball for overflow before delivering.
- Export `presentation/News-Insight-slides-v2.pdf` (Playwright PDF export script in the session scratchpad).
- Old deck (`index.html`, `News-Insight-slides.pdf`) is not modified or deleted.

## Out of scope

- No changes to the app, pipeline code, or report (the pipeline run uses the existing HTTP trigger only).
- No French translation of the deck.
- No PPTX export.
