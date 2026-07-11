from etl import metrics

def test_record_pipeline_metrics_inserts(monkeypatch):
    captured = {}
    class FakeCur:
        def execute(self, q, params): captured["q"] = q; captured["params"] = params
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def commit(self): ...
        def close(self): ...
    monkeypatch.setattr(metrics, "get_connection", lambda: FakeConn())
    metrics.record_pipeline_metrics({"source": "all", "articles_new": 3})
    assert "INSERT INTO pipeline_metrics" in captured["q"]
    assert captured["params"][0] == "all"
