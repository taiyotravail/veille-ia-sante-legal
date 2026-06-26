"""Découverte d'événements 100% open source via DuckDuckGo (sans clé API).

La recherche passe par DuckDuckGo (`ddgs`), en pur Python et exécutée localement.
Les résultats (titre / URL / snippet) sont anonymisés localement (Presidio) avant
tout traitement, par construction RGPD.

Les requêtes-graines curées garantissent la couverture des grands salons (IA Santé
et LegalTech) indépendamment d'un modèle local : la découverte ne dépend plus de
l'« initiative » d'un LLM, mais d'une liste déterministe enrichie par recherche.
"""

from __future__ import annotations

from ddgs import DDGS

from .anonymizer import anonymize
from .verification import extract_date_label

# Requêtes-graines curées : garantissent la couverture des grands salons et des
# secteurs cibles. {year} est substitué à l'exécution.
SEED_QUERIES: tuple[str, ...] = (
    # IA Santé — secteur + salons phares connus
    "salon IA santé numérique France {year}",
    "congrès santé digitale intelligence artificielle {year}",
    "SantExpo {year} dates programme",
    "Paris Healthcare Week {year}",
    "MedInTechs {year} salon innovation santé",
    "HealthTech AI summit {year} Europe",
    "Big Data AI Paris {year} santé",
    # IA Légal / LegalTech — secteur + salons phares connus
    "salon LegalTech France {year}",
    "congrès intelligence artificielle droit juridique {year}",
    "Village de la LegalTech {year}",
    "Transformations du droit {year} IA",
    "LegalTech summit {year} Europe contrats IA",
)

# Paramètres de collecte. Une seule piste par requête-graine (couverture large des
# secteurs), mais on inspecte plusieurs résultats pour PRIVILÉGIER celui dont le
# snippet porte une date exploitable (meilleur recall de dates).
_SEED_PER_QUERY = 1
_SEED_CANDIDATES_PER_QUERY = 4
_SEED_MAX_LEADS = 12
_SEED_SNIPPET_CHARS = 300


def collect_seed_events(
    year: int = 2026,
    per_query: int = _SEED_PER_QUERY,
    max_leads: int = _SEED_MAX_LEADS,
) -> list[dict[str, str]]:
    """Exécute les requêtes-graines et renvoie les pistes en structuré.

    Chaque piste est un dict `{title, url, snippet}` (snippet anonymisé) prêt à
    être parsé en Python par l'extraction déterministe, sans passer par un LLM.
    Parmi les candidats d'une même requête, on retient en priorité ceux dont le
    snippet porte une date exploitable.

    Args:
        year: Année cible injectée dans les requêtes.
        per_query: Nombre de pistes retenues par requête-graine.
        max_leads: Nombre total maximum de pistes retournées.

    Returns:
        Liste de dicts `{title, url, snippet}`, dédupliquée par URL.
    """
    vues: set[str] = set()
    evenements: list[dict[str, str]] = []
    for gabarit in SEED_QUERIES:
        if len(evenements) >= max_leads:
            break
        requete = gabarit.format(year=year)
        try:
            resultats = DDGS().text(requete, max_results=_SEED_CANDIDATES_PER_QUERY)
        except Exception:  # noqa: BLE001 — une requête qui échoue ne bloque pas l'amorce
            continue

        # Parmi les candidats de cette requête, on retient en priorité ceux dont le
        # snippet porte une date exploitable (les autres servent de repli).
        candidats = [r for r in (resultats or []) if (r.get("href") or "") not in vues]
        candidats.sort(
            key=lambda r: extract_date_label(r.get("body", "")) is None  # date-bearing d'abord
        )
        for item in candidats[:per_query]:
            url = item["href"]
            vues.add(url)
            evenements.append(
                {
                    "title": item.get("title", "Sans titre"),
                    "url": url,
                    "snippet": anonymize((item.get("body", "") or "")[:_SEED_SNIPPET_CHARS]),
                }
            )
    return evenements
