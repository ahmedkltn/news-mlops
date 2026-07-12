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
# GenAI — any OpenAI-compatible provider (default = Groq free tier)
LLM_API_KEY=REPLACE_ME
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
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

GenAI features (summaries, "ask the news" chat, topic labels) use any OpenAI-compatible provider via `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` — default is the **Groq** free tier; switch to Gemini or OpenRouter by changing those two URLs/model values (see `.env.example`). `MLFLOW_TRACKING_URI` drives experiment tracking.

## Pipeline (step by step)

```bash
make db          # start postgres
make scrape      # fetch articles
make transform   # embeddings + sentiment
make cluster     # BERTopic topics
make api         # start API  → :8000
make frontend    # start UI   → :5173
```
