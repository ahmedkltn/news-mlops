CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS articles (
    id           SERIAL PRIMARY KEY,
    url          TEXT UNIQUE NOT NULL,
    source       TEXT NOT NULL,
    title        TEXT,
    content      TEXT,
    language     TEXT,
    scraped_at   TIMESTAMP DEFAULT NOW(),
    topic_id     INTEGER,
    topic_label  TEXT,
    sentiment    TEXT,
    embedding    vector(384),
    published_at TIMESTAMP,
    image_url    TEXT,
    categories   TEXT[],
    summary      TEXT,
    story_id     INTEGER,
    region       TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic_id);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_story ON articles(story_id);
CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region);

CREATE TABLE IF NOT EXISTS entities (
    id          SERIAL PRIMARY KEY,
    article_id  INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    label       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id            SERIAL PRIMARY KEY,
    run_at        TIMESTAMP DEFAULT NOW(),
    source        TEXT,
    articles_new  INTEGER,
    n_topics      INTEGER,
    outlier_pct   REAL,
    sentiment_pos INTEGER,
    sentiment_neu INTEGER,
    sentiment_neg INTEGER,
    embed_model   TEXT
);