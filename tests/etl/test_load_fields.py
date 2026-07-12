from etl import load

def test_save_articles_sql_includes_new_columns(monkeypatch):
    captured = {}
    class FakeCur:
        rowcount = 1
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def commit(self): ...
        def rollback(self): ...
        def close(self): ...
    def fake_execute_values(cur, query, rows):
        captured["query"] = query; captured["rows"] = rows
    monkeypatch.setattr(load, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(load, "execute_values", fake_execute_values)
    load.save_articles([{
        "url": "u", "source": "s", "title": "t", "content": "c", "language": "fr",
        "topic_id": None, "topic_label": None, "sentiment": "neutral",
        "embedding": [0.0], "published_at": "2026-07-11", "image_url": "i",
        "categories": ["a"],
    }])
    assert "published_at" in captured["query"]
    assert "image_url" in captured["query"]
    assert "categories" in captured["query"]
