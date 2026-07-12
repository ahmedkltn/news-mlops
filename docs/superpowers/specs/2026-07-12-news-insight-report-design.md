# News Insight — Project Report (Rapport) Design

Date: 2026-07-12
Status: approved

## Goal

Produce an academic end-of-semester project report for the news-mlops project, in the style and template of the PriceRadar example report (`~/Downloads/PriceRadar.zip`). Deliverable is a LaTeX source tree that compiles to a ~50-page English PDF.

## Deliverable

- New `report/` directory at the repo root.
- ISI LaTeX template (class `isipfe.cls`, cover pages, resume/abstract back cover, signatures) copied from the PriceRadar example.
- Compiles locally with `latexmk` (XeLaTeX, as required by the template) to `report/main.pdf`.
- A `report/README.md` with one-line build instructions.

## Cover page (global_config.tex)

| Field | Value |
|---|---|
| Title | News Insight: An MLOps Platform for Tunisian News Analysis |
| Author | Ahmed Klabi |
| Second/third authors | Mariem Smadhi, Hichem Sboui (isBinomal = true, fourth author empty) |
| Diploma | End-of-Semester Project |
| Speciality | Data Science and AI |
| Academic supervisor | Sawssen Jalel (speciality field left empty — not provided) |
| Professional supervisor / company | none (empty, same as example) |
| Year | 2025-2026 |
| French abstract | empty (English-only report, same as example) |
| English abstract | rewritten for news-mlops: scraping Tunisian news, NLP analysis (embeddings, sentiment, topics), GenAI features, MLOps stack |
| Keywords | News Analysis, MLOps, Web Scraping, NLP, BERTopic, Sentence Transformers, pgvector, FastAPI, Prefect, MLflow, GenAI, RAG |

## Chapter structure (11 chapters)

Follows the PriceRadar per-layer structure, adapted: the dbt transformation chapter is replaced by an ML/NLP chapter, and a dedicated GenAI chapter is added.

1. **Introduction** — project context (Tunisian news landscape, information fragmentation), problem statement, objectives, work methodology (agile, GitHub flow: branches/PRs/commit history replaces the example's Linear screenshots), technology stack overview with logos.
2. **Global Architecture** — high-level architecture diagram, UML use case diagram, class diagram of core entities (Article, Topic/Theme, Region, Summary), sequence diagrams (scrape→transform→cluster pipeline, AI semantic search, ask-the-news chat).
3. **Data Ingestion and Web Scraping** — scraper design (`scrapers/base.py`, `kapitalis.py`, `rss.py`), BeautifulSoup extraction, deduplication, raw article storage, error handling.
4. **Storage Layer and Database Design** — PostgreSQL + pgvector choice, schema (`db/schema.sql`, migrations 001/002 incl. regions), embedding storage and vector indexing.
5. **Machine Learning and NLP Pipeline** — sentence-transformers embeddings, cardiffnlp sentiment analysis, BERTopic clustering (`etl/cluster.py`), themes/labels/regions enrichment (`etl/themes.py`, `labels.py`, `regions.py`), pipeline metrics (`etl/metrics.py`).
6. **GenAI Features** — LLM provider abstraction (`etl/llm.py`, OpenAI-compatible, Groq default), article summaries, LLM topic labels and themes, AI semantic search with relevance filtering, "ask the news" chat assistant.
7. **Orchestration and Experiment Tracking** — Prefect flows and scheduling (`flows/news_flow.py`, `schedule.py`), MLflow experiment tracking, monitoring.
8. **Backend and Data Exposure** — FastAPI app (`api/main.py`), route modules (articles, search, genai, img, pipeline), data access patterns, security and reliability considerations.
9. **Deployment and DevOps** — Docker Compose service composition (postgres, prefect, mlflow, api, frontend), environment configuration (.env), volumes and persistence, Makefile developer workflow.
10. **Frontend and Data Visualization** — React + Vite dashboard, article exploration, source diversity, sentiment/topic visualizations, floating chat assistant, UX considerations.
11. **Final Conclusion and Future Improvements** — contributions, limitations, future work (more sources, Tunisia map view, model retraining automation).

Front/back matter as in the example: acronyms list, table of contents, list of figures, general introduction page, webography (`webo_*.tex`), English abstract on back cover.

## Figures (~25 total)

- **Tech logos** (chapter 1 stack section + per-chapter choice sections): Python, BeautifulSoup, PostgreSQL, pgvector, FastAPI, Prefect, MLflow, React, Vite, Docker, Hugging Face — downloaded from official sources into `report/img/`.
- **Generated diagrams** (graphviz/mermaid rendered to PNG): high-level architecture, UML use case, class diagram, 3 sequence diagrams, scraping workflow, ETL/ML pipeline flow, database schema graph.
- **Live screenshots**: run `docker-compose up`, capture headlessly with Playwright — frontend dashboard (home, search, chat open), FastAPI `/docs`, Prefect UI flow run, MLflow experiment page. If a service fails to start or has no data, fall back to a labeled placeholder box for that one figure and note it in the final summary.
- **GitHub methodology figures** (chapter 1): screenshot of repo PR list / commit graph.

## Build & verification

- Compile with `latexmk -xelatex` (template is RTL-aware/polyglossia-based; match whatever the example's `main.fls`/log shows was used).
- Zero LaTeX errors; overfull hbox warnings acceptable.
- Verify PDF page count roughly 45–60 pages, TOC/LOF populated, all figures render.

## Out of scope

- French translation.
- Printing/binding specifics.
- Content for features that do not exist in the repo (report describes the codebase as-is).
