import logging
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

def save_articles(articles: list[dict]) -> int:
    """
    Each article dict should have:
    url, source, title, content, language, categories,
    published_at, topic_id, topic_label, sentiment, embedding
    """
    if not articles:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    rows = [
        (
            a["url"],
            a["source"],
            a["title"],
            a["content"],
            a["language"],
            a.get("topic_id"),
            a.get("topic_label"),
            a.get("sentiment"),
            a.get("embedding"),
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