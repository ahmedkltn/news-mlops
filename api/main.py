import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api.routes import pipeline, articles, search

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="News MLOps API",
    description="API for Tunisian news scraping, clustering and sentiment analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(search.router, prefix="/search", tags=["search"])

@app.get("/health")
def health():
    return {"status": "ok"}