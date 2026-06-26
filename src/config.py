"""Configuration centralisée du projet.

Toute la configuration (clés API, modèle, paramètres de chunking) est résolue ici
afin de respecter le principe d'architecture découplée : un seul point de
modification pour le choix du modèle ou les seuils de troncature.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Charge le fichier .env local si présent (clés API, surcharges).
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Paramètres immuables de l'application.

    Pipeline 100% local et open source : recherche via DuckDuckGo (ddgs) et
    extraction déterministe en Python, sans aucune clé API ni service cloud.
    Zéro coût, confidentialité garantie.
    """

    # Langue principale analysée par Presidio (anonymisation locale).
    presidio_lang: str = field(default_factory=lambda: os.getenv("PRESIDIO_LANG", "fr"))


# Instance unique partagée par l'application.
settings = Settings()
