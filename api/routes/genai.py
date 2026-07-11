import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from etl.load import get_connection
from etl.transform import get_embedding

logger = logging.getLogger(__name__)
router = APIRouter()

_client_singleton = None
def _client():
    global _client_singleton
    if _client_singleton is None:
        import anthropic
        _client_singleton = anthropic.Anthropic()
    return _client_singleton

@router.get("/summary/{article_id}")
def summary(article_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT summary, title, content FROM articles WHERE id=%s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Article not found")
        cached, title, content = row
        if cached:
            return {"summary": cached}
        msg = _client().messages.create(
            model="claude-haiku-4-5", max_tokens=160,
            messages=[{"role": "user", "content":
                f"Résume cet article tunisien en 2 phrases claires, en français :\n\n{title}\n{(content or '')[:2000]}"}])
        text = next((b.text.strip() for b in msg.content if b.type == "text"), "")
        cur.execute("UPDATE articles SET summary=%s WHERE id=%s", (text, article_id))
        conn.commit()
        return {"summary": text}
    finally:
        cur.close()
        conn.close()


class ChatBody(BaseModel):
    q: str

@router.post("/chat")
def chat(body: ChatBody):
    emb = get_embedding(body.q)
    emb_str = f"[{','.join(map(str, emb))}]"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, url, content
        FROM articles
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (emb_str,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    context = "\n\n".join(f"[{i+1}] {r[1]}\n{(r[3] or '')[:800]}" for i, r in enumerate(rows))
    msg = _client().messages.create(
        model="claude-haiku-4-5", max_tokens=512,
        system="Tu réponds aux questions sur l'actualité tunisienne en te basant "
               "UNIQUEMENT sur les articles fournis. Cite les numéros de source. "
               "Si l'info manque, dis-le.",
        messages=[{"role": "user", "content": f"Articles:\n{context}\n\nQuestion: {body.q}"}])
    answer = next((b.text.strip() for b in msg.content if b.type == "text"), "")
    return {"answer": answer,
            "sources": [{"id": r[0], "title": r[1], "url": r[2]} for r in rows]}
