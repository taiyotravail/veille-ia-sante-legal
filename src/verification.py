"""Contrôle de fiabilité indirect (anti-hallucination).

Rétro-vérification locale : on certifie que chaque URL produite par le LLM
dans le livrable final est bien présente, à l'identique, dans le contenu source
issu de Firecrawl. Une URL absente du contexte est signalée comme potentiellement
hallucinée.
"""

from __future__ import annotations

import re

# Capture les URL http/https dans un texte Markdown.
_URL_RE = re.compile(r"https?://[^\s)\]\"'>]+")
# Ponctuation terminale à retirer (point final de phrase, virgule, etc.).
_TRAILING = ".,;:!?"


def extract_urls(text: str) -> set[str]:
    """Extrait l'ensemble des URL d'un texte.

    La ponctuation terminale (point final, virgule…) accolée à une URL est
    retirée pour éviter les faux négatifs lors de la rétro-vérification.

    Args:
        text: Texte à analyser (Markdown ou brut).

    Returns:
        Ensemble des URL trouvées (sans doublons).
    """
    return {match.rstrip(_TRAILING) for match in _URL_RE.findall(text or "")}


def verify_urls(report: str, source_corpus: str) -> dict[str, list[str]]:
    """Vérifie que les URL du rapport existent dans le corpus source.

    Args:
        report: Livrable Markdown généré par l'Analyste.
        source_corpus: Concaténation des contenus Firecrawl injectés en contexte.

    Returns:
        Dictionnaire : `{"verified": [...], "suspect": [...]}`. Les URL « suspect »
        sont absentes du corpus et doivent être revues manuellement (arbitrage
        humain) avant publication.
    """
    report_urls = extract_urls(report)
    verified: list[str] = []
    suspect: list[str] = []
    for url in sorted(report_urls):
        (verified if url in source_corpus else suspect).append(url)
    return {"verified": verified, "suspect": suspect}
