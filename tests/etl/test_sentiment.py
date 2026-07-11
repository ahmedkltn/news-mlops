from etl import transform

def test_get_sentiments_batched(monkeypatch):
    def fake_pipeline():
        def run(texts, **kw):
            return [{"label": "Positive"} for _ in texts]
        return run
    monkeypatch.setattr(transform, "_get_sentiment_pipeline", fake_pipeline)
    out = transform.get_sentiments(["a", "b", "c"])
    assert out == ["positive", "positive", "positive"]
