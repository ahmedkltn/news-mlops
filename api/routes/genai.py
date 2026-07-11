import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from etl.load import get_connection

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
    # implemented in Task C2
    raise HTTPException(501, "not implemented")
