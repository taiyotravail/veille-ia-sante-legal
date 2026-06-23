"""Tests unitaires de l'anonymisation locale (RGPD).

Ces tests nécessitent Presidio + le modèle spaCy installés. Ils sont ignorés
automatiquement si les dépendances sont absentes (environnement CI léger).
"""

from __future__ import annotations

import pytest

pytest.importorskip("presidio_analyzer")
pytest.importorskip("presidio_anonymizer")


def test_anonymize_redacts_email() -> None:
    """Une adresse email est remplacée par un marqueur, sans fuite de DCP."""
    from src.anonymizer import anonymize

    result = anonymize("Contact : jean.dupont@example.com pour l'inscription.")
    assert "jean.dupont@example.com" not in result
    assert "EMAIL_ADDRESS" in result


def test_anonymize_empty_string() -> None:
    """Une chaîne vide est renvoyée telle quelle."""
    from src.anonymizer import anonymize

    assert anonymize("") == ""
