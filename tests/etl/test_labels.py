from etl import labels


def test_label_topics_maps_ids(monkeypatch):
    monkeypatch.setattr(labels, "complete", lambda **kw: "Politique nationale")
    out = labels.label_topics({0: ["tunisie", "gouvernement", "loi"]})
    assert out[0] == "Politique nationale"


def test_label_topics_falls_back_on_failure(monkeypatch):
    def boom(**kw):
        raise RuntimeError("provider down")
    monkeypatch.setattr(labels, "complete", boom)
    out = labels.label_topics({3: ["a", "b"]})
    assert out[3] == "Topic 3"
