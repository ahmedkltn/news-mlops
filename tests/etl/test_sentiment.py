import numpy as np

from etl import transform
from scrapers.base import Article

# Distinct, position-dependent labels so a shuffled/duplicated result would fail.
_LABELS = ["Positive", "Negative", "Neutral"]


def test_get_sentiments_batched(monkeypatch):
    def fake_pipeline():
        def run(texts, **kw):
            return [{"label": _LABELS[i]} for i, _ in enumerate(texts)]
        return run
    monkeypatch.setattr(transform, "_get_sentiment_pipeline", fake_pipeline)
    out = transform.get_sentiments(["a", "b", "c"])
    assert out == ["positive", "negative", "neutral"]


def test_transform_articles_sentiment_order(monkeypatch):
    """
    End-to-end check that transform_articles maps sentiments[i] -> articles[i].

    Note: an "empty-text article in the middle" case is not constructible here
    because the Pydantic Article validator rejects empty title/content, so the
    `continue` branch in transform_articles is effectively unreachable for
    validated inputs — ordering/alignment is what actually matters, and that's
    what this test verifies.
    """
    articles = [
        Article(url="https://example.com/1", source="test", title="Title A", content="Content A"),
        Article(url="https://example.com/2", source="test", title="Title B", content="Content B"),
        Article(url="https://example.com/3", source="test", title="Title C", content="Content C"),
    ]

    class FakeModel:
        def encode(self, texts, **kw):
            return np.zeros((len(texts), 384))

    def fake_pipeline():
        def run(texts, **kw):
            return [{"label": _LABELS[i]} for i, _ in enumerate(texts)]
        return run

    monkeypatch.setattr(transform, "_get_embedding_model", lambda: FakeModel())
    monkeypatch.setattr(transform, "_get_sentiment_pipeline", fake_pipeline)

    out = transform.transform_articles(articles)

    expected = ["positive", "negative", "neutral"]
    assert [row["sentiment"] for row in out] == expected
