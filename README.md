# news-mlops

MLOps platform for Tunisian news — scrape, analyse, explore.

## Stack

- **Scraping** — BeautifulSoup (Kapitalis)
- **ML** — sentence-transformers, BERTopic, cardiffnlp sentiment
- **Storage** — PostgreSQL + pgvector
- **API** — FastAPI
- **Orchestration** — Prefect
- **Frontend** — React + Vite
- **Infra** — Docker Compose

## Run

Copy `.env.example` to `.env` and fill in real values:
```bash
cp .env.example .env
```
```env
POSTGRES_USER=news_user
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=news_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
PREFECT_API_URL=http://localhost:4200/api
MLFLOW_TRACKING_URI=http://localhost:5000
ANTHROPIC_API_KEY=sk-ant-REPLACE_ME
```

Start everything:
```bash
docker-compose up --build
```

| | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000/docs |
| Prefect | http://localhost:4200 |
| MLflow | http://localhost:5000 |

`ANTHROPIC_API_KEY` (for GenAI features) and `MLFLOW_TRACKING_URI` (experiment tracking) also belong in `.env` — see `.env` for the full list of variables.

## Pipeline (step by step)

```bash
make db          # start postgres
make scrape      # fetch articles
make transform   # embeddings + sentiment
make cluster     # BERTopic topics
make api         # start API  → :8000
make frontend    # start UI   → :5173
```
