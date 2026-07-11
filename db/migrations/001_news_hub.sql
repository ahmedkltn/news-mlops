-- 001_news_hub.sql — additive migration, safe to run on an existing DB
ALTER TABLE articles ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS image_url    TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS categories   TEXT[];
ALTER TABLE articles ADD COLUMN IF NOT EXISTS summary      TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS story_id     INTEGER;

CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_story ON articles(story_id);

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
