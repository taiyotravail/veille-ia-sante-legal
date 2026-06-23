"""Anonymisation locale stricte (RGPD) basée sur Microsoft Presidio.

Ce module s'exécute **localement sur le Mac M1**. Aucune Donnée à Caractère
Personnel (DCP) ne doit quitter la machine : tout texte issu de Firecrawl est
expurgé ici (noms, emails, téléphones, etc.) avant transmission à l'API Anthropic.
"""

from __future__ import annotations

from functools import lru_cache

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from .config import settings

# Catégories de DCP expurgées. On vise les entités à risque RGPD tout en
# préservant le contenu événementiel utile (dates, organisations, URL).
_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IBAN_CODE",
    "CREDIT_CARD",
    "IP_ADDRESS",
]


@lru_cache(maxsize=1)
def _engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    """Instancie (une seule fois) les moteurs Presidio.

    Les moteurs sont coûteux à charger (modèle spaCy) ; on les met en cache pour
    toute la durée du processus.

    Returns:
        Le couple (analyzer, anonymizer).
    """
    return AnalyzerEngine(), AnonymizerEngine()


def anonymize(text: str) -> str:
    """Expurge les DCP d'un texte avant transmission au LLM.

    Args:
        text: Texte brut (Markdown) potentiellement porteur de DCP.

    Returns:
        Le texte avec les entités sensibles remplacées par des marqueurs
        (`<PERSON>`, `<EMAIL_ADDRESS>`, ...). Une chaîne vide en entrée renvoie
        une chaîne vide.
    """
    if not text or not text.strip():
        return text

    analyzer, anonymizer = _engines()
    results = analyzer.analyze(
        text=text,
        entities=_ENTITIES,
        language=settings.presidio_lang,
    )
    return anonymizer.anonymize(text=text, analyzer_results=results).text
