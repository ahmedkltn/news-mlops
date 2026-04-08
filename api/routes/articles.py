from fastapi import APIRouter, Query
from etl.load import get_connection

router = APIRouter()

@router.get("/")
def get_articles(
    source: str = Query(None),
    sentiment: str = Query(None),
    topic_id: int = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    conn = get_connection()
    cur = conn.cursor()

    filters = []
    params = []

    if source:
        filters.append("source = %s")
        params.append(source)
    if sentiment:
        filters.append("sentiment = %s")
        params.append(sentiment)
    if topic_id is not None:
        filters.append("topic_id = %s")
        params.append(topic_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.extend([limit, offset])

    cur.execute(f"""
        SELECT id, url, source, title, language, sentiment,
               topic_id, topic_label, scraped_at
        FROM articles
        {where}
        ORDER BY scraped_at DESC
        LIMIT %s OFFSET %s
    """, params)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "url": r[1],
            "source": r[2],
            "title": r[3],
            "language": r[4],
            "sentiment": r[5],
            "topic_id": r[6],
            "topic_label": r[7],
            "scraped_at": r[8],
        }
        for r in rows
    ]

@router.get("/topics")
def get_topics():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT topic_id, topic_label, COUNT(*) as count
        FROM articles
        WHERE topic_id IS NOT NULL
        GROUP BY topic_id, topic_label
        ORDER BY count DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"topic_id": r[0], "topic_label": r[1], "count": r[2]}
        for r in rows
    ]

@router.get("/{article_id}")
def get_article(article_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, url, source, title, content, language,
               sentiment, topic_id, topic_label, scraped_at
        FROM articles WHERE id = %s
    """, (article_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "id": row[0],
        "url": row[1],
        "source": row[2],
        "title": row[3],
        "content": row[4],
        "language": row[5],
        "sentiment": row[6],
        "topic_id": row[7],
        "topic_label": row[8],
        "scraped_at": row[9],
    }