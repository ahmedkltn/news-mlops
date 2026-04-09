import logging
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv(override=False)  # never override vars already set by Docker
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

def save_raw_articles(articles) -> int:
    """
    Step 1 — persist scraped articles with no ML fields.
    Accepts Article dataclass objects or plain dicts.
    Skips urls that already exist so re-runs are safe.
    """
    if not articles:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    rows = [
        (
            a.url     if hasattr(a, "url")     else a["url"],
            a.source  if hasattr(a, "source")  else a["source"],
            a.title   if hasattr(a, "title")   else a.get("title"),
            a.content if hasattr(a, "content") else a.get("content"),
            a.language if hasattr(a, "language") else a.get("language"),
        )
        for a in articles
    ]

    query = """
        INSERT INTO articles (url, source, title, content, language)
        VALUES %s
        ON CONFLICT (url) DO NOTHING
    """

    try:
        execute_values(cur, query, rows)
        conn.commit()
        inserted = cur.rowcount
        logger.info(f"Saved {inserted} raw articles to DB")
        return inserted
    except Exception as e:
        conn.rollback()
        logger.error(f"DB insert failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def fetch_untransformed_articles() -> list[dict]:
    """Return articles that have no embedding yet (need transform step)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, url, source, title, content, language
        FROM articles
        WHERE embedding IS NULL
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "url": r[1], "source": r[2],
         "title": r[3], "content": r[4], "language": r[5]}
        for r in rows
    ]


def update_article_ml_fields(article_id: int, embedding: list, sentiment: str):
    """Write embedding + sentiment back for a single article."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE articles
        SET embedding = %s, sentiment = %s
        WHERE id = %s
    """, (embedding, sentiment, article_id))
    conn.commit()
    cur.close()
    conn.close()


def save_articles(articles: list[dict]) -> int:
    """
    Full upsert — used by the all-in-one pipeline.
    Each dict must have: url, source, title, content, language,
                         topic_id, topic_label, sentiment, embedding
    """
    if not articles:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    rows = [
        (
            a["url"], a["source"], a["title"], a["content"], a["language"],
            a.get("topic_id"), a.get("topic_label"),
            a.get("sentiment"), a.get("embedding"),
        )
        for a in articles
    ]

    query = """
        INSERT INTO articles (
            url, source, title, content, language,
            topic_id, topic_label, sentiment, embedding
        )
        VALUES %s
        ON CONFLICT (url) DO UPDATE SET
            topic_id    = EXCLUDED.topic_id,
            topic_label = EXCLUDED.topic_label,
            sentiment   = EXCLUDED.sentiment,
            embedding   = EXCLUDED.embedding
    """

    try:
        execute_values(cur, query, rows)
        conn.commit()
        inserted = cur.rowcount
        logger.info(f"Saved {inserted} articles to DB")
        return inserted
    except Exception as e:
        conn.rollback()
        logger.error(f"DB insert failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()