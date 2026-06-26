"""Tests unitaires de l'extraction déterministe du tableau de veille."""

from __future__ import annotations

from datetime import date

from src.extraction import build_report_from_events, classify_sector


def test_classify_sector_sante() -> None:
    """Un contexte santé est classé « IA Santé »."""
    assert classify_sector("SantExpo, salon de la santé et du médico-social") == "IA Santé"


def test_classify_sector_legal() -> None:
    """Un contexte juridique est classé « IA Légal »."""
    assert classify_sector("Village de la LegalTech : droit et contrats") == "IA Légal"


def test_classify_sector_noise_returns_none() -> None:
    """Un contexte sans mot-clé sectoriel (bruit) renvoie None."""
    assert classify_sector("Master in Management - catalogue de cours") is None


def test_build_report_extracts_date_and_keeps_in_range() -> None:
    """SantExpo (date dans le snippet) est extrait avec sa date, dans la plage."""
    events = [
        {
            "title": "SantExpo 2026",
            "url": "https://santexpo.com",
            "snippet": "SantExpo 2026 will be held from 19 to 21 May 2026 in Paris.",
        }
    ]
    res = build_report_from_events(events, date(2026, 4, 1), date(2026, 6, 30))

    assert "SantExpo 2026" in res["report"]
    assert "May 2026" in res["report"]  # date reprise verbatim
    assert "IA Santé" in res["report"]
    assert res["retenues"] == ["SantExpo 2026"]
    assert res["flaguees"] == []


def test_build_report_drops_out_of_range() -> None:
    """Un événement à date précise hors plage est écarté."""
    events = [
        {
            "title": "HealthTech Congress",
            "url": "https://h.com",
            "snippet": "Santé numérique, le 10 février 2026 à Lyon.",
        }
    ]
    res = build_report_from_events(events, date(2026, 4, 1), date(2026, 6, 30))

    assert "HealthTech Congress" not in res["report"]
    assert len(res["ecartees"]) == 1


def test_build_report_flags_imprecise_date() -> None:
    """Un événement santé sans date parsable est conservé mais flagué."""
    events = [
        {
            "title": "Salon e-santé",
            "url": "https://e.com",
            "snippet": "Le grand rendez-vous de la santé numérique, programme à venir.",
        }
    ]
    res = build_report_from_events(events, date(2026, 4, 1), date(2026, 6, 30))

    assert "Salon e-santé" in res["report"]
    assert "⚠️ à vérifier" in res["report"]
    assert res["flaguees"] == ["Salon e-santé"]


def test_build_report_skips_noise() -> None:
    """Une piste hors sujet (sans secteur) est écartée du tableau."""
    events = [
        {
            "title": "Catalogue de cours HEC",
            "url": "https://hec.edu",
            "snippet": "Liste des électifs du Master in Management.",
        }
    ]
    res = build_report_from_events(events, date(2026, 4, 1), date(2026, 6, 30))

    assert "HEC" not in res["report"]
    assert res["bruit"] == ["Catalogue de cours HEC"]
