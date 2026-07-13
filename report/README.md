# News Insight — Project Report

LaTeX source for the ISI end-of-semester project report on **News Insight: An
MLOps Platform for Tunisian News Analysis**.

- **Authors:** Ahmed Klabi, Mariem Smadhi, Hichem Sboui
- **Academic supervisor:** Sawssen Jalel
- **Template:** ISI PFE report class (`tpl/isipfe`)
- **Structure:** General Introduction + 11 chapters + List of Acronyms +
  Webography, ~104 pages, English

## Build

The only prerequisite is Docker — no local LaTeX install needed.

```bash
docker run --rm -v "$PWD/report":/work -w /work texlive/texlive \
  latexmk -pdf -interaction=nonstopmode main.tex
```

Run it twice from a clean tree (or just twice in a row) so the table of
contents, list of figures, and cross-references settle — `latexmk` already
reruns `pdflatex`/`bibtex` internally as needed, so two invocations of the
command above is enough even on a first build.

Output: `report/main.pdf` (~104 pages). Build artifacts (`*.aux`, `*.toc`,
`*.lof`, `*.fdb_latexmk`, `main.pdf`, etc.) are git-ignored; only the
LaTeX sources and images are tracked.

To force a fully clean rebuild first:

```bash
docker run --rm -v "$PWD/report":/work -w /work texlive/texlive \
  latexmk -C main.tex
```

## Regenerating figures

Most figures under `report/img/` are committed directly and don't need to be
regenerated. Two categories are generated from source and can be rebuilt:

- **Diagrams** (architecture, sequence, class, use-case diagrams):
  Mermaid sources live in `report/diagrams/*.mmd`. Render them all to
  `report/img/*.png` with:

  ```bash
  bash report/diagrams/render.sh
  ```

  Requires Docker (uses the dockerised `minlag/mermaid-cli`).

- **Screenshots** (dashboard, search, chat, API docs, Prefect UI, MLflow UI):
  Captured live from the running application by `report/screenshots.py`.
  Requires the project's `docker-compose` stack to be up and Playwright
  installed:

  ```bash
  pip install playwright
  python -m playwright install chromium
  python report/screenshots.py
  ```

  See the script's docstring for the expected host ports (`FRONTEND_URL`,
  `API_URL`, `PREFECT_URL`, `MLFLOW_URL`), overridable via environment
  variables if your stack uses different port mappings.

- **Logos** (Python, React, Docker, FastAPI, PostgreSQL, Prefect, MLflow,
  Vite, Hugging Face, etc.) are committed as static assets and never need
  regeneration.

## Report structure

| # | Chapter |
|---|---------|
| — | General Introduction |
| 1 | Introduction |
| 2 | Global Architecture |
| 3 | Data Ingestion and Web Scraping |
| 4 | Storage Layer and Database Design |
| 5 | Machine Learning and NLP Pipeline |
| 6 | GenAI Features |
| 7 | Orchestration and Experiment Tracking |
| 8 | Backend and Data Exposure |
| 9 | Deployment and DevOps |
| 10 | Frontend and Data Visualization |
| 11 | Final Conclusion and Future Improvements |
| — | Webography |
