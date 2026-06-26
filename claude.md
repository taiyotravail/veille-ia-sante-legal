# Architecture d'Extraction Déterministe - Veille Événementielle (IA Santé & Légal 2026)

Ce document définit l'architecture du pipeline de veille, **100% local, open source et déterministe** (sans LLM dans le chemin principal).

> **Historique :** une première version reposait sur une architecture multi-agents **CrewAI + Ollama (qwen2.5:3b)**. Elle a été abandonnée : le modèle local 3B était trop peu fiable pour l'extraction (dates perdues, salons majeurs ignorés comme SantExpo, bruit retenu, lignes vides en cas de surcharge de contexte). L'extraction a été basculée en **pur Python déterministe**, nettement plus robuste et reproductible sur un Mac M1 8 Go.

## 1. Infrastructure locale (zéro dépendance lourde)

*   **Aucun LLM, aucun service cloud, aucune clé API.** Le pipeline tourne intégralement en Python local. Zéro coût, confidentialité complète (zéro donnée quittant le Mac M1), résultats reproductibles.
*   **Dépendances :** `ddgs` (recherche DuckDuckGo), Microsoft **Presidio** + spaCy `fr_core_news_lg` (anonymisation RGPD), `python-dotenv`, `pytest`. Cf. `requirements.txt`.

## 2. Pipeline de données sécurisé (RGPD Compliant, Zero-Cloud)

Le flux se décompose en trois phases, garantissant conformité RGPD et confidentialité intégrale :

1.  **Découverte par requêtes-graines curées (sans clé API) :** La découverte passe par **DuckDuckGo** (`ddgs`), en pur Python local. Une liste de **requêtes-graines curées** (`SEED_QUERIES` dans `src/tools.py`) couvre les secteurs cibles ET les salons phares connus (SantExpo, Paris Healthcare Week, MedInTechs, Big Data & AI Paris, Village de la LegalTech, Transformations du droit…). Cette amorce déterministe garantit la couverture des grands salons sans dépendre de l'« initiative » d'un modèle. Pour chaque requête, on privilégie le résultat dont le *snippet* porte une date exploitable.
2.  **Anonymisation Locale Stricte (Microsoft Presidio) :** Chaque snippet récupéré est expurgé localement (DCP : noms, emails, téléphones…) via **Presidio** + spaCy, configuré pour la langue cible (`PRESIDIO_LANG`, défaut `fr`). Cf. `src/anonymizer.py`.
3.  **Extraction déterministe 100% locale :** Les pistes anonymisées sont transformées en tableau de reporting par regex (dates) et mots-clés (secteur), sans aucun appel LLM. Cf. `src/extraction.py`.

## 3. L'extraction déterministe (`src/extraction.py`)

Remplace les deux agents CrewAI par une logique Python testable :

*   **Date :** extraite *verbatim* du snippet par regex (`extract_date_label` / `parse_event_interval` dans `src/verification.py`). Formats reconnus : ISO `YYYY-MM-DD`, jour + mois nommé (FR/EN), mois + année, intervalles (« 19 au 21 mai 2026 »). Anti-hallucination par construction : aucune date n'est inventée.
*   **Secteur :** déduit par mots-clés (`classify_sector`) → « IA Santé » / « IA Légal ». Une piste sans mot-clé sectoriel est considérée comme du bruit et écartée.
*   **Poids stratégique (1-5) :** heuristique transparente (`_weight`) : base 3, +1 si salon phare, +1 si date précise.
*   **Filtrage par plage de dates :** optionnel via `--debut/--fin` (CLI). Politique **« garder + flaguer »** (cf. §4).

## 4. Contrôle de fiabilité (anti-hallucination local)

*   **Dates verbatim :** reprises telles quelles du corpus source ; jamais extrapolées. Absence de date → « Information non fournie ».
*   **Politique de dates « garder + flaguer »** (`build_report_from_events`) :
    - date précise **dans** la plage → conservée ;
    - date précise **hors** plage → écartée (réellement hors sujet) ;
    - date **imprécise / absente** → **conservée mais flaguée « ⚠️ à vérifier »** pour arbitrage humain, afin de ne perdre aucun grand salon dont la date n'apparaît pas dans le snippet (ex : SantExpo).
*   **Rétro-vérification des URL (`verify_urls`)** : chaque URL du livrable doit être présente, à l'identique, dans le corpus source réellement collecté (titres + URL + snippets). Une URL absente est signalée comme suspecte.
*   **Tests :** chaque brique (parsing de dates, classification, filtrage, vérification d'URL) est couverte par des tests unitaires (`tests/`).

## 5. Livrables : Tableau de Reporting

### A. Exécution

```bash
python main.py                                  # veille 2026 globale
python main.py --debut 2026-04-01 --fin 2026-06-30   # entre deux dates
```

Le livrable est écrit dans `rapport_veille_2026.md`.

### B. Structure du Tableau Markdown de Reporting

| Date & Lieu | Événement | Secteur | Thème IA 2026 | Poids Stratégique (1-5) | Lien Source / Inscription |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *19 au 21 mai 2026* | *SantExpo 2026* | *IA Santé* | *Information non fournie* | *5* | *[Lien](#)* |
| *⚠️ à vérifier Information non fournie* | *MedInTechs 2026* | *IA Santé* | *Information non fournie* | *4* | *[Lien](#)* |

> Arbitrage humain obligatoire avant diffusion : les lignes « ⚠️ à vérifier » et la pertinence stratégique finale relèvent du décideur.
