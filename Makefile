# ── news-mlops ────────────────────────────────────────────────────────────────
# Run steps individually (DB in Docker, everything else local)
#
# Typical workflow:
#   make db          → start postgres (detached)
#   make scrape      → scrape Kapitalis, save raw articles
#   make transform   → generate embeddings + sentiment (heavy, ~few min)
#   make cluster     → run BERTopic clustering
#   make api         → start FastAPI on :8000
#   make frontend    → start Vite dev server on :5173
# ──────────────────────────────────────────────────────────────────────────────

PAGES       ?= 5
BATCH_SIZE  ?= 16
MIN_CLUSTER ?= 3

.PHONY: db db-down scrape transform cluster api frontend install logs help

# ── Infrastructure ─────────────────────────────────────────────────────────────

db:
	docker-compose up -d postgres
	@echo "✓ Postgres ready on :5432"

db-down:
	docker-compose down

db-full:
	docker-compose up -d
	@echo "✓ All services started (postgres, prefect, mlflow)"

# ── Pipeline steps ─────────────────────────────────────────────────────────────

scrape:
	python -m scripts.scrape --pages $(PAGES)

transform:
	python -m scripts.transform --batch-size $(BATCH_SIZE)

cluster:
	python -m scripts.cluster --min-cluster-size $(MIN_CLUSTER)

# Run all three in sequence
pipeline: scrape transform cluster

# ── Local servers ──────────────────────────────────────────────────────────────

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# ── Setup ──────────────────────────────────────────────────────────────────────

install:
	pip install -r requirements.txt
	cd frontend && npm install

# ── Docker full stack ──────────────────────────────────────────────────────────

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down -v

logs:
	docker-compose logs -f api

# ── Help ───────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  make db            start postgres in Docker (detached)"
	@echo "  make scrape        scrape articles  (PAGES=5)"
	@echo "  make transform     embed + sentiment (BATCH_SIZE=16)"
	@echo "  make cluster       BERTopic clustering (MIN_CLUSTER=3)"
	@echo "  make pipeline      scrape → transform → cluster"
	@echo "  make api           run FastAPI locally  (:8000)"
	@echo "  make frontend      run Vite dev server  (:5173)"
	@echo "  make install       pip install + npm install"
	@echo "  make docker-up     full docker-compose stack"
	@echo ""
