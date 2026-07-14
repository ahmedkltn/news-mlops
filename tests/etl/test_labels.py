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
    assert out[3] == "A / B"


def test_clean_label_keeps_short_title():
    assert labels.clean_label("Tension au détroit d'Ormuz", ["ormuz"], 3) == "Tension au détroit d'Ormuz"


def test_clean_label_strips_quotes_and_final_dot():
    assert labels.clean_label('"Été chaud en Tunisie".', ["canicule"], 3) == "Été chaud en Tunisie"


def test_clean_label_rejects_meta_chatter():
    leaked = (
        "Je vois plusieurs options de titres possibles mais je vais te choisir "
        "une de moins de quatre mots La mort de"
    )
    assert labels.clean_label(leaked, ["décès", "football"], 7) == "Décès / Football"


def test_clean_label_rejects_overlong_output():
    assert (
        labels.clean_label("Un titre beaucoup trop long qui dépasse largement la limite fixée", [], 9)
        == "Topic 9"
    )


def test_clean_label_empty_falls_back_to_keywords_then_tid():
    assert labels.clean_label("", ["sport"], 4) == "Sport"
    assert labels.clean_label(None, [], 4) == "Topic 4"
