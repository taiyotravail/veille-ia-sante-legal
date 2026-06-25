"""Définition des deux agents phi4-mini (CrewAI via Ollama).

- Agent 1 : Le Chercheur de niche (Niche Researcher)
- Agent 2 : L'Analyste / Rédacteur (Analyst & Writer)

Les deux agents partagent le même LLM local (Ollama + phi4-mini).
Zéro transmission cloud, confidentialité garantie, coûts nuls.
"""

from __future__ import annotations

from crewai import Agent, LLM

from .config import settings
from .tools import DuckDuckGoSearchTool, WebScrapeTool


def build_llm() -> LLM:
    """Construit le client LLM Ollama local (phi4-mini) via CrewAI/LiteLLM.

    Returns:
        Une instance `LLM` configurée pour Ollama local.
    """
    return LLM(
        model=settings.crewai_model,
        base_url=settings.ollama_base_url,
        temperature=0.5,
    )


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
        tools=[DuckDuckGoSearchTool(), WebScrapeTool()],
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
