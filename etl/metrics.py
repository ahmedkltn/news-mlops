import logging
from etl.load import get_connection

logger = logging.getLogger(__name__)

def record_pipeline_metrics(m: dict) -> None:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO pipeline_metrics
            (source, articles_new, n_topics, outlier_pct,
             sentiment_pos, sentiment_neu, sentiment_neg, embed_model)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (m.get("source"), m.get("articles_new"), m.get("n_topics"),
          m.get("outlier_pct"), m.get("sentiment_pos"), m.get("sentiment_neu"),
          m.get("sentiment_neg"), m.get("embed_model")))
    conn.commit(); cur.close(); conn.close()
    logger.info(f"Recorded pipeline metrics: {m}")
