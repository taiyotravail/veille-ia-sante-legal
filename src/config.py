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


def _require(key: str) -> str:
    """Récupère une variable d'environnement obligatoire.

    Args:
        key: Nom de la variable d'environnement.

    Returns:
        La valeur de la variable.

    Raises:
        RuntimeError: Si la variable est absente ou vide.
    """
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Variable d'environnement manquante : {key}. "
            "Copiez .env.example vers .env et renseignez vos clés."
        )
    return value


@dataclass(frozen=True)
class Settings:
    """Paramètres immuables de l'application.

    Le modèle par défaut est `claude-sonnet-4-6` : équivalent Sonnet actuel
    (fenêtre de contexte 1M tokens), retenu pour le rapport coût/performance
    annoncé dans la feuille de route. Surchargagle via ANTHROPIC_MODEL.
    """

    anthropic_api_key: str = field(default_factory=lambda: _require("ANTHROPIC_API_KEY"))
    firecrawl_api_key: str = field(default_factory=lambda: _require("FIRECRAWL_API_KEY"))
    tavily_api_key: str = field(default_factory=lambda: _require("TAVILY_API_KEY"))

    # Préfixe `anthropic/` requis par l'intégration LiteLLM de CrewAI.
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    )

    # Langue principale analysée par Presidio (anonymisation locale).
    presidio_lang: str = field(default_factory=lambda: os.getenv("PRESIDIO_LANG", "fr"))

    # Troncature préventive : nombre max de caractères injectés par page scrapée,
    # pour maîtriser le budget de tokens lors de l'ingestion de sites entiers.
    max_chars_per_page: int = field(
        default_factory=lambda: int(os.getenv("MAX_CHARS_PER_PAGE", "40000"))
    )

    @property
    def crewai_model(self) -> str:
        """Identifiant du modèle au format attendu par CrewAI/LiteLLM."""
        return f"anthropic/{self.anthropic_model}"


# Instance unique partagée par l'application.
settings = Settings()
