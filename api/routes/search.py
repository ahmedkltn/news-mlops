import json
import re

from fastapi import APIRouter, Query
from etl.load import get_connection
from etl.transform import get_embedding, embeddings_available
from etl.llm import complete, FAST_MODEL

router = APIRouter()

COLS = "id, url, source, title, sentiment, topic_label"
CAND_LIMIT = 40


def _row_dict(r, similarity=None):
    return {"id": r[0], "url": r[1], "source": r[2], "title": r[3],
            "sentiment": r[4], "topic_label": r[5], "similarity": similarity}


def _candidates(cur, q):
    """Text-match candidates, topped up with recent articles, for the LLM to rank."""
    or_q = " or ".join(q.split()) or q
    cur.execute(f"""
        SELECT {COLS}
        FROM articles
        WHERE to_tsvector('french', unaccent(coalesce(title,'') || ' ' || coalesce(content,'')))
              @@ websearch_to_tsquery('french', unaccent(%s))
        ORDER BY ts_rank(
                    to_tsvector('french', unaccent(coalesce(title,'') || ' ' || coalesce(content,''))),
                    websearch_to_tsquery('french', unaccent(%s))
                 ) DESC
        LIMIT %s
    """, (or_q, or_q, CAND_LIMIT))
    rows = cur.fetchall()
    seen = {r[0] for r in rows}
    if len(rows) < CAND_LIMIT:
        cur.execute(f"""
            SELECT {COLS} FROM articles
            ORDER BY COALESCE(published_at, scraped_at) DESC
            LIMIT %s
        """, (CAND_LIMIT,))
        for r in cur.fetchall():
            if r[0] not in seen:
                rows.append(r); seen.add(r[0])
            if len(rows) >= CAND_LIMIT:
                break
    return rows


def _ai_rank(q, rows, limit):
    """Ask the LLM which candidates are relevant, ranked. Returns ordered ids."""
    listing = "\n".join(f"{r[0]}: {r[3]}" for r in rows)
    prompt = (
        f'Requête de recherche : "{q}"\n\n'
        f"Articles disponibles (id: titre) :\n{listing}\n\n"
        f"Renvoie UNIQUEMENT un tableau JSON des id des articles pertinents pour "
        f"la requête, du plus au moins pertinent (maximum {limit}). "
        f"Sois inclusif sur le sens (ex: « sport » couvre football, match, club). "
        f"Si aucun n'est pertinent, renvoie []."
    )
    try:
        out = complete(
            system="Tu es un moteur de recherche sémantique. Tu réponds UNIQUEMENT par un tableau JSON d'entiers.",
            user=prompt, max_tokens=200, model=FAST_MODEL,
        )
        m = re.search(r"\[[\d,\s]*\]", out)
        return json.loads(m.group(0)) if m else []
    except Exception:
        return []


@router.get("/")
def semantic_search(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, le=50),
):
    conn = get_connection()
    cur = conn.cursor()

    if embeddings_available():
        embedding = get_embedding(q)
        embedding_str = f"[{','.join(map(str, embedding))}]"
        cur.execute(f"""
            SELECT {COLS}, 1 - (embedding <=> %s::vector) AS similarity
            FROM articles
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (embedding_str, embedding_str, limit))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [_row_dict(r, round(r[6], 4)) for r in rows]

    # No embedding model — AI-powered ranking over text+recent candidates.
    candidates = _candidates(cur, q)
    cur.close(); conn.close()
    if not candidates:
        return []
    by_id = {r[0]: r for r in candidates}
    ranked_ids = _ai_rank(q, candidates, limit)
    ranked = [by_id[i] for i in ranked_ids if i in by_id][:limit]
    if not ranked:  # LLM gave nothing usable → fall back to text-rank order
        ranked = candidates[:limit]
    return [_row_dict(r) for r in ranked]
