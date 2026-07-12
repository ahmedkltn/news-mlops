from etl import regions
from etl.regions import (
    GOVERNORATES, SLUGS, normalize, region_label,
    tag_region_gazetteer, tag_region_llm, tag_region,
)


def test_exactly_24_governorates():
    assert len(GOVERNORATES) == 24
    assert len(set(SLUGS)) == 24


def test_every_governorate_has_required_fields():
    for slug, meta in GOVERNORATES.items():
        assert meta["fr"] and meta["ar"] and meta["geojson_id"]
        assert meta["aliases"], slug
        assert meta["geojson_id"].startswith("TN-")


def test_normalize_strips_latin_accents_and_case():
    assert normalize("Béja") == "beja"
    assert normalize("  GABÈS  ") == "gabes"
    assert normalize("Sidi   Bouzid") == "sidi bouzid"


def test_normalize_keeps_arabic_letters():
    assert "صفاقس" in normalize("صفاقس")


def test_gazetteer_matches_governorate_name():
    assert tag_region_gazetteer("Grève générale à Sfax", "") == "sfax"


def test_gazetteer_matches_city_to_governorate():
    # Djerba is in Médenine
    assert tag_region_gazetteer("Tourisme à Djerba en hausse") == "medenine"
    # Hammamet is in Nabeul
    assert tag_region_gazetteer("Festival de Hammamet") == "nabeul"


def test_gazetteer_title_outweighs_body():
    # 'sousse' once in title (x3) beats 'sfax' once in body
    slug = tag_region_gazetteer("Match à Sousse", "communiqué depuis Sfax")
    assert slug == "sousse"


def test_gazetteer_matches_arabic_alias():
    assert tag_region_gazetteer("خبر من صفاقس") == "sfax"


def test_gazetteer_no_match_returns_none():
    assert tag_region_gazetteer("Le gouvernement annonce une réforme") is None


def test_gazetteer_word_boundary_no_false_positive():
    # 'kef' must not match inside another word
    assert tag_region_gazetteer("Le weekend prolongé approche") is None


def test_llm_fallback_accepts_valid_slug(monkeypatch):
    # tag_region_llm does `from etl.llm import complete` at call time
    import etl.llm as llm
    monkeypatch.setattr(llm, "complete", lambda **kw: "sfax")
    assert tag_region_llm("Un titre ambigu", "corps") == "sfax"


def test_llm_fallback_rejects_hallucinated_slug(monkeypatch):
    import etl.llm as llm
    monkeypatch.setattr(llm, "complete", lambda **kw: "atlantis")
    assert tag_region_llm("titre", "corps") is None


def test_llm_fallback_normalizes_spaced_answer(monkeypatch):
    import etl.llm as llm
    monkeypatch.setattr(llm, "complete", lambda **kw: "Sidi Bouzid")
    assert tag_region_llm("t", "c") == "sidi-bouzid"


def test_tag_region_skips_llm_when_gazetteer_hits(monkeypatch):
    import etl.llm as llm
    def _boom(**kw):
        raise AssertionError("LLM should not be called on a gazetteer hit")
    monkeypatch.setattr(llm, "complete", _boom)
    assert tag_region("Incident à Bizerte", "", use_llm=True) == "bizerte"


def test_tag_region_no_llm_flag():
    assert tag_region("texte neutre sans lieu", "", use_llm=False) is None


def test_region_label():
    assert region_label("sfax") == "Sfax"
    assert region_label(None) == "National / non localisé"
