"""Tests unitaires de la rétro-vérification anti-hallucination."""

from __future__ import annotations

from datetime import date

from src.verification import (
    extract_date_label,
    extract_urls,
    parse_event_interval,
    verify_urls,
)


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


# --- Filtrage de dates strict ------------------------------------------------


def test_parse_event_interval_iso_date() -> None:
    """Une date ISO complète donne un intervalle d'un seul jour."""
    assert parse_event_interval("2026-04-15 - Paris") == (
        date(2026, 4, 15),
        date(2026, 4, 15),
    )


def test_parse_event_interval_month_only() -> None:
    """Un mois + année couvre tout le mois (premier au dernier jour)."""
    assert parse_event_interval("Avril 2026 - Paris") == (
        date(2026, 4, 1),
        date(2026, 4, 30),
    )


def test_parse_event_interval_day_french() -> None:
    """« 04 mai 2026 » (jour + mois FR) donne un intervalle d'un jour."""
    assert parse_event_interval("04 mai 2026") == (date(2026, 5, 4), date(2026, 5, 4))


def test_parse_event_interval_day_english() -> None:
    """« February 25, 2026 » (mois EN + jour) donne un intervalle d'un jour."""
    assert parse_event_interval("February 25, 2026 - Paris") == (
        date(2026, 2, 25),
        date(2026, 2, 25),
    )


def test_parse_event_interval_month_english() -> None:
    """« May 2026 » (mois EN seul) couvre tout le mois."""
    assert parse_event_interval("May 2026 - London") == (
        date(2026, 5, 1),
        date(2026, 5, 31),
    )


def test_parse_event_interval_invalid_day_returns_none() -> None:
    """Une date calendairement invalide (31 février) est rejetée."""
    assert parse_event_interval("31 février 2026") is None


def test_parse_event_interval_imprecise_returns_none() -> None:
    """Une date imprécise n'est pas parsable (exclusion stricte)."""
    assert parse_event_interval("Printemps 2026 - Lyon") is None
    assert parse_event_interval("Information non fournie") is None
    assert parse_event_interval("2026 - Paris") is None


# --- Libellé de date affichable -----------------------------------------------


def test_extract_date_label_range() -> None:
    """Un intervalle « 19 to 21 May 2026 » est restitué tel quel."""
    assert extract_date_label("SantExpo will be held from 19 to 21 May 2026.") == (
        "19 to 21 May 2026"
    )


def test_extract_date_label_single() -> None:
    """Une date simple est restituée verbatim."""
    assert extract_date_label("Rendez-vous le 04 mai 2026 à Paris.") == "04 mai 2026"


def test_extract_date_label_none() -> None:
    """Aucune date reconnue -> None."""
    assert extract_date_label("Programme à venir, inscriptions ouvertes.") is None
