-- Per-governorate news map: tag each article with a Tunisia governorate slug.
-- region IS NULL => untagged / national bucket.
ALTER TABLE articles ADD COLUMN IF NOT EXISTS region TEXT;
CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region);
