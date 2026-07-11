from fastapi.testclient import TestClient
import api.routes.genai as genai
from api.main import app

def test_summary_returns_cached(monkeypatch):
    # DB returns an already-cached summary → no LLM call
    class FakeCur:
        def execute(self, q, p=None): self._q = q
        def fetchone(self): return ("Résumé en cache", "titre", "corps")
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def commit(self): ...
        def close(self): ...
    monkeypatch.setattr(genai, "get_connection", lambda: FakeConn())
    client = TestClient(app)
    r = client.get("/genai/summary/1")
    assert r.status_code == 200
    assert r.json()["summary"] == "Résumé en cache"
