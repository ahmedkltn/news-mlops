import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from etl.load import get_connection
from etl.transform import get_embedding, embeddings_available
from etl.llm import complete, model_for, FAST_MODEL, DEFAULT_MODEL

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/summary/{article_id}")
def summary(article_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT summary, title, content FROM articles WHERE id=%s", (article_id,))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row:
        raise HTTPException(404, "Article not found")
    cached, title, content = row
    if cached:
        return {"summary": cached}

    text = complete(
        user=f"Résume cet article tunisien en 2 phrases claires, en français :\n\n{title}\n{(content or '')[:2000]}",
        max_tokens=160,
        model=model_for("summary", FAST_MODEL),
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE articles SET summary=%s WHERE id=%s", (text, article_id))
        conn.commit()
        cur.close()
    finally:
        conn.close()

    return {"summary": text}


class ChatBody(BaseModel):
    q: str

@router.post("/chat")
def chat(body: ChatBody):
    conn = get_connection()
    cur = conn.cursor()
    if embeddings_available():
        emb = get_embedding(body.q)
        emb_str = f"[{','.join(map(str, emb))}]"
        cur.execute("""
            SELECT id, title, url, content
            FROM articles
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, (emb_str,))
    else:
        # No embedding model cached — rank by keyword relevance, but always
        # return the top 5 (relevance then recency) so the model has real
        # articles to ground its answer even on a loose/no-match query.
        cur.execute("""
            SELECT id, title, url, content
            FROM articles
            ORDER BY ts_rank(
                        to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(content,'')),
                        plainto_tsquery('simple', %s)
                     ) DESC,
                     COALESCE(published_at, scraped_at) DESC
            LIMIT 5
        """, (body.q,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    context = "\n\n".join(f"[{i+1}] {r[1]}\n{(r[3] or '')[:800]}" for i, r in enumerate(rows))
    answer = complete(
        system="Tu réponds aux questions sur l'actualité tunisienne en te basant "
               "UNIQUEMENT sur les articles fournis. Cite les numéros de source. "
               "Si l'info manque, dis-le.",
        user=f"Articles:\n{context}\n\nQuestion: {body.q}",
        max_tokens=512,
        model=model_for("chat", DEFAULT_MODEL),
    )
    return {"answer": answer,
            "sources": [{"id": r[0], "title": r[1], "url": r[2]} for r in rows]}
