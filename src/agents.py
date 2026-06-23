"""Définition des deux agents Claude (CrewAI).

- Agent 1 : Le Chercheur de niche (Niche Researcher)
- Agent 2 : L'Analyste / Rédacteur (Analyst & Writer)

Les deux agents partagent le même LLM (Anthropic via LiteLLM). Le Chercheur
dispose des outils de recherche et de scraping ; l'Analyste consolide sans
nouvel accès réseau pour limiter les risques de divergence factuelle.
"""

from __future__ import annotations

from crewai import LLM, Agent

from .config import settings
from .tools import FirecrawlScrapeTool, TavilySearchTool


def build_llm() -> LLM:
    """Construit le client LLM CrewAI pointant vers Anthropic.

    Returns:
        Une instance `LLM` configurée avec le modèle et la clé Anthropic.
    """
    return LLM(model=settings.crewai_model, api_key=settings.anthropic_api_key)


def build_researcher(llm: LLM) -> Agent:
    """Crée le Chercheur de niche.

    Args:
        llm: Client LLM partagé.

    Returns:
        L'agent CrewAI « Chercheur de niche ».
    """
    return Agent(
        role="Chercheur de niche (IA Santé & LegalTech 2026)",
        goal=(
            "Identifier, scraper et filtrer à la source les événements émergents, "
            "salons professionnels et webinaires confidentiels programmés pour 2026 "
            "dans les écosystèmes de la Santé Digitale et de la LegalTech."
        ),
        backstory=(
            "Tu es un documentaliste technologique de pointe. Ton but est d'extraire "
            "la substantifique moelle d'un ensemble de plannings bruts, en excluant le "
            "bruit commercial et en te concentrant sur l'innovation IA réelle. "
            "Tu cites toujours l'URL source exacte trouvée dans le contexte. Si une "
            "information (date, lieu, lien) est absente, tu écris littéralement "
            "« Information non fournie » au lieu de l'extrapoler."
        ),
        tools=[TavilySearchTool(), FirecrawlScrapeTool()],
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def build_analyst(llm: LLM) -> Agent:
    """Crée l'Analyste / Rédacteur.

    Args:
        llm: Client LLM partagé.

    Returns:
        L'agent CrewAI « Analyste / Rédacteur ».
    """
    return Agent(
        role="Analyste stratégique & Rédacteur",
        goal=(
            "Consolider les trouvailles du Chercheur, valider leur adéquation avec les "
            "thématiques cibles (IA Santé, IA Légal) et rédiger le reporting Markdown final."
        ),
        backstory=(
            "Tu es un analyste stratégique rigoureux. Tu transformes des listes "
            "d'événements disparates en une veille technologique actionnable pour les "
            "décideurs. Tu ne fabriques jamais d'URL ni de date : tu reproduis "
            "textuellement celles présentes dans le contexte fourni, sinon tu indiques "
            "« Information non fournie »."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
