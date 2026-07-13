# News Insight Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce `report/` — an ISI-template LaTeX report ("News Insight: An MLOps Platform for Tunisian News Analysis") that compiles to a ~50-page English PDF documenting the news-mlops project.

**Architecture:** Copy the ISI LaTeX template from the PriceRadar example (extracted at `/tmp/claude-1000/-home-ahmedklabi-dev-news-mlops/c0df8714-6f56-43ce-b296-cc1606887cc0/scratchpad/priceradar/Main`), rewrite `global_config.tex` + all content files for news-mlops, generate figures (downloaded logos, mermaid diagrams, live Playwright screenshots), compile with pdflatex inside a texlive Docker container.

**Tech Stack:** LaTeX (ISI `isipfe.cls`, pdflatex via `texlive/texlive` Docker image), mermaid-cli (`minlag/mermaid-cli` Docker image), Playwright (pip) for screenshots, docker-compose for the live stack.

## Global Constraints

- Template files under `report/tpl/` are copied verbatim from the example — never edited (except none; all config goes in `global_config.tex`).
- Report language: English. French abstract stays empty.
- Cover metadata (exact values): title "News Insight: An MLOps Platform for Tunisian News Analysis"; author "Ahmed Klabi"; second "Mariem Smadhi"; third "Hichem Sboui"; fourth empty; `isBinomal` true; diploma "End-of-Semester Project"; speciality "Data Science and AI"; academic supervisor "Sawssen Jalel" (speciality empty); no company; year "2025-2026".
- Compile command (from repo root, used in every compile step):
  `docker run --rm -v "$PWD/report":/work -w /work texlive/texlive latexmk -pdf -interaction=nonstopmode main.tex`
- Success criterion per compile: exit code 0 and `report/main.pdf` regenerated. Overfull hbox warnings acceptable; LaTeX errors are not.
- Report describes the codebase as-is — no invented features.
- Chapter prose is written at execution time from the content briefs below + reading the referenced source files. Briefs list exact section headings and facts; prose itself is the execution deliverable (not duplicated in this plan).
- Commit after every task. Commit messages in normal English (not caveman).

---

### Task 1: Scaffold report/ from template

**Files:**
- Create: `report/tpl/` (copy of example `Main/tpl/`: `isipfe.cls`, `cover_page.tex`, `cover_page_black.tex`, `new_commands.tex`, `resume.tex`, `signatures.tex`)
- Create: `report/main.tex` (copy from example, chapter inputs renamed `chap_01_newsinsight` … `chap_11_newsinsight`, plus `webo_newsinsight`)
- Create: `report/global_config.tex` (rewritten metadata per Global Constraints)
- Create: `report/acronymes.tex`, `report/introduction.tex`, `report/annexes.tex` (copied, content emptied/stubbed)
- Create: `report/chap_01_newsinsight.tex` … `report/chap_11_newsinsight.tex` (stubs: `\chapter{<final title>}` + `\section{Introduction}` placeholder sentence)
- Create: `report/webo_newsinsight.tex` (stub)
- Create: `report/.gitignore` (LaTeX build artifacts: `*.aux *.log *.toc *.lof *.mtc* *.maf *.idx *.ind *.ilg *.bbl *.blg *.fls *.fdb_latexmk *.run.xml *.synctex* main.pdf`)
- Create: `report/img/` (empty, `.gitkeep`)

**Interfaces:**
- Produces: compiling skeleton; chapter file names `chap_NN_newsinsight.tex` used by all later tasks; `report/img/` as figure home.

Chapter titles (exact, used in stubs and later tasks):
1 Introduction · 2 Global Architecture · 3 Data Ingestion and Web Scraping · 4 Storage Layer and Database Design · 5 Machine Learning and NLP Pipeline · 6 GenAI Features · 7 Orchestration and Experiment Tracking · 8 Backend and Data Exposure · 9 Deployment and DevOps · 10 Frontend and Data Visualization · 11 Final Conclusion and Future Improvements

- [ ] **Step 1:** Copy template: `mkdir -p report && cp -r <example>/Main/tpl report/ && cp <example>/Main/{main.tex,acronymes.tex,introduction.tex,annexes.tex,global_config.tex,biblio.bib,main-blx.bib} report/`. Delete nothing else (build artifacts never copied).
- [ ] **Step 2:** Rewrite `report/global_config.tex` cover section with News Insight metadata (Global Constraints values). English abstract: 2 paragraphs — (1) News Insight scrapes Tunisian news sources, stores them in PostgreSQL+pgvector, and analyses them with embeddings, sentiment and BERTopic topics; (2) GenAI layer (summaries, ask-the-news chat, LLM topic labels) + MLOps stack (Prefect, MLflow, FastAPI, React, Docker). Keywords: `News Analysis, MLOps, Web Scraping, NLP, BERTopic, Sentence Transformers, pgvector, FastAPI, Prefect, MLflow, GenAI, RAG`.
- [ ] **Step 3:** Edit `report/main.tex`: replace the ten `\input{chap_NN_priceradar}` lines with eleven `\input{chap_NN_newsinsight}` lines and `\input{webo_priceradar}` → `\input{webo_newsinsight}`.
- [ ] **Step 4:** Create 11 chapter stubs + `webo_newsinsight.tex` stub + empty `acronymes.tex` body + `introduction.tex` (General Introduction stub) + `.gitignore` + `img/.gitkeep`.
- [ ] **Step 5:** Compile (Global Constraints command). Expected: exit 0, `report/main.pdf` with cover page showing News Insight metadata + 11 stub chapters. First run pulls `texlive/texlive` image (~2 GB, one-time).
- [ ] **Step 6:** Commit: `git add report && git commit -m "report: scaffold News Insight report from ISI template"`

### Task 2: Tech logos

**Files:**
- Create: `report/img/{python,beautifulsoup,postgresql,pgvector,fastapi,prefect,mlflow,react,vite,docker,huggingface}.png`

**Interfaces:**
- Produces: logo PNGs referenced by chapters 1, 3–10 technology-choice sections.

- [ ] **Step 1:** Download each logo with `curl -L -o report/img/<name>.png <url>` from Wikimedia Commons / official press kits (search per logo; prefer PNG ≥200px on transparent or white background). Any logo that can't be fetched: render text fallback later, note it.
- [ ] **Step 2:** Verify: `file report/img/*.png` — all report PNG image data; open-check sizes reasonable (no 404 HTML saved as .png).
- [ ] **Step 3:** Commit: `git commit -m "report: add technology logos"`

### Task 3: Diagrams (mermaid → PNG)

**Files:**
- Create: `report/diagrams/*.mmd` (sources), `report/img/*.png` (rendered), `report/diagrams/render.sh`

**Interfaces:**
- Produces (PNG names, referenced by chapters): `arch-highlevel` (ch2), `usecase` (ch2), `classes` (ch2), `seq-pipeline` (ch2), `seq-aisearch` (ch2), `seq-chat` (ch2), `scrape-flow` (ch3), `db-schema` (ch4), `ml-pipeline` (ch5), `prefect-flow` (ch7).

- [ ] **Step 1:** Write `render.sh`: loops `*.mmd`, runs `docker run --rm -u $(id -u) -v "$PWD":/data minlag/mermaid-cli -i /data/<f>.mmd -o /data/../img/<f>.png -w 1600 -b white`.
- [ ] **Step 2:** Author 10 `.mmd` sources grounded in the code (read first: `db/schema.sql`, `db/migrations/*.sql`, `etl/pipeline.py`, `flows/news_flow.py`, `api/routes/*.py`, `scrapers/*.py`):
  - `arch-highlevel.mmd` — flowchart LR: sources (Kapitalis, RSS) → scrapers → Postgres+pgvector → ETL (embeddings/sentiment/BERTopic/LLM) → FastAPI → React; Prefect orchestrates ETL; MLflow tracks; LLM provider external.
  - `usecase.mmd` — flowchart: actors Visitor + Operator; use cases browse articles, semantic search, ask-the-news chat, view topics/themes, trigger pipeline, monitor runs.
  - `classes.mmd` — classDiagram from actual DB schema: Article, Topic/Theme, Region, Summary + key fields/relations.
  - `seq-pipeline.mmd`, `seq-aisearch.mmd`, `seq-chat.mmd` — sequenceDiagram, participants matching real modules/routes.
  - `scrape-flow.mmd`, `db-schema.mmd` (erDiagram), `ml-pipeline.mmd`, `prefect-flow.mmd`.
- [ ] **Step 3:** Run `bash report/diagrams/render.sh`. Expected: 10 PNGs in `report/img/`, each non-empty. Fix mermaid syntax errors until clean.
- [ ] **Step 4:** Commit: `git commit -m "report: add generated architecture and UML diagrams"`

### Task 4: Live screenshots

**Files:**
- Create: `report/screenshots.py` (Playwright capture script)
- Create: `report/img/{screen-dashboard,screen-search,screen-chat,screen-apidocs,screen-prefect,screen-mlflow}.png`

**Interfaces:**
- Consumes: running docker-compose stack (`.env` must exist — copy `.env.example` if missing; LLM key may be absent → chat screenshot falls back).
- Produces: 6 screenshot PNGs (ch 1/7/8/10). Any capture that fails → skip, use `\fbox` placeholder in the chapter and record in final summary.

- [ ] **Step 1:** `pip install playwright && python -m playwright install chromium`
- [ ] **Step 2:** Ensure `.env` exists; `docker-compose up -d --build`; wait for health: `curl -sf localhost:8000/docs`, `curl -sf localhost:5173`, `curl -sf localhost:4200`, `curl -sf localhost:5000`. If DB empty, seed: `make scrape PAGES=2 && make transform && make cluster` (or docker equivalents) so UI shows data.
- [ ] **Step 3:** Write `report/screenshots.py`: sync Playwright, viewport 1600×900, `page.goto` each URL (`:5173` home; `:5173` after typing query in search; `:5173` with chat widget opened via click; `:8000/docs`; `:4200` runs page; `:5000` experiments), `page.screenshot(path=...)` full page where sensible.
- [ ] **Step 4:** Run script; verify 6 PNGs look right (Read each image). Re-run individual captures as needed.
- [ ] **Step 5:** `docker-compose down` (leave volumes). Commit: `git commit -m "report: add live application screenshots"`

### Task 5: Chapter 1 — Introduction

**Files:**
- Modify: `report/chap_01_newsinsight.tex`
- Modify: `report/introduction.tex` (General Introduction, 1 page)

**Interfaces:**
- Consumes: logos (Task 2). Produces: nothing downstream.

Sections (exact): Introduction · Project context · Problem statement · Objectives · Work methodology · Technology stack overview · Conclusion.

- [ ] **Step 1:** Read `README.md`, `git log --oneline`, memory file `news-hub-roadmap` context if present. Write chapter (~5 pages): Tunisian news fragmentation/French-Arabic mix as context; problem = no unified analytical view; objectives = automated collection, NLP enrichment, GenAI access, reproducible MLOps; methodology = agile via GitHub flow — cite real branch/PR names from `git log` (e.g. `fix/ai-search-precision`, `feat/ai-search-themes-diversity`), include figure `screen-github` OPTIONAL: capture `github.com/ahmedkltn/news-mlops` PR list via Playwright if reachable, else skip figure; stack overview = logo grid figure (logos from Task 2, `subfigure`/tabular layout like example's chapter 1).
- [ ] **Step 2:** Write `introduction.tex` General Introduction (1 page, unnumbered `\chapter*`): motivation → report roadmap paragraph.
- [ ] **Step 3:** Compile; fix errors. **Step 4:** Commit `"report: write chapter 1 (introduction)"`.

### Task 6: Chapter 2 — Global Architecture

**Files:** Modify `report/chap_02_newsinsight.tex`

Sections: Introduction · High-level architecture · Actors and use cases · Domain model · Key scenarios (3 sequence diagrams) · Conclusion.

- [ ] **Step 1:** Write chapter (~6 pages) around figures `arch-highlevel`, `usecase`, `classes`, `seq-pipeline`, `seq-aisearch`, `seq-chat`; prose explains each layer boundary + data flow, matching diagram content.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 2 (global architecture)"`.

### Task 7: Chapter 3 — Data Ingestion and Web Scraping

**Files:** Modify `report/chap_03_newsinsight.tex`

Sections: Introduction · Scraping technology choice · Scraper architecture · Kapitalis scraper · RSS ingestion · Deduplication and raw storage · Error handling · Conclusion.

- [ ] **Step 1:** Read `scrapers/base.py`, `scrapers/kapitalis.py`, `scrapers/rss.py`, `etl/extract.py`, `scripts/scrape.py` (if exists). Write chapter (~5 pages): BeautifulSoup-vs-Playwright/Scrapy choice rationale; base-class contract (actual method names); pagination + article parsing specifics; RSS feed handling; URL-hash/unique-constraint dedup (state what schema actually enforces); figure `scrape-flow`; 1–2 short real code excerpts (`lstlisting`/`minted` — match example's listing style).
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 3 (data ingestion and web scraping)"`.

### Task 8: Chapter 4 — Storage Layer and Database Design

**Files:** Modify `report/chap_04_newsinsight.tex`

Sections: Introduction · Database technology choice · Schema design · Vector storage with pgvector · Migrations · Conclusion.

- [ ] **Step 1:** Read `db/schema.sql`, `db/migrations/001_news_hub.sql`, `db/migrations/002_region.sql`. Write chapter (~5 pages): Postgres+pgvector vs dedicated vector DB rationale; real tables/columns/indexes; embedding column dims + distance operator actually used (check `api/routes/search.py` / `etl/load.py`); region migration; figure `db-schema`.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 4 (storage layer and database design)"`.

### Task 9: Chapter 5 — Machine Learning and NLP Pipeline

**Files:** Modify `report/chap_05_newsinsight.tex`

Sections: Introduction · Pipeline overview · Text embeddings · Sentiment analysis · Topic modeling with BERTopic · Enrichment: themes, labels and regions · Pipeline metrics · Conclusion.

- [ ] **Step 1:** Read `etl/transform.py`, `etl/cluster.py`, `etl/themes.py`, `etl/labels.py`, `etl/regions.py`, `etl/metrics.py`, `etl/pipeline.py`. Write chapter (~6 pages): exact model names (sentence-transformers model id, cardiffnlp model id) from code; BERTopic config (min cluster size etc. from code/Makefile `MIN_CLUSTER`); how themes/labels/regions computed; metrics tracked; figure `ml-pipeline`.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 5 (machine learning and NLP pipeline)"`.

### Task 10: Chapter 6 — GenAI Features

**Files:** Modify `report/chap_06_newsinsight.tex`

Sections: Introduction · LLM provider abstraction · Article summaries · LLM topic labels and themes · AI semantic search · Ask-the-news chat assistant · Cost and reliability considerations · Conclusion.

- [ ] **Step 1:** Read `etl/llm.py`, `api/routes/genai.py`, `api/routes/search.py`, relevant frontend chat component. Write chapter (~5 pages): OpenAI-compatible abstraction (env vars `LLM_API_KEY/BASE_URL/MODEL`, Groq default); summary generation flow incl. thin-content fix (commit b8959a4); search precision fix — relevance filtering instead of padding to limit (commit 9da5a05); RAG pattern of chat; figures `screen-chat`, `screen-search`.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 6 (GenAI features)"`.

### Task 11: Chapter 7 — Orchestration and Experiment Tracking

**Files:** Modify `report/chap_07_newsinsight.tex`

Sections: Introduction · Orchestration technology choice · Flow design · Scheduling · Experiment tracking with MLflow · Monitoring and reliability · Conclusion.

- [ ] **Step 1:** Read `flows/news_flow.py`, `flows/schedule.py`, MLflow usage in `etl/*`. Write chapter (~4 pages): Prefect-vs-Airflow rationale (lightweight, pythonic); real task/flow names; schedule cadence from code; what params/metrics logged to MLflow; figures `prefect-flow`, `screen-prefect`, `screen-mlflow`.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 7 (orchestration and experiment tracking)"`.

### Task 12: Chapter 8 — Backend and Data Exposure

**Files:** Modify `report/chap_08_newsinsight.tex`

Sections: Introduction · Backend technology choice · API structure · Endpoints · Data access patterns · Security and reliability considerations · Conclusion.

- [ ] **Step 1:** Read `api/main.py`, all `api/routes/*.py`. Write chapter (~4 pages): FastAPI choice; router-per-domain layout; endpoint table (real paths/methods from code: articles, search, genai, img, pipeline); CORS/env handling; figure `screen-apidocs`.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 8 (backend and data exposure)"`.

### Task 13: Chapter 9 — Deployment and DevOps

**Files:** Modify `report/chap_09_newsinsight.tex`

Sections: Introduction · Containerization strategy · Service composition · Environment configuration · Data persistence · Developer workflow · Conclusion.

- [ ] **Step 1:** Read `docker-compose.yml`, `Makefile`, `.env.example`, any Dockerfiles. Write chapter (~4 pages): real service list + ports; env var table; volumes; Makefile step-by-step workflow (scrape→transform→cluster→api→frontend); docker logo figure optional.
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 9 (deployment and devops)"`.

### Task 14: Chapter 10 — Frontend and Data Visualization

**Files:** Modify `report/chap_10_newsinsight.tex`

Sections: Introduction · Frontend technology choice · Application structure · Article exploration and search UX · Visualizations and source diversity · Floating chat assistant · Conclusion.

- [ ] **Step 1:** Read `frontend/src` structure (pages/components, main App). Write chapter (~4 pages): React+Vite choice; component map; search/diversity UX (commit 0450d23 features); figures `screen-dashboard`, `screen-search` (if not used in ch6 — each screenshot used exactly once; ch6 keeps `screen-chat`, ch10 gets `screen-dashboard` + `screen-search`; adjust ch6 step accordingly at execution).
- [ ] **Step 2:** Compile. **Step 3:** Commit `"report: write chapter 10 (frontend and data visualization)"`.

### Task 15: Chapter 11 + front/back matter

**Files:** Modify `report/chap_11_newsinsight.tex`, `report/acronymes.tex`, `report/webo_newsinsight.tex`, `report/annexes.tex`

- [ ] **Step 1:** Chapter 11 (~3 pages), sections: Final conclusion · Project contributions · Future improvements · Closing remarks. Future work: more sources beyond Kapitalis, Tunisia per-governorate map (spec exists in memory), automated retraining, Arabic-dialect sentiment model, alerting.
- [ ] **Step 2:** `acronymes.tex`: real acronyms used (API, ETL, LLM, MLOps, NLP, ORM, RAG, REST, RSS, SQL, UI, UML, UX, JSON, HTTP, CORS…), template's list format.
- [ ] **Step 3:** `webo_newsinsight.tex`: webography entries mirroring example format — official docs URLs (FastAPI, Prefect, MLflow, BERTopic, sentence-transformers, pgvector, React, Vite, Docker, Groq).
- [ ] **Step 4:** `annexes.tex`: keep minimal or drop from main.tex if example leaves it out of final PDF — mirror example behavior.
- [ ] **Step 5:** Compile. **Step 6:** Commit `"report: write conclusion, acronyms and webography"`.

### Task 16: Final verification pass

**Files:** Create `report/README.md`

- [ ] **Step 1:** Full clean compile ×2 (TOC/LOF need two passes; latexmk handles reruns). Expected: exit 0.
- [ ] **Step 2:** Verify PDF: page count 45–60 (`docker run --rm -v "$PWD/report":/work -w /work texlive/texlive pdfinfo main.pdf` or `qpdf --show-npages`); TOC lists 11 chapters; LOF populated; spot-Read rendered pages (cover, one figure-heavy page) as images if convertible, else visually via user.
- [ ] **Step 3:** Grep sources for leftovers: `grep -ri "priceradar\|TODO\|TBD\|PLACEHOLDER" report/*.tex` → only intentional hits (none expected outside placeholder fboxes noted in Task 4).
- [ ] **Step 4:** Write `report/README.md`: build command, prerequisites (docker), figure regeneration (`diagrams/render.sh`, `screenshots.py`).
- [ ] **Step 5:** Commit `"report: final verification and build docs"`. Send user `report/main.pdf` + summary of any placeholder figures.
