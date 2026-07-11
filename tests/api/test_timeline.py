from fastapi.testclient import TestClient
import api.routes.articles as articles
from api.main import app

def test_timeline_shape(monkeypatch):
    class FakeCur:
        def execute(self, q, p=None): self._q = q
        def fetchall(self): return [("2026-07-10", 3, 2, 1)]
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def close(self): ...
    monkeypatch.setattr(articles, "get_connection", lambda: FakeConn())
    client = TestClient(app)
    r = client.get("/articles/timeline?days=30")
    assert r.status_code == 200
    assert r.json()[0]["positive"] == 3
