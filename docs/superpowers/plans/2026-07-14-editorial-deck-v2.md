# Editorial Defense Deck v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `presentation/index-v2.html` — a 15-slide, newspaper-styled defense deck with real evidence — and export `presentation/News-Insight-slides-v2.pdf`.

**Architecture:** One self-contained HTML file with a `show(n)` slide mechanism (same as the old deck), rendered and verified slide-by-slide with Playwright at 1400×820, exported to PDF per-slide and merged. Evidence (numbers, screenshots) is gathered first so no slide ever contains an invented value.

**Tech Stack:** HTML/CSS (no framework), Playwright (Python, in `.venv`), pypdf for merge, PostgreSQL queries via `docker exec news_postgres`, MLflow REST (`:5000`), Prefect REST/UI (`:4200`).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-14-editorial-deck-design.md` — re-read before starting.
- Old deck files (`presentation/index.html`, `News-Insight-slides.pdf`) must not be modified or deleted.
- Every number on a slide comes from Task 1's facts file or a Task 2/3 capture. No invented stats.
- Banned visuals: gradients, drop shadows, emojis, rounded SaaS cards, logo walls, decorative blobs.
- Paper `#faf9f7`, ink `#1a1a1a`, one red accent (exact hex captured in Task 1 as `--red`).
- Headlines: Playfair Display with Georgia fallback (serif); body: system sans; code/ports/SQL: monospace.
- Every slide: double-rule masthead, red small-caps kicker, serif assertion headline, folio footer `News Insight · Soutenance · N / 15`.
- Deck language: English. Product UI is French — note this once on the first product slide (slide 4).
- Work on branch `feat/deck-v2`.
- All scratch scripts go in the session scratchpad directory, NOT in the repo (except nothing — no scripts belong in the repo for this plan).

---

### Task 1: Facts pack (no invented numbers)

**Files:**
- Create: `<scratchpad>/facts.md` (scratchpad = session scratchpad directory)

**Interfaces:**
- Produces: `facts.md` with sections BRAND, CORPUS, SOURCES, TESTS, TRIGGER. Tasks 4–7 read slide content values ONLY from this file.

- [ ] **Step 1: Capture the Tuniscope red**

```bash
grep -rhoE '#[e-fE-F][0-9a-fA-F]{5}|#d9[0-9a-fA-F]{4}|--(red|accent|primary)[^;]*' /home/ahmedklabi/dev/news-mlops/frontend/src --include='*.css' --include='*.tsx' -r | sort | uniq -c | sort -rn | head -15
```

Pick the red used for the Tuniscope wordmark/nav accent (verify against `presentation/img/shot-home.png` visually). Record as `BRAND: --red: #xxxxxx`.

- [ ] **Step 2: Query corpus stats**

```bash
docker exec news_postgres psql -U news_user -d news_db -P pager=off \
  -c "SELECT COUNT(*) articles, MIN(published_at)::date oldest, MAX(published_at)::date newest FROM articles;" \
  -c "SELECT source, COUNT(*) FROM articles GROUP BY 1 ORDER BY 2 DESC;" \
  -c "SELECT sentiment, COUNT(*), ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),0) pct FROM articles GROUP BY 1 ORDER BY 2 DESC;" \
  -c "SELECT COUNT(DISTINCT topic_id) topics FROM articles WHERE topic_id IS NOT NULL;" \
  -c "SELECT COUNT(DISTINCT region) regions FROM articles WHERE region IS NOT NULL;" \
  -c "SELECT topic_label, COUNT(*) FROM articles WHERE topic_label IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 6;"
```

Record all outputs under CORPUS.

- [ ] **Step 3: Inventory scrapers and stack**

```bash
ls /home/ahmedklabi/dev/news-mlops/scrapers/
grep -E 'container_name|ports' /home/ahmedklabi/dev/news-mlops/docker-compose.yml
cd /home/ahmedklabi/dev/news-mlops && .venv/bin/python -m pytest --collect-only -q 2>/dev/null | tail -3
```

Record scraper module names under SOURCES, container names + host ports and test count under TESTS.

- [ ] **Step 4: Find the pipeline HTTP trigger**

```bash
grep -rn "router\|@app\|post\|run" /home/ahmedklabi/dev/news-mlops/api/routers/pipeline*.py | head -20
```

Record the exact method + path (e.g. `POST http://localhost:8001/pipeline/run`) under TRIGGER. Confirm the API host port from docker-compose output in Step 3.

- [ ] **Step 5: Write `facts.md` and verify completeness**

Write all recorded values into `<scratchpad>/facts.md` with the five section headers. Verify: every section non-empty; sentiment percentages sum to ~100; source count noted (expected: 3 of 4 scrapers have rows — record actual).

---

### Task 2: Trigger one real pipeline run

**Files:**
- Modify: none (runtime state only: `pipeline_metrics` row, MLflow run, Prefect flow run)

**Interfaces:**
- Consumes: TRIGGER endpoint from `facts.md`.
- Produces: ≥1 row in `pipeline_metrics`; ≥1 fresh MLflow run; ≥1 completed Prefect flow run. Appends section RUN to `facts.md` (metrics row values, MLflow run_id + experiment id, Prefect flow_run id).

- [ ] **Step 1: Trigger**

```bash
curl -s -X POST <TRIGGER-URL-from-facts> | head -5
```

Expected: JSON ack (flow run id or status). If the endpoint differs, re-check Task 1 Step 4 output.

- [ ] **Step 2: Wait and verify metrics row**

Poll (pipeline scrapes 4 sites + runs models; allow up to ~10 min):

```bash
docker exec news_postgres psql -U news_user -d news_db -P pager=off \
  -c "SELECT * FROM pipeline_metrics ORDER BY id DESC LIMIT 2;"
```

Expected: ≥1 row with `articles_new`, `n_topics`, `outlier_pct`, sentiment counts. Record the row in `facts.md` under RUN.

- [ ] **Step 3: Get MLflow + Prefect run ids**

```bash
curl -s "http://localhost:5000/api/2.0/mlflow/runs/search" -H 'Content-Type: application/json' \
  -d '{"experiment_ids":["0","1"],"max_results":3,"order_by":["attributes.start_time DESC"]}' | head -c 1500
curl -s -X POST "http://localhost:4200/api/flow_runs/filter" -H 'Content-Type: application/json' \
  -d '{"limit":3,"sort":"START_TIME_DESC"}' | head -c 1500
```

Record MLflow `run_id` + experiment id and Prefect flow-run `id` + state (`COMPLETED`) in `facts.md`. If the pipeline failed, stop and report — do not fake it.

---

### Task 3: Capture MLflow and Prefect screenshots

**Files:**
- Create: `presentation/img/shot-mlflow.png`, `presentation/img/shot-prefect.png`
- Create: `<scratchpad>/capture.py`

**Interfaces:**
- Consumes: run ids from `facts.md` RUN section.
- Produces: the two PNGs, referenced by slides 10 and 11 as `img/shot-mlflow.png` and `img/shot-prefect.png`.

- [ ] **Step 1: Write `<scratchpad>/capture.py`**

```python
import sys
from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 900}, device_scale_factor=2)
    pg.goto(url, wait_until="networkidle")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=out)
    b.close()
print("saved", out)
```

- [ ] **Step 2: Capture both UIs**

```bash
cd /home/ahmedklabi/dev/news-mlops
.venv/bin/python <scratchpad>/capture.py "http://localhost:5000/#/experiments/<EID>/runs/<RUN_ID>" presentation/img/shot-mlflow.png
.venv/bin/python <scratchpad>/capture.py "http://localhost:4200/flow-runs/flow-run/<FLOW_RUN_ID>" presentation/img/shot-prefect.png
```

- [ ] **Step 3: Verify visually**

Read both PNGs. MLflow shot must show run params/metrics; Prefect shot must show a green/COMPLETED run timeline. If a page rendered empty, increase the timeout to 4000 ms and retry.

- [ ] **Step 4: Commit**

```bash
git add presentation/img/shot-mlflow.png presentation/img/shot-prefect.png
git commit -m "presentation: capture real MLflow and Prefect run screenshots"
```

---

### Task 4: Deck skeleton — design system + slides 1 and 15

**Files:**
- Create: `presentation/index-v2.html`
- Create: `<scratchpad>/shot.py`

**Interfaces:**
- Consumes: `--red` from `facts.md`.
- Produces: `index-v2.html` with the full CSS system and global `show(n)` JS; `shot.py <n> <out.png>` renders slide n. All later tasks add `<section class="slide">` blocks and use these class names verbatim: `mast`, `kicker`, `assert`, `cols`, `why`, `fig`, `figcap`, `stats`, `stat`, `press`, `node`, `gloss`, `arr`, `code`, `folio`, `divider-dark`.

- [ ] **Step 1: Check the old deck's show() mechanism**

```bash
grep -n "function show" /home/ahmedklabi/dev/news-mlops/presentation/index.html
```

Match its signature in the new file (so the old export tooling pattern still applies).

- [ ] **Step 2: Write the skeleton**

`presentation/index-v2.html` — full design system, slide 1 (title) and slide 15 (thanks) only:

```html
<!doctype html><html><head><meta charset="utf-8"><title>News Insight — soutenance v2</title>
<style>
:root{ --red:#E02B2B; /* replace with facts.md BRAND value */
  --paper:#faf9f7; --ink:#1a1a1a; --mut:#6d675e; --rule:#d8d4cc; --hair:#c9c5bd; }
*{margin:0;padding:0;box-sizing:border-box}
body{background:#333;font-family:'Segoe UI',system-ui,sans-serif;color:var(--ink)}
.slide{width:1400px;height:820px;background:var(--paper);padding:48px 72px 64px;
  position:relative;display:none;flex-direction:column}
.slide.active{display:flex}
.serif{font-family:'Playfair Display',Georgia,'Times New Roman',serif}
.mono{font-family:'JetBrains Mono','Cascadia Code',Consolas,monospace}
/* masthead */
.mast{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:3px double var(--ink);padding-bottom:10px}
.mast .brand{font-family:Georgia,serif;font-weight:700;font-size:21px}
.mast .brand i{color:var(--red);font-style:normal}
.mast .ed{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--mut)}
/* headline block */
.kicker{font-size:12.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  color:var(--red);margin:24px 0 6px}
.assert{font-family:'Playfair Display',Georgia,serif;font-size:42px;line-height:1.12;
  font-weight:700;max-width:1120px;margin-bottom:22px}
/* layout */
.cols{display:grid;grid-template-columns:1fr 340px;gap:40px;flex:1;min-height:0}
.why{border-left:2px solid var(--red);padding:2px 0 2px 16px;font-size:15px;
  line-height:1.5;color:#3a372f;margin-top:8px}
.why b{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--red)}
/* figures */
.fig{border:1px solid var(--hair);background:#fff;padding:10px}
.fig img{width:100%;display:block}
.figcap{font-size:13px;color:#3a372f;margin-top:9px;line-height:1.45}
.figcap b{font-size:11.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink)}
.figcap i{color:var(--mut)}
/* stat strip */
.stats{display:flex;border-top:3px double var(--ink);border-bottom:3px double var(--ink)}
.stat{flex:1;padding:16px 18px;border-right:1px solid var(--rule)}
.stat:last-child{border-right:none}
.stat .n{font-family:Georgia,serif;font-size:38px;font-weight:700}
.stat .n i{font-style:normal;color:var(--red)}
.stat .l{font-size:11.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--mut);margin-top:2px}
/* press table */
.press{width:100%;border-collapse:collapse;font-size:15px;line-height:1.4}
.press th{font-size:11.5px;letter-spacing:.13em;text-transform:uppercase;text-align:left;
  color:var(--red);border-bottom:2px solid var(--ink);padding:0 14px 8px 0}
.press td{border-bottom:1px solid var(--rule);padding:10px 14px 10px 0;vertical-align:top}
/* diagram atoms */
.node{border:1.5px solid var(--ink);background:#fff;padding:10px 14px;text-align:center}
.node b{font-size:16px}
.gloss{font-size:12.5px;color:var(--mut)}
.arr{color:var(--red);font-family:Consolas,monospace;font-size:12.5px;font-weight:700;
  text-align:center;align-self:center}
.code{font-family:Consolas,monospace;font-size:13.5px;background:#f0ede7;padding:2px 7px}
/* folio */
.folio{position:absolute;left:72px;right:72px;bottom:20px;display:flex;
  justify-content:space-between;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--mut);border-top:1px solid var(--rule);padding-top:9px}
/* dark back page (slides 1 uses paper; 15 uses ink) */
.divider-dark{background:var(--ink);color:var(--paper)}
.divider-dark .mast{border-bottom-color:var(--paper)}
.divider-dark .folio{color:#a49e93;border-top-color:#4a463f}
</style></head><body>
<!-- SLIDE 1 · TITLE -->
<section class="slide" id="s1">
  <div class="mast"><span class="brand">Tuni<i>scope</i> <i>●</i></span>
    <span class="ed">TEK-UP University · Data Science &amp; AI · 2025–2026</span></div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center">
    <div class="kicker">End-of-semester project · MLOps · Soutenance edition</div>
    <div class="serif" style="font-size:88px;font-weight:700;line-height:1.02">News Insight</div>
    <div class="serif" style="font-size:26px;font-style:italic;color:#3a372f;margin-top:14px">
      An MLOps platform that collects, understands and serves Tunisian news.</div>
    <div style="display:flex;gap:64px;margin-top:44px;font-size:16px">
      <div><div class="kicker" style="margin:0 0 6px">Prepared by</div>
        Ahmed Klabi · Mariem Smadhi · Hichem Sboui</div>
      <div><div class="kicker" style="margin:0 0 6px">Supervisor</div>Sawssen Jalel</div>
    </div>
  </div>
  <div class="stats" style="margin-bottom:26px">
    <div class="stat"><div class="l" style="margin:0">In this edition</div></div>
    <div class="stat"><div class="l" style="margin:0">1 · The problem &amp; the product</div></div>
    <div class="stat"><div class="l" style="margin:0">2 · Architecture &amp; models</div></div>
    <div class="stat"><div class="l" style="margin:0">3 · Operations &amp; monitoring</div></div>
    <div class="stat"><div class="l" style="margin:0">4 · Contributions</div></div>
  </div>
  <div class="folio"><span>News Insight · Soutenance</span><span>1 / 15</span></div>
</section>
<!-- SLIDE 15 · THANKS -->
<section class="slide divider-dark" id="s15">
  <div class="mast"><span class="brand" style="color:var(--paper)">Tuni<i>scope</i> <i>●</i></span>
    <span class="ed" style="color:#a49e93">Back page</span></div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">
    <div class="serif" style="font-size:76px;font-weight:700">Thank you.</div>
    <div class="serif" style="font-size:24px;font-style:italic;color:#c9c4ba;margin-top:16px">
      Questions &amp; discussion — the stack is running, ask for any live view.</div>
  </div>
  <div class="folio"><span>News Insight · Soutenance</span><span>15 / 15</span></div>
</section>
<script>
function show(n){document.querySelectorAll('.slide').forEach(function(s,i){
  s.classList.toggle('active', i===n-1);});}
show(1);
document.addEventListener('keydown',function(e){
  var a=[].indexOf.call(document.querySelectorAll('.slide'),document.querySelector('.slide.active'))+1;
  if(e.key==='ArrowRight')show(Math.min(a+1,document.querySelectorAll('.slide').length));
  if(e.key==='ArrowLeft')show(Math.max(a-1,1));});
</script></body></html>
```

Set `--red` to the facts.md value. Adjust `show()` to match the old deck's signature if it differs (Step 1).

- [ ] **Step 3: Write `<scratchpad>/shot.py`**

```python
import sys, pathlib
from playwright.sync_api import sync_playwright

n, out = int(sys.argv[1]), sys.argv[2]
url = pathlib.Path("/home/ahmedklabi/dev/news-mlops/presentation/index-v2.html").as_uri()
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 820})
    pg.goto(url)
    pg.evaluate(f"show({n})")
    pg.wait_for_timeout(300)
    pg.screenshot(path=out)
    b.close()
print("saved", out)
```

- [ ] **Step 4: Render slides 1 and 15, verify**

```bash
cd /home/ahmedklabi/dev/news-mlops
.venv/bin/python <scratchpad>/shot.py 1 <scratchpad>/r1.png
.venv/bin/python <scratchpad>/shot.py 2 <scratchpad>/r15.png   # slide 15 is 2nd section until middles exist
```

Read both renders. Check: masthead double rule, serif title, no overflow, folio visible. Note: shot.py's `show(n)` indexes DOM order — while only 2 sections exist, slide 15 is n=2. Re-render after later tasks insert slides.

- [ ] **Step 5: Commit**

```bash
git add presentation/index-v2.html
git commit -m "presentation: deck v2 skeleton — editorial design system, title and back page"
```

---

### Task 5: Slides 2–6 (problem, platform, product tour)

**Files:**
- Modify: `presentation/index-v2.html` (insert `<section id="s2">…<section id="s6">` between s1 and s15)

**Interfaces:**
- Consumes: class system from Task 4; CORPUS/SOURCES numbers from `facts.md`; existing `img/shot-home.png`, `shot-dashboard.png`, `shot-map.png`, `shot-search.png`, `shot-chat.png`.
- Produces: slides 2–6 finished.

Slide content (headlines verbatim; numbers = placeholders here, substitute facts.md values marked `«»`):

| # | Kicker | Assertion headline | Evidence | WHY margin note |
|---|---|---|---|---|
| 2 | PART 1 · THE PROBLEM | Tunisian news is scattered across sites — unsearchable, unmeasured. | Press table: the 4 real sources (name, language, format RSS/HTML) from facts.md | Readers and analysts must visit each site by hand; nothing offers search by meaning, an overall mood, or a regional view. |
| 3 | PART 1 · THE ANSWER | One pipeline: collect the news, understand it, serve it. | Stat strip: «60» articles · 4 scrapers · 5 models · «24» governorates mapped · 1 `docker-compose up`; under it a 3-node flow Collect → Understand → Explore with labeled red arrows | Built as an MLOps platform: the loop runs on a schedule, unattended, and every run is logged. |
| 4 | PART 1 · THE PRODUCT | Every source lands in one feed, tagged by topic and mood. | `img/shot-home.png` as Fig. 1, full-width | UI is French for a Tunisian audience. Each card: source · theme · sentiment — the pipeline's output, visible. |
| 5 | PART 1 · THE PRODUCT | Sentiment, themes and geography — measured, not guessed. | Two figs side by side: `shot-dashboard.png` (Fig. 2), `shot-map.png` (Fig. 3) | Current corpus: «45%» negative / «28%» neutral / «27%» positive over «60» articles; map shades all 24 governorates by volume or mood. |
| 6 | PART 1 · THE PRODUCT | Search works by meaning; the assistant answers only from real articles. | Two figs: `shot-search.png` (Fig. 4), `shot-chat.png` (Fig. 5) | "football" finds transfer news that never says "football". The assistant cites numbered sources — mechanics on slide 12. |

- [ ] **Step 1: Write slides 2–6** using only Task 4 classes. Figures follow the `fig`/`figcap` pattern: `<b>Fig. 1</b> — caption. <i>italic gloss.</i>`
- [ ] **Step 2: Render each** (`shot.py` n=2..6 after insertion) and read every render. Check: no overflow, images load (file paths are relative: `img/...`), headlines fit on ≤2 lines.
- [ ] **Step 3: Fix any overflow** (reduce img max-height via inline style, or shorten gloss) and re-render.
- [ ] **Step 4: Commit**

```bash
git add presentation/index-v2.html
git commit -m "presentation: deck v2 slides 2-6 — problem, platform, product tour"
```

---

### Task 6: Slides 7–11 (architecture, collection, models, topics, operations)

**Files:**
- Modify: `presentation/index-v2.html`

**Interfaces:**
- Consumes: Task 4 classes; facts.md CORPUS/SOURCES/RUN; `img/shot-mlflow.png`, `img/shot-prefect.png` from Task 3.
- Produces: slides 7–11 finished.

| # | Kicker | Assertion headline | Evidence | WHY margin note |
|---|---|---|---|---|
| 7 | PART 2 · ARCHITECTURE | From live sites to one database to one app — every layer replaceable. | Full-width layered diagram (`node`/`arr`/`gloss` atoms): Sources («4» scrapers) → `Prefect · scrape → transform → load` → PostgreSQL + pgvector (`one articles table · text + vector(384)`) → Enrichment row (Embeddings e5-small · Sentiment XLM-R · Theme LLM · Region gazetteer · GenAI Groq) → FastAPI → React+Vite. Every arrow labeled. | One table, not a warehouse: enrichment is UPDATE-in-place columns. pgvector over a vector DB: SQL joins + `cosine <=>` index, one fewer service to operate. |
| 8 | PART 2 · COLLECTION | Collection survives messy sources: RSS, an HTML fallback, idempotent writes. | Flow: RSS ×3 + Kapitalis HTML deep-crawl → Dedup `ON CONFLICT (url) DO NOTHING` → articles. Under it, honest ops table from facts.md: per-source article counts in current window | Feeds fail in the wild — in the current window «3 of 4» sources delivered. `ON CONFLICT` makes re-runs safe: the daily cron can never duplicate an article. |
| 9 | PART 2 · MODELS | Four models enrich every article — each chosen for a reason. | Press table: Model / Task / Output / Why this one — e5-small → embedding → `vector(384)` → multilingual FR-AR, CPU-cheap; XLM-RoBERTa → sentiment → pos·neu·neg → trained on 100+ langs incl. Arabic; Groq LLM → theme → 1 of 10 fixed → fixed label space keeps charts comparable across runs; gazetteer + LLM → region → governorate → place names beat NER on short news briefs | Each model writes one column back to `articles` — enrichment is inspectable with plain SQL. |
| 10 | PART 2 · TOPICS | BERTopic finds the topics; MLflow keeps the receipts. | Left: 3-node flow BERTopic clusters embeddings → LLM names each cluster → write `topic_id`,`topic_label`; Right: `img/shot-mlflow.png` as Fig. 6 (real run: params + metrics) | Topics are *discovered*, not predefined — «9» topics in the current corpus, «N%» outliers. Every clustering run logs params, metrics and the model to MLflow: reproducible. |
| 11 | PART 3 · OPERATIONS | Prefect runs it every morning — and every run leaves a metrics row. | Left: `img/shot-prefect.png` as Fig. 7 (real COMPLETED run); Right: chips `cron 06:00 Africa/Tunis` · `HTTP trigger` · `retries 2× / 60s` + the real `pipeline_metrics` row from facts.md RUN rendered as a mono table | Monitoring = one row per run: `articles_new`, `n_topics`, `outlier_pct`, sentiment counts. This row is from the run we triggered while building this deck. |

- [ ] **Step 1: Write slides 7–11.** Slide 7 diagram: CSS grid rows, each arrow an `.arr` cell with a text label (`new rows →`, `store →`, `enrich →`, `serve →`). Gloss every technical term (`pgvector · vector similarity in SQL`, `e5-small · meaning vector`...).
- [ ] **Step 2: Render 7–11, read each.** Slide 7 is the overflow risk (tallest); if it overflows, drop node padding to 8px and gloss to 12px — do not drop content.
- [ ] **Step 3: Commit**

```bash
git add presentation/index-v2.html
git commit -m "presentation: deck v2 slides 7-11 — architecture, collection, models, topics, ops"
```

---

### Task 7: Slides 12–14 (RAG, reproducibility, contributions)

**Files:**
- Modify: `presentation/index-v2.html`

**Interfaces:**
- Consumes: Task 4 classes; facts.md TESTS/CORPUS.
- Produces: slides 12–14 finished; deck complete at 15 sections.

| # | Kicker | Assertion headline | Evidence | WHY margin note |
|---|---|---|---|---|
| 12 | PART 3 · THE ASSISTANT | The assistant reads five retrieved articles — not its memory. | 5-node flow: Question (plain language) → e5 embed → `SELECT … ORDER BY embedding <=> :q LIMIT 5` (shown as real SQL in a `.code` block) → Groq reads only those 5 → answer + numbered sources. | Retrieval-augmented generation: grounding beats fine-tuning here — the corpus changes daily, retrieval is free, and every claim carries a citation the jury can check. |
| 13 | PART 3 · REPRODUCIBILITY | The whole platform reproduces with one command. | Mono block: `docker-compose up` → 5 containers with real names + host ports from facts.md (`news_postgres :5432`, `news_api :«8001»`, `news_frontend :«5180»`, `news_prefect :4200`, `news_mlflow :5000`); schema chips for `articles`; `«N» pytest tests` | Everything open-source; secrets in `.env`; a fresh machine reaches the same running stack — the definition of reproducible MLOps. |
| 14 | PART 4 · CONTRIBUTIONS | What this project demonstrates — and where it stops. | Press table, 4 claims + evidence pointer: end-to-end platform (slides 4–6, running today) · search by meaning (pgvector + multilingual embeddings, slide 12) · assistant that cites sources (slide 12) · reproducible MLOps (Prefect + MLflow + metrics row, slides 10–11). Below, italic honest-limits line + 4 future-work chips: more sources · Arabic dialect sentiment · named-entity extraction · continuous scheduler | Honest limits: «60» articles over «2» days, French-first, sentiment unevaluated against a labeled Tunisian set. Claims are sized to the evidence. |

- [ ] **Step 1: Write slides 12–14.**
- [ ] **Step 2: Render 12–14, read each, fix overflow.**
- [ ] **Step 3: Commit**

```bash
git add presentation/index-v2.html
git commit -m "presentation: deck v2 slides 12-14 — RAG mechanics, reproducibility, contributions"
```

---

### Task 8: Full sweep, PDF export, deliver

**Files:**
- Create: `presentation/News-Insight-slides-v2.pdf`
- Create: `<scratchpad>/export_pdf.py`

**Interfaces:**
- Consumes: finished `index-v2.html` (15 sections).
- Produces: the final PDF; branch ready for PR.

- [ ] **Step 1: Full render sweep**

```bash
cd /home/ahmedklabi/dev/news-mlops
for n in $(seq 1 15); do .venv/bin/python <scratchpad>/shot.py $n <scratchpad>/sweep-$n.png; done
```

Read ALL 15 renders. Checklist per slide: no overflow; folio shows correct `N / 15`; kicker/headline/figure present; no empty whitespace band taller than ~150px (that was the old deck's sparse look).

- [ ] **Step 2: Cross-check numbers**

Grep every digit-bearing claim in `index-v2.html` against `facts.md`. Zero mismatches allowed.

- [ ] **Step 3: Write `<scratchpad>/export_pdf.py`**

```python
import pathlib
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter

root = pathlib.Path("/home/ahmedklabi/dev/news-mlops/presentation")
url = (root / "index-v2.html").as_uri()
tmp = pathlib.Path(__file__).parent
parts = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 820})
    pg.goto(url)
    n_slides = pg.evaluate("document.querySelectorAll('.slide').length")
    for n in range(1, n_slides + 1):
        pg.evaluate(f"show({n})")
        pg.wait_for_timeout(250)
        f = tmp / f"pdf-{n}.pdf"
        pg.pdf(path=str(f), width="1400px", height="820px",
               print_background=True, page_ranges="1")
        parts.append(f)
    b.close()
w = PdfWriter()
for f in parts:
    w.append(str(f))
out = root / "News-Insight-slides-v2.pdf"
with open(out, "wb") as fh:
    w.write(fh)
print("wrote", out, len(parts), "pages")
```

If `pypdf` is missing: `.venv/bin/pip install pypdf`.

- [ ] **Step 4: Export and verify**

```bash
.venv/bin/python <scratchpad>/export_pdf.py
```

Expected: `wrote .../News-Insight-slides-v2.pdf 15 pages`. Read pages 1–5 of the PDF to confirm rendering (fonts, images, no clipping).

- [ ] **Step 5: Commit and deliver**

```bash
git add presentation/News-Insight-slides-v2.pdf
git commit -m "presentation: export deck v2 PDF"
```

Send the PDF to the user. Offer PR via finishing-a-development-branch skill.
