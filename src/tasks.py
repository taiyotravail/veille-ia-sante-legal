"""Définition des tâches CrewAI (recherche puis rédaction du reporting)."""

from __future__ import annotations

from crewai import Agent, Task

# Structure imposée du livrable final (cf. feuille de route §5).
_REPORT_TEMPLATE = """\
| Date & Lieu | Événement | Secteur | Thème IA 2026 | Poids Stratégique (1-5) | Lien Source / Inscription |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""


def build_research_task(agent: Agent) -> Task:
    """Tâche de recherche et de filtrage à la source.

    Args:
        agent: Le Chercheur de niche.

    Returns:
        La tâche CrewAI de collecte.
    """
    return Task(
        description=(
            "Recherche les salons, conférences et webinaires programmés en 2026 sur "
            "l'IA en Santé Digitale et en LegalTech. Pour chaque piste pertinente, "
            "scrape la page source afin d'extraire : la date, le lieu, le nom de "
            "l'événement, le thème IA précis et l'URL d'inscription EXACTE. "
            "Exclus le bruit purement commercial. Reproduis fidèlement les URL et les "
            "dates telles qu'elles apparaissent dans le contenu scrapé ; si une donnée "
            "manque, écris « Information non fournie »."
        ),
        expected_output=(
            "Une liste structurée d'événements, chacun avec : date, lieu, nom, secteur "
            "(IA Santé ou IA Légal), thème IA, et l'URL source exacte issue du scraping."
        ),
        agent=agent,
    )


def build_report_task(agent: Agent) -> Task:
    """Tâche de consolidation et de rédaction du reporting Markdown.

    Args:
        agent: L'Analyste / Rédacteur.

    Returns:
        La tâche CrewAI de rédaction.
    """
    return Task(
        description=(
            "À partir des trouvailles du Chercheur, valide l'adéquation stratégique de "
            "chaque événement avec les thématiques IA Santé / IA Légal, attribue un "
            "Poids Stratégique de 1 à 5, et produis le tableau de reporting Markdown. "
            "N'invente aucune URL ni date : reprends uniquement celles présentes dans le "
            "contexte. Toute donnée absente doit être notée « Information non fournie »."
        ),
        expected_output=(
            "Un tableau Markdown respectant exactement cet en-tête, suivi d'une ligne "
            "par événement :\n\n" + _REPORT_TEMPLATE
        ),
        agent=agent,
        output_file="rapport_veille_2026.md",
    )
