CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS articles (
    id          SERIAL PRIMARY KEY,
    url         TEXT UNIQUE NOT NULL,
    source      TEXT NOT NULL,
    title       TEXT,
    content     TEXT,
    language    TEXT,
    scraped_at  TIMESTAMP DEFAULT NOW(),
    topic_id    INTEGER,
    topic_label TEXT,
    sentiment   TEXT,
    embedding   vector(1024)
);

CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic_id);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at);