"""Extraction déterministe du tableau de veille (sans dépendance au LLM).

Plutôt que de confier l'extraction à un modèle local 3B (peu fiable : il perd les
dates, retient du bruit, ignore des salons majeurs), on construit le tableau de
reporting directement en Python à partir des pistes pré-collectées (graines) :

    snippet de recherche  ──>  date (regex), secteur (mots-clés), poids (heuristique)

Les dates sont reprises *verbatim* du corpus source (anti-hallucination par
construction), et le secteur est déduit par mots-clés. Le résultat est un livrable
Markdown reproductible, qui ne perd aucun grand salon présent dans les graines.
"""

from __future__ import annotations

from datetime import date

from .verification import extract_date_label, parse_event_interval

# Marqueur d'une date imprécise à arbitrer manuellement (cohérent avec verification).
_FLAG = "⚠️ à vérifier"

# Mots-clés de classification sectorielle (déterministe). Un événement sans aucun
# mot-clé est considéré comme du bruit (ex : catalogue de cours) et écarté.
_KEYWORDS_SANTE = (
    "santé", "sante", "health", "médic", "medic", "soin", "hôpital", "hopital",
    "hospital", "pharma", "cliniq", "patient", "diagnostic", "biotech", "medtech",
    "healthtech", "médico", "medico", "e-santé", "esante",
)
_KEYWORDS_LEGAL = (
    "droit", "legal", "légal", "juridiq", "justice", "avocat", "contrat",
    "law", "compliance", "legaltech", "notaire", "conformité", "réglement",
)

# Salons phares : poids stratégique rehaussé d'office.
_FLAGSHIPS = (
    "santexpo", "vivatech", "healthtech", "paris healthcare", "medintechs",
    "legaltech", "big data", "transformations du droit",
)

# En-tête imposé du livrable (cf. CLAUDE.md §5).
_HEADER = (
    "| Date & Lieu | Événement | Secteur | Thème IA 2026 | Poids Stratégique (1-5) | Lien Source / Inscription |\n"
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
)


def classify_sector(texte: str) -> str | None:
    """Déduit le secteur (« IA Santé » / « IA Légal ») par mots-clés.

    Args:
        texte: Titre + snippet de l'événement, en minuscules ou non.

    Returns:
        « IA Santé », « IA Légal », ou None si aucun mot-clé reconnu (bruit).
    """
    bas = texte.lower()
    sante = any(k in bas for k in _KEYWORDS_SANTE)
    legal = any(k in bas for k in _KEYWORDS_LEGAL)
    if sante and not legal:
        return "IA Santé"
    if legal and not sante:
        return "IA Légal"
    if sante and legal:
        # Ambigu : on tranche sur le premier mot-clé rencontré dans le texte.
        idx_sante = min((bas.find(k) for k in _KEYWORDS_SANTE if k in bas), default=10**9)
        idx_legal = min((bas.find(k) for k in _KEYWORDS_LEGAL if k in bas), default=10**9)
        return "IA Santé" if idx_sante <= idx_legal else "IA Légal"
    return None


def _weight(titre: str, date_precise: bool) -> int:
    """Attribue un poids stratégique (1-5) par heuristique transparente.

    Args:
        titre: Titre de l'événement (détection des salons phares).
        date_precise: True si une date exploitable a été extraite.

    Returns:
        Un entier borné dans [1, 5].
    """
    poids = 3
    if any(f in titre.lower() for f in _FLAGSHIPS):
        poids += 1
    if date_precise:
        poids += 1
    return max(1, min(5, poids))


def build_report_from_events(
    events: list[dict[str, str]],
    date_debut: date | None = None,
    date_fin: date | None = None,
) -> dict[str, object]:
    """Construit le tableau de reporting Markdown de façon déterministe.

    Pour chaque piste : extraction de la date (verbatim) et du secteur, filtrage
    par plage (garder + flaguer les dates imprécises), calcul du poids. Les pistes
    sans secteur identifiable (bruit) sont écartées.

    Args:
        events: Pistes structurées `{title, url, snippet}` (graines).
        date_debut: Borne basse incluse de la plage, ou None (pas de filtrage).
        date_fin: Borne haute incluse de la plage, ou None.

    Returns:
        Dictionnaire `{"report", "retenues", "flaguees", "ecartees", "bruit"}`.
    """
    lignes: list[str] = []
    retenues: list[str] = []
    flaguees: list[str] = []
    ecartees: list[str] = []
    bruit: list[str] = []

    for ev in events:
        titre = ev["title"].strip()
        url = ev["url"].strip()
        contexte = f"{titre} {ev.get('snippet', '')}"

        secteur = classify_sector(contexte)
        if secteur is None:
            bruit.append(titre)
            continue

        label = extract_date_label(ev.get("snippet", "")) or "Information non fournie"
        intervalle = parse_event_interval(ev.get("snippet", ""))

        # Filtrage par plage : garder + flaguer (cohérent avec verification).
        flag = ""
        if date_debut and date_fin:
            if intervalle is None:
                flag = f"{_FLAG} "
                flaguees.append(titre)
            elif intervalle[0] <= date_fin and intervalle[1] >= date_debut:
                retenues.append(titre)
            else:
                ecartees.append(f"{titre} ({label})")
                continue
        else:
            retenues.append(titre)

        poids = _weight(titre, intervalle is not None)
        date_cellule = f"{flag}{label}".strip()
        lignes.append(
            f"| {date_cellule} | {titre} | {secteur} | Information non fournie "
            f"| {poids} | [Lien]({url}) |"
        )

    rapport = _HEADER + ("\n" + "\n".join(lignes) if lignes else "")
    return {
        "report": rapport,
        "retenues": retenues,
        "flaguees": flaguees,
        "ecartees": ecartees,
        "bruit": bruit,
    }
