"""Point d'entrée : exécute la veille et applique la rétro-vérification locale.

Usage :
    python main.py
"""

from __future__ import annotations

from pathlib import Path

from src.crew import build_crew
from src.verification import verify_urls

_OUTPUT_FILE = Path("rapport_veille_2026.md")


def main() -> None:
    """Lance l'équipage puis effectue le sanity check anti-hallucination."""
    crew = build_crew()
    result = crew.kickoff()
    report = str(result)

    print("\n" + "=" * 70)
    print("RAPPORT DE VEILLE GÉNÉRÉ")
    print("=" * 70)
    print(report)

    # Rétro-vérification : reconstitue le corpus source à partir des sorties de
    # tâches, puis confronte les URL du livrable au contenu réellement scrapé.
    source_corpus = "\n".join(
        str(getattr(t, "raw", "") or "") for t in getattr(result, "tasks_output", [])
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
