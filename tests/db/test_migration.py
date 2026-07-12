import os, pytest, psycopg2
from etl.load import get_connection

REQUIRED = {"published_at", "image_url", "categories", "summary", "story_id"}

@pytest.mark.integration
def test_articles_has_new_columns():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'articles'
    """)
    cols = {r[0] for r in cur.fetchall()}
    cur.close(); conn.close()
    assert REQUIRED.issubset(cols), f"missing: {REQUIRED - cols}"
