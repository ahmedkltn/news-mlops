from etl import llm


class _FakeResp:
    def __init__(self, content):
        msg = type("M", (), {"content": content})()
        self.choices = [type("C", (), {"message": msg})()]


def _fake_client(capture):
    class Completions:
        def create(self, **kw):
            capture.update(kw)
            return _FakeResp("  Titre  ")

    class Chat:
        completions = Completions()

    return type("Client", (), {"chat": Chat()})()


def test_complete_returns_stripped_content(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "_client", lambda: _fake_client(cap))
    out = llm.complete(user="salut", system="sys", max_tokens=42)
    assert out == "Titre"
    assert cap["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "salut"},
    ]
    assert cap["max_tokens"] == 42


def test_complete_omits_system_when_none(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "_client", lambda: _fake_client(cap))
    llm.complete(user="q")
    assert cap["messages"] == [{"role": "user", "content": "q"}]


def test_complete_uses_env_model(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "_client", lambda: _fake_client(cap))
    monkeypatch.setenv("LLM_MODEL", "some/model:free")
    llm.complete(user="q")
    assert cap["model"] == "some/model:free"
