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
    scraping via trafilatura, sans aucune clé API. Le LLM tourne en local via
    Ollama. Zéro coût, confidentialité garantie.
    """

    # Modèle Ollama à exécuter localement.
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "phi4-mini")
    )

    # Base URL d'Ollama (par défaut localhost:11434).
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    # Langue principale analysée par Presidio (anonymisation locale).
    presidio_lang: str = field(default_factory=lambda: os.getenv("PRESIDIO_LANG", "fr"))

    # Troncature préventive : nombre max de caractères injectés par page scrapée,
    # critère encore plus important avec phi4-mini (contexte limité).
    max_chars_per_page: int = field(
        default_factory=lambda: int(os.getenv("MAX_CHARS_PER_PAGE", "20000"))
    )

    @property
    def crewai_model(self) -> str:
        """Identifiant du modèle au format LiteLLM pour Ollama local."""
        return f"ollama/{self.ollama_model}"


# Instance unique partagée par l'application.
settings = Settings()
