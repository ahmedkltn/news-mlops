from etl import labels

def test_label_topics_maps_ids(monkeypatch):
    class FakeText:
        type = "text"; text = "Politique nationale"
    class FakeMsg:
        content = [FakeText()]
    class FakeMessages:
        def create(self, **kw): return FakeMsg()
    class FakeClient:
        messages = FakeMessages()
    monkeypatch.setattr(labels, "_client", lambda: FakeClient())
    out = labels.label_topics({0: ["tunisie", "gouvernement", "loi"]})
    assert out[0] == "Politique nationale"
