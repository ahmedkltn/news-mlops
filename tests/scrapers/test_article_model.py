import pytest
from pydantic import ValidationError
from scrapers.base import Article

def test_valid_article():
    a = Article(url="https://x.tn/1", source="kapitalis",
                title="Titre", content="Corps de l'article", language="fr")
    assert a.image_url is None
    assert a.categories == []

def test_empty_title_rejected():
    with pytest.raises(ValidationError):
        Article(url="https://x.tn/1", source="s", title="  ", content="body", language="fr")

def test_empty_content_rejected():
    with pytest.raises(ValidationError):
        Article(url="https://x.tn/1", source="s", title="t", content="", language="fr")
