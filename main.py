"""Point d'entrée : exécute la veille déterministe et la rétro-vérification locale.

L'extraction est déterministe (Python, sans LLM) : à partir des pistes pré-collectées
(requêtes-graines), les dates/secteurs/poids sont calculés par regex et mots-clés.
C'est nettement plus fiable qu'un modèle local 3B (qui perd les dates et ignore des
salons majeurs). cf. src/extraction.py.

Usage :
    python main.py
    python main.py --debut 2026-04-01 --fin 2026-06-30
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from src.extraction import build_report_from_events
from src.tools import collect_seed_events
from src.verification import verify_urls

_OUTPUT_FILE = Path("rapport_veille_2026.md")


def _parse_date(valeur: str) -> date:
    """Convertit une chaîne YYYY-MM-DD en `date` pour argparse.

    Args:
        valeur: Date au format ISO (YYYY-MM-DD).

    Returns:
        L'objet `date` correspondant.

    Raises:
        argparse.ArgumentTypeError: Si le format est invalide.
    """
    try:
        return datetime.strptime(valeur, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Date invalide « {valeur} » : format attendu YYYY-MM-DD."
        ) from exc


def _parse_args() -> argparse.Namespace:
    """Définit et lit les arguments CLI (plage de dates optionnelle)."""
    parser = argparse.ArgumentParser(
        description="Veille événementielle IA Santé & Légal (extraction déterministe)."
    )
    parser.add_argument(
        "--debut", type=_parse_date, help="Date de début incluse (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--fin", type=_parse_date, help="Date de fin incluse (YYYY-MM-DD)."
    )
    args = parser.parse_args()
    if bool(args.debut) ^ bool(args.fin):
        parser.error("--debut et --fin doivent être fournis ensemble.")
    if args.debut and args.fin and args.debut > args.fin:
        parser.error("--debut doit être antérieure ou égale à --fin.")
    return args


def main() -> None:
    """Collecte les graines, construit le rapport déterministe, puis l'audite."""
    args = _parse_args()
    debut_iso = args.debut.isoformat() if args.debut else None
    fin_iso = args.fin.isoformat() if args.fin else None
    annee = args.debut.year if args.debut else 2026

    # 1) Découverte déterministe : pistes ciblées (graines) collectées localement.
    events = collect_seed_events(year=annee)
    # 2) Extraction déterministe : dates (regex) + secteurs (mots-clés) + poids.
    resultat = build_report_from_events(events, args.debut, args.fin)
    report = str(resultat["report"])
    _OUTPUT_FILE.write_text(report, encoding="utf-8")

    if args.debut and args.fin:
        print("\n" + "-" * 70)
        print(f"VEILLE [{debut_iso} → {fin_iso}] (extraction déterministe, garder + flaguer)")
    else:
        print("\n" + "-" * 70)
        print("VEILLE 2026 (extraction déterministe)")
    print(f"  Événements retenus     : {len(resultat['retenues'])}")
    if resultat["flaguees"]:
        print(f"  ⚠️  À vérifier (date)   : {len(resultat['flaguees'])}")
        for titre in resultat["flaguees"]:
            print(f"      - {titre}")
    if resultat["ecartees"]:
        print(f"  Écartés (hors plage)   : {len(resultat['ecartees'])}")
        for titre in resultat["ecartees"]:
            print(f"      - {titre}")
    if resultat["bruit"]:
        print(f"  Écartés (hors sujet)   : {len(resultat['bruit'])}")
    print("-" * 70)

    print("\n" + "=" * 70)
    print("RAPPORT DE VEILLE GÉNÉRÉ")
    print("=" * 70)
    print(report)

    # Rétro-vérification anti-hallucination : chaque URL du livrable doit provenir
    # du corpus source réellement collecté (titres + URL + snippets des graines).
    source_corpus = "\n".join(
        f"{ev['title']} {ev['url']} {ev.get('snippet', '')}" for ev in events
    )
    audit = verify_urls(report, source_corpus)

    print("\n" + "-" * 70)
    print("CONTRÔLE DE FIABILITÉ (anti-hallucination)")
    print(f"  URL vérifiées dans le corpus source : {len(audit['verified'])}")
    if audit["suspect"]:
        print(f"  ⚠️  URL SUSPECTES (absentes du corpus, à arbitrer) :")
        for url in audit["suspect"]:
            print(f"      - {url}")
    else:
        print("  Aucune URL suspecte détectée.")
    print("-" * 70)

    if _OUTPUT_FILE.exists():
        print(f"\nLivrable écrit dans : {_OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
