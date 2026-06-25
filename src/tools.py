"""Outils CrewAI 100% open source : scraping (trafilatura) et recherche (DuckDuckGo).

Aucune clé API ni service cloud propriétaire n'est requis : la recherche passe par
DuckDuckGo (`ddgs`) et l'extraction de contenu par `trafilatura`, tous deux en pur
Python et exécutés localement.

Le pipeline de sécurité RGPD est appliqué *à la source* : le contenu récupéré est
tronqué (maîtrise du budget de tokens) puis anonymisé localement via Presidio avant
d'être renvoyé à l'agent — donc avant tout appel au LLM.
"""

from __future__ import annotations

import trafilatura
from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field

from .anonymizer import anonymize
from .config import settings


class ScrapeInput(BaseModel):
    """Schéma d'entrée de l'outil de scraping."""

    url: str = Field(..., description="URL complète de la page à scraper.")


class WebScrapeTool(BaseTool):
    """Récupère une page en Markdown propre (trafilatura), anonymisée localement (RGPD)."""

    name: str = "web_scrape"
    description: str = (
        "Scrape une URL et renvoie son contenu principal en Markdown propre "
        "(extraction locale via trafilatura, sans navigateur). Le contenu est tronqué "
        "pour maîtriser le budget de tokens et anonymisé localement (Presidio) avant "
        "d'être retourné. À utiliser pour lire le détail d'une page d'événement identifiée."
    )
    args_schema: type[BaseModel] = ScrapeInput

    def _run(self, url: str) -> str:
        """Scrape, tronque puis anonymise une page.

        Args:
            url: URL de la page à récupérer.

        Returns:
            Markdown anonymisé, ou un message d'erreur exploitable par l'agent.
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return f"Erreur de scraping pour {url} : page inaccessible."
            markdown = trafilatura.extract(
                downloaded, output_format="markdown", include_links=True
            )
        except Exception as exc:  # noqa: BLE001 — remonté à l'agent, pas masqué
            return f"Erreur de scraping pour {url} : {exc}"

        if not markdown:
            return f"Information non fournie : aucun contenu exploitable pour {url}."

        # 1) Troncature préventive (chunking) pour maîtriser le budget de tokens.
        truncated = markdown[: settings.max_chars_per_page]
        # 2) Anonymisation locale stricte avant transmission au LLM.
        return anonymize(truncated)


class SearchInput(BaseModel):
    """Schéma d'entrée de l'outil de recherche."""

    query: str = Field(..., description="Requête de recherche web ciblée.")


class DuckDuckGoSearchTool(BaseTool):
    """Recherche web ciblée (DuckDuckGo), résultats anonymisés localement."""

    name: str = "web_search"
    description: str = (
        "Recherche sur le web des événements, salons et webinaires 2026 en IA "
        "Santé et LegalTech via DuckDuckGo (sans clé API). Renvoie des titres, URL "
        "et extraits anonymisés. À utiliser pour découvrir des sources avant de les "
        "scraper en détail."
    )
    args_schema: type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        """Effectue une recherche web et renvoie des résultats anonymisés.

        Args:
            query: Requête de recherche.

        Returns:
            Liste textuelle (titre / URL / extrait) anonymisée, ou message d'erreur.
        """
        try:
            results = DDGS().text(query, max_results=8)
        except Exception as exc:  # noqa: BLE001
            return f"Erreur de recherche pour « {query} » : {exc}"

        if not results:
            return "Information non fournie : aucun résultat de recherche."

        lines = []
        for item in results:
            title = item.get("title", "Sans titre")
            url = item.get("href", "")
            snippet = (item.get("body", "") or "")[:500]
            lines.append(f"- {title}\n  URL : {url}\n  Extrait : {anonymize(snippet)}")
        return "\n".join(lines)
