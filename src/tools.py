"""Outils CrewAI : scraping Firecrawl et recherche web Tavily.

Le pipeline de sécurité RGPD est appliqué *à la source* : le contenu récupéré
par Firecrawl est tronqué (maîtrise du budget de tokens) puis anonymisé
localement via Presidio avant d'être renvoyé à l'agent — donc avant tout appel
au LLM distant.
"""

from __future__ import annotations

from crewai.tools import BaseTool
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from tavily import TavilyClient

from .anonymizer import anonymize
from .config import settings


class ScrapeInput(BaseModel):
    """Schéma d'entrée de l'outil de scraping."""

    url: str = Field(..., description="URL complète de la page à scraper.")


class FirecrawlScrapeTool(BaseTool):
    """Récupère une page en Markdown propre, anonymisée localement (RGPD)."""

    name: str = "firecrawl_scrape"
    description: str = (
        "Scrape une URL via Firecrawl et renvoie son contenu en Markdown propre. "
        "Le contenu est tronqué pour maîtriser le budget de tokens et anonymisé "
        "localement (Presidio) avant d'être retourné. À utiliser pour lire le "
        "détail d'une page d'événement identifiée."
    )
    args_schema: type[BaseModel] = ScrapeInput

    def _run(self, url: str) -> str:
        """Scrape, tronque puis anonymise une page.

        Args:
            url: URL de la page à récupérer.

        Returns:
            Markdown anonymisé, ou un message d'erreur exploitable par l'agent.
        """
        client = FirecrawlApp(api_key=settings.firecrawl_api_key)
        try:
            result = client.scrape_url(url, params={"formats": ["markdown"]})
        except Exception as exc:  # noqa: BLE001 — remonté à l'agent, pas masqué
            return f"Erreur de scraping pour {url} : {exc}"

        markdown = (result or {}).get("markdown", "") if isinstance(result, dict) else ""
        if not markdown:
            return f"Information non fournie : aucun contenu Markdown pour {url}."

        # 1) Troncature préventive (chunking) pour maîtriser le coût API.
        truncated = markdown[: settings.max_chars_per_page]
        # 2) Anonymisation locale stricte avant transmission au LLM.
        return anonymize(truncated)


class SearchInput(BaseModel):
    """Schéma d'entrée de l'outil de recherche."""

    query: str = Field(..., description="Requête de recherche web ciblée.")


class TavilySearchTool(BaseTool):
    """Recherche web ciblée (Tavily), résultats anonymisés localement."""

    name: str = "tavily_search"
    description: str = (
        "Recherche sur le web des événements, salons et webinaires 2026 en IA "
        "Santé et LegalTech. Renvoie des titres, URL et extraits anonymisés. "
        "À utiliser pour découvrir des sources avant de les scraper en détail."
    )
    args_schema: type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        """Effectue une recherche web et renvoie des résultats anonymisés.

        Args:
            query: Requête de recherche.

        Returns:
            Liste textuelle (titre / URL / extrait) anonymisée, ou message d'erreur.
        """
        client = TavilyClient(api_key=settings.tavily_api_key)
        try:
            response = client.search(query=query, max_results=8, search_depth="advanced")
        except Exception as exc:  # noqa: BLE001
            return f"Erreur de recherche pour « {query} » : {exc}"

        results = response.get("results", []) if isinstance(response, dict) else []
        if not results:
            return "Information non fournie : aucun résultat de recherche."

        lines = []
        for item in results:
            title = item.get("title", "Sans titre")
            url = item.get("url", "")
            snippet = (item.get("content", "") or "")[:500]
            lines.append(f"- {title}\n  URL : {url}\n  Extrait : {anonymize(snippet)}")
        return "\n".join(lines)
