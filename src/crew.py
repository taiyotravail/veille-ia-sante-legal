"""Assemblage de l'équipage (Crew) et orchestration séquentielle."""

from __future__ import annotations

from crewai import Crew, Process

from .agents import build_analyst, build_llm, build_researcher
from .tasks import build_report_task, build_research_task


def build_crew() -> Crew:
    """Assemble l'équipage Chercheur -> Analyste en processus séquentiel.

    Returns:
        Le `Crew` prêt à être exécuté via `crew.kickoff()`.
    """
    llm = build_llm()
    researcher = build_researcher(llm)
    analyst = build_analyst(llm)

    return Crew(
        agents=[researcher, analyst],
        tasks=[build_research_task(researcher), build_report_task(analyst)],
        process=Process.sequential,
        verbose=True,
    )
