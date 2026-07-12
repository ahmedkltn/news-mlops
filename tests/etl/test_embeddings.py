from etl import transform


def test_query_and_passage_dims():
    import pytest
    pytest.importorskip("sentence_transformers")
    q = transform.get_embedding("politique en Tunisie")
    p = transform.get_passage_embedding("La politique en Tunisie évolue.")
    assert len(q) == 384
    assert len(p) == 384


def test_prefixes_differ(monkeypatch):
    seen = {}
    class FakeModel:
        def encode(self, text, **kw):
            seen["text"] = text
            import numpy as np
            return np.zeros(384)
    monkeypatch.setattr(transform, "_get_embedding_model", lambda: FakeModel())
    transform.get_embedding("x")
    assert seen["text"].startswith("query: ")
    transform.get_passage_embedding("y")
    assert seen["text"].startswith("passage: ")
