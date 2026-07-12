import json
import re

from fastapi import APIRouter, Query
from etl.load import get_connection
from etl.transform import get_embedding, embeddings_available
from etl.llm import complete, DEFAULT_MODEL

router = APIRouter()

COLS = "id, url, source, title, sentiment, topic_label"
CAND_LIMIT = 40


def _row_dict(r, similarity=None):
    return {"id": r[0], "url": r[1], "source": r[2], "title": r[3],
            "sentiment": r[4], "topic_label": r[5], "similarity": similarity}


def _text_matches(cur, q):
    """Articles whose text matches the query (French, accent-folded, OR terms)."""
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
    return cur.fetchall()


def _recent(cur, n):
    cur.execute(f"""
        SELECT {COLS} FROM articles
        ORDER BY COALESCE(published_at, scraped_at) DESC
        LIMIT %s
    """, (n,))
    return cur.fetchall()


def _ai_rank(q, rows, limit):
    """LLM picks ONLY the genuinely relevant candidates, ranked. Ordered ids."""
    listing = "\n".join(f"{r[0]}: {r[3]}" for r in rows)
    prompt = (
        f'Requête : "{q}"\n\n'
        f"Articles (id: titre) :\n{listing}\n\n"
        "Renvoie un tableau JSON des id des articles VRAIMENT pertinents pour la "
        "requête, du plus pertinent au moins pertinent. Comprends le sens (ex : "
        "« sport » = football, match, club, EST, ESS…). N'inclus AUCUN article "
        "hors sujet — la liste peut être courte, ou vide [] si rien ne correspond. "
        "Réponds uniquement par le tableau JSON."
    )
    try:
        out = complete(
            system="Tu es un moteur de recherche sémantique précis. Tu réponds UNIQUEMENT par un tableau JSON d'entiers, sans texte autour.",
            user=prompt, max_tokens=200, model=DEFAULT_MODEL,
        )
        m = re.search(r"\[[\d,\s]*\]", out)
        ids = json.loads(m.group(0)) if m else []
        return [int(i) for i in ids][:limit]
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

    # No embedding model — AI ranking. Candidates = text matches (precise)
    # plus recent articles (so the LLM can catch semantic matches the text
    # search misses, e.g. a football club acronym for "sport").
    text_rows = _text_matches(cur, q)
    seen = {r[0] for r in text_rows}
    candidates = list(text_rows)
    for r in _recent(cur, CAND_LIMIT):
        if r[0] not in seen and len(candidates) < CAND_LIMIT:
            candidates.append(r); seen.add(r[0])
    cur.close(); conn.close()

    if not candidates:
        return []
    by_id = {r[0]: r for r in candidates}
    ranked = [by_id[i] for i in _ai_rank(q, candidates, limit) if i in by_id][:limit]
    if not ranked:
        # LLM found nothing usable → return only genuine text matches, never
        # unrelated recent articles.
        ranked = list(text_rows)[:limit]
    return [_row_dict(r) for r in ranked]
