"""Outils de fiabilité : parsing/validation de dates et contrôle anti-hallucination.

Deux rôles :
    * parsing de dates (FR/EN, jour ou mois) pour l'extraction et le filtrage par
      plage — `parse_event_interval`, `extract_date_label` ;
    * rétro-vérification locale : certifier que chaque URL du livrable final est
      bien présente, à l'identique, dans le corpus source réellement collecté
      (`verify_urls`). Une URL absente est signalée comme potentiellement hallucinée.
"""

from __future__ import annotations

import calendar
import re
from datetime import date

# Capture les URL http/https dans un texte Markdown.
_URL_RE = re.compile(r"https?://[^\s)\]\"'>]+")
# Ponctuation terminale à retirer (point final de phrase, virgule, etc.).
_TRAILING = ".,;:!?"

# Date ISO complète (YYYY-MM-DD) : la forme la plus précise et fiable.
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

# Noms de mois français ET anglais : le LLM local produit des formats hétérogènes
# (« 04 mai 2026 », « February 25, 2026 ») qu'il faut tous reconnaître pour ne pas
# écarter à tort un événement réellement dans la plage.
_MONTHS = {
    # Français
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
    "decembre": 12,
    # Anglais
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
_MONTH_NAMES = "|".join(sorted(_MONTHS, key=len, reverse=True))

# Date au jour près avec mois nommé : « 04 mai 2026 » ou « February 25, 2026 ».
_DAY_DMY_RE = re.compile(
    r"\b(\d{1,2})\s+(" + _MONTH_NAMES + r")\s+(\d{4})\b", re.IGNORECASE
)
_DAY_MDY_RE = re.compile(
    r"\b(" + _MONTH_NAMES + r")\s+(\d{1,2}),?\s+(\d{4})\b", re.IGNORECASE
)
# Date au mois près (« Avril 2026 », « May 2026 »).
_MONTH_DATE_RE = re.compile(
    r"\b(" + _MONTH_NAMES + r")\s+(\d{4})\b", re.IGNORECASE
)


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


def extract_date_label(text: str) -> str | None:
    """Renvoie la chaîne de date brute trouvée dans un texte (pour affichage).

    Contrairement à `parse_event_interval` (qui renvoie un intervalle calculé),
    cette fonction restitue le libellé exact repéré (« 19 to 21 May 2026 »,
    « 04 mai 2026 »…) afin de l'afficher tel quel dans le tableau de reporting.

    Args:
        text: Texte source (snippet de recherche, contenu scrapé…).

    Returns:
        Le libellé de date trouvé, ou None si aucun motif reconnu.
    """
    texte = text or ""
    # On privilégie un éventuel intervalle « 19 to 21 May 2026 » / « 19-21 mai 2026 ».
    plage = re.search(
        r"\b\d{1,2}\s*(?:-|–|au|to|et|&)\s*\d{1,2}\s+(?:" + _MONTH_NAMES + r")\s+\d{4}",
        texte,
        re.IGNORECASE,
    )
    if plage:
        return plage.group(0)
    for motif in (_ISO_DATE_RE, _DAY_DMY_RE, _DAY_MDY_RE, _MONTH_DATE_RE):
        trouve = motif.search(texte)
        if trouve:
            return trouve.group(0)
    return None


def parse_event_interval(text: str) -> tuple[date, date] | None:
    """Extrait l'intervalle de dates couvert par une cellule « Date & Lieu ».

    Plusieurs niveaux de précision sont reconnus, par ordre de priorité :
        * date ISO complète (YYYY-MM-DD) -> intervalle d'un seul jour ;
        * jour + mois nommé + année (« 04 mai 2026 », « February 25, 2026 »,
          FR ou EN) -> intervalle d'un seul jour ;
        * mois + année (« Avril 2026 », « May 2026 ») -> intervalle du mois entier.

    Toute date imprécise (« Printemps 2026 », « Information non fournie », année
    seule) renvoie None : elle sera écartée par le filtrage strict.

    Args:
        text: Contenu de la cellule date (premier champ d'une ligne du tableau).

    Returns:
        Le couple (début, fin) de l'intervalle, ou None si rien de parsable.
    """
    texte = text or ""

    iso = _ISO_DATE_RE.search(texte)
    if iso:
        return _jour_unique(int(iso[1]), int(iso[2]), int(iso[3]))

    dmy = _DAY_DMY_RE.search(texte)  # « 04 mai 2026 »
    if dmy:
        return _jour_unique(int(dmy[3]), _MONTHS[dmy[2].lower()], int(dmy[1]))

    mdy = _DAY_MDY_RE.search(texte)  # « February 25, 2026 »
    if mdy:
        return _jour_unique(int(mdy[3]), _MONTHS[mdy[1].lower()], int(mdy[2]))

    mois = _MONTH_DATE_RE.search(texte)  # « Avril 2026 »
    if mois:
        numero = _MONTHS[mois[1].lower()]
        annee = int(mois[2])
        dernier_jour = calendar.monthrange(annee, numero)[1]
        return (date(annee, numero, 1), date(annee, numero, dernier_jour))

    return None


def _jour_unique(annee: int, mois: int, jour: int) -> tuple[date, date] | None:
    """Construit un intervalle d'un seul jour, ou None si la date est invalide.

    Args:
        annee: Année (4 chiffres).
        mois: Numéro de mois (1-12).
        jour: Jour du mois.

    Returns:
        Le couple (jour, jour), ou None si la date n'existe pas (ex : 31 février).
    """
    try:
        d = date(annee, mois, jour)
    except ValueError:
        return None
    return (d, d)


def verify_urls(report: str, source_corpus: str) -> dict[str, list[str]]:
    """Vérifie que les URL du rapport existent dans le corpus source.

    Args:
        report: Livrable Markdown généré par l'extraction déterministe.
        source_corpus: Concaténation des pistes sources (titres + URL + snippets).

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
