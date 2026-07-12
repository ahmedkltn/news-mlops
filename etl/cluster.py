import ast
import logging
import os
import numpy as np
from dotenv import load_dotenv
from etl.load import get_connection
from etl.labels import label_topics

load_dotenv(override=False)
logger = logging.getLogger(__name__)

mlflow = None


def log_clustering_run(n_topics: int, outlier_pct: float, min_cluster_size: int):
    global mlflow
    if mlflow is None:
        import mlflow as _mlflow
        mlflow = _mlflow
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("news-clustering")
    with mlflow.start_run():
        mlflow.log_params({"embed_model": "intfloat/multilingual-e5-small",
                           "min_cluster_size": min_cluster_size})
        mlflow.log_metrics({"n_topics": n_topics, "outlier_pct": outlier_pct})
        (mlflow.log_artifacts if os.path.isdir("models/bertopic_model") else mlflow.log_artifact)("models/bertopic_model")


def load_articles_for_clustering() -> tuple[list[int], list[str], list[list[float]]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, content, embedding
        FROM articles
        WHERE embedding IS NOT NULL
        ORDER BY id
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    ids, texts, embeddings = [], [], []
    for row in rows:
        ids.append(row[0])
        text = f"{row[1] or ''} {row[2] or ''}".strip()
        texts.append(text)
        embedding = row[3]
        if isinstance(embedding, str):
            embedding = ast.literal_eval(embedding)
        embeddings.append(embedding)

    logger.info(f"Loaded {len(ids)} articles for clustering")
    return ids, texts, embeddings


def update_topics(article_ids: list[int], topics: list[int], topic_labels: dict[int, str]):
    conn = get_connection()
    cur = conn.cursor()

    for article_id, topic_id in zip(article_ids, topics):
        label = topic_labels.get(topic_id, "unknown")
        cur.execute("""
            UPDATE articles SET topic_id = %s, topic_label = %s WHERE id = %s
        """, (topic_id, label, article_id))

    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Updated topics for {len(article_ids)} articles")


def run_clustering(min_cluster_size: int = 3) -> dict:
    # ── Lazy imports — only paid when clustering actually runs, not at API startup
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer
    from spacy.lang.fr.stop_words import STOP_WORDS as FR_STOP_WORDS
    # ─────────────────────────────────────────────────────────────────────────────

    ids, texts, embeddings = load_articles_for_clustering()

    if len(ids) < 10:
        logger.warning(f"Not enough articles: {len(ids)}, need at least 10")
        return {"status": "skipped", "reason": "not enough articles"}

    embeddings_array = np.array(embeddings)

    vectorizer = CountVectorizer(
        min_df=1,
        stop_words=list(FR_STOP_WORDS),
        ngram_range=(1, 2),
    )

    logger.info("Fitting BERTopic model…")
    topic_model = BERTopic(
        vectorizer_model=vectorizer,
        min_topic_size=min_cluster_size,
        language="french",
        calculate_probabilities=False,
        verbose=True,
    )

    topics, _ = topic_model.fit_transform(texts, embeddings=embeddings_array)

    topic_info = topic_model.get_topic_info()
    topic_labels = {
        row["Topic"]: row["Name"]
        for _, row in topic_info.iterrows()
        if row["Topic"] != -1
    }

    logger.info(f"Found {len(topic_labels)} topics")
    for tid, label in topic_labels.items():
        logger.info(f"  Topic {tid}: {label}")

    try:
        topic_keywords = {
            tid: [w for w, _ in topic_model.get_topic(tid)]
            for tid in topic_labels
        }
        topic_labels = label_topics(topic_keywords)
        logger.info("Generated human-readable topic labels via Claude Haiku")
    except Exception:
        logger.warning("Failed to generate LLM topic labels, falling back to raw BERTopic names", exc_info=True)

    os.makedirs("models", exist_ok=True)
    topic_model.save("models/bertopic_model")
    logger.info("Model saved to models/bertopic_model")

    update_topics(ids, topics, topic_labels)

    outlier_pct = topics.count(-1) / max(len(topics), 1)
    try:
        log_clustering_run(len(topic_labels), outlier_pct, min_cluster_size)
    except Exception:
        logger.warning("Failed to log clustering run to MLflow", exc_info=True)

    return {
        "status": "done",
        "articles_clustered": len(ids),
        "topics_found": len(topic_labels),
        "outliers": topics.count(-1),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_clustering())
