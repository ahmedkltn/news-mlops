from fastapi import APIRouter, Query
from etl.load import get_connection
from etl.transform import get_embedding, embeddings_available

router = APIRouter()

@router.get("/")
def semantic_search(
    q: str = Query(..., min_length=3),
    limit: int = Query(10, le=50),
):
    conn = get_connection()
    cur = conn.cursor()

    if embeddings_available():
        embedding = get_embedding(q)
        embedding_str = f"[{','.join(map(str, embedding))}]"
        cur.execute("""
            SELECT id, url, source, title, sentiment, topic_label,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM articles
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (embedding_str, embedding_str, limit))
    else:
        # No embedding model cached — degrade to keyword search so the
        # feature still works (lower relevance, no semantic ranking).
        cur.execute("""
            SELECT id, url, source, title, sentiment, topic_label,
                   ts_rank(
                       to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(content,'')),
                       plainto_tsquery('simple', %s)
                   ) AS similarity
            FROM articles
            WHERE to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(content,''))
                  @@ plainto_tsquery('simple', %s)
            ORDER BY similarity DESC
            LIMIT %s
        """, (q, q, limit))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "url": r[1],
            "source": r[2],
            "title": r[3],
            "sentiment": r[4],
            "topic_label": r[5],
            "similarity": round(r[6], 4),
        }
        for r in rows
    ]