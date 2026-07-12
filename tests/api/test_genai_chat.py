from fastapi.testclient import TestClient
import api.routes.genai as genai
from api.main import app

def test_chat_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(genai, "get_embedding", lambda q: [0.0] * 384, raising=False)
    class FakeCur:
        def execute(self, q, p=None): ...
        def fetchall(self): return [(1, "Titre A", "https://x.tn/a", "corps a")]
        def close(self): ...
    class FakeConn:
        def cursor(self): return FakeCur()
        def close(self): ...
    monkeypatch.setattr(genai, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(genai, "complete",
        lambda **kw: "Réponse fondée sur les sources.", raising=False)
    client = TestClient(app)
    r = client.post("/genai/chat", json={"q": "Que se passe-t-il en Tunisie ?"})
    assert r.status_code == 200
    assert r.json()["sources"][0]["title"] == "Titre A"
