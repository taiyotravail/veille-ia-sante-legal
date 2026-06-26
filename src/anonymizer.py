"""Anonymisation locale stricte (RGPD) basée sur Microsoft Presidio.

Ce module s'exécute **localement sur le Mac M1**. Aucune Donnée à Caractère
Personnel (DCP) ne doit quitter la machine : tout texte issu de la recherche web
(titres, snippets) est expurgé ici (noms, emails, téléphones…) avant traitement.
"""

from __future__ import annotations

from functools import lru_cache

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

from .config import settings

# Modèle spaCy à charger selon la langue Presidio configurée. Doit être installé
# au préalable (ex: `python -m spacy download fr_core_news_lg`).
_SPACY_MODELS = {
    "fr": "fr_core_news_lg",
    "en": "en_core_web_lg",
}

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

    Le moteur NLP est explicitement configuré avec le modèle spaCy de la langue
    cible (`settings.presidio_lang`), sans quoi l'analyzer par défaut (anglais)
    ne dispose d'aucun recognizer pour le français. Les moteurs sont coûteux à
    charger ; on les met en cache pour toute la durée du processus.

    Returns:
        Le couple (analyzer, anonymizer).
    """
    lang = settings.presidio_lang
    model_name = _SPACY_MODELS.get(lang, _SPACY_MODELS["en"])
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": lang, "model_name": model_name}],
        }
    ).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[lang])
    return analyzer, AnonymizerEngine()


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
