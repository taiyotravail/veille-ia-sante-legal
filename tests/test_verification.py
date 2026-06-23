"""Tests unitaires de la rétro-vérification anti-hallucination."""

from __future__ import annotations

from src.verification import extract_urls, verify_urls


def test_extract_urls_finds_all_unique() -> None:
    """Extrait toutes les URL sans doublon."""
    text = "Voir https://a.com/x et https://b.com/y ainsi que https://a.com/x."
    assert extract_urls(text) == {"https://a.com/x", "https://b.com/y"}


def test_extract_urls_empty() -> None:
    """Une entrée vide renvoie un ensemble vide."""
    assert extract_urls("") == set()


def test_verify_urls_separates_verified_and_suspect() -> None:
    """Classe les URL selon leur présence dans le corpus source."""
    report = "Source : https://reel.com/event et https://hallucine.com/faux"
    corpus = "Contenu scrapé contenant https://reel.com/event uniquement."

    audit = verify_urls(report, corpus)

    assert audit["verified"] == ["https://reel.com/event"]
    assert audit["suspect"] == ["https://hallucine.com/faux"]


def test_verify_urls_no_urls() -> None:
    """Un rapport sans URL ne produit aucune entrée."""
    audit = verify_urls("Aucun lien ici.", "corpus")
    assert audit == {"verified": [], "suspect": []}
