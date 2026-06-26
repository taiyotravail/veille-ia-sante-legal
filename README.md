# Veille Événementielle IA Santé & Légal 2026 — Pipeline déterministe (local)

Pipeline de veille **100% local, open source et déterministe**, sans aucune clé API
ni service cloud. Il découvre des salons/conférences IA (Santé Digitale & LegalTech)
via DuckDuckGo, anonymise localement (RGPD), puis extrait un tableau de reporting
par règles Python explicites — **sans LLM**.

> **Zéro coût d'API · zéro donnée quittant le Mac · résultats reproductibles.**

## « Déterministe » : pourquoi pas d'agents IA ?

Le projet utilisait au départ deux **agents CrewAI** propulsés par un LLM local
(Ollama + `qwen2.5:3b`). Sur un Mac M1 8 Go, ce petit modèle s'est révélé trop peu
fiable : dates perdues, salons majeurs ignorés (ex : SantExpo), bruit retenu, et
résultats différents à chaque exécution.

L'extraction a donc été basculée en **pur Python déterministe** :

| | Agents LLM (abandonné) | Déterministe (actuel) |
| :--- | :--- | :--- |
| Cherche sur Internet | ✅ Oui | ✅ Oui (DuckDuckGo) |
| Choix des requêtes | L'IA improvise | Liste fixe curée (`SEED_QUERIES`) |
| Extraction date/secteur | L'IA « comprend » le texte | Règles regex + mots-clés |
| Reproductible | ❌ Non | ✅ Oui (mêmes entrées → mêmes sorties) |
| Peut halluciner | ⚠️ Oui | ❌ Non (dates/URL verbatim) |

On perd en « intelligence » contextuelle, on gagne en **fiabilité** — ce qui prime
ici, le modèle local échouant à la tâche.

## Pipeline

```
Requêtes-graines curées  ──►  DuckDuckGo (ddgs)  ──►  Presidio (local, RGPD)  ──►  Extraction déterministe
   12 requêtes fixes            recherche web            anonymisation             regex dates + mots-clés secteur
   (SantExpo, MedInTechs…)                                                                   │
                                                                                  Reporting Markdown
                                                                                             │
                                                          Rétro-vérification locale (URL ⊂ corpus source)
```

Chaque étape s'exécute localement. Les snippets sont **anonymisés (Presidio) avant**
tout traitement — voir [`src/tools.py`](src/tools.py).

## Fonctionnement

- **Découverte** ([`src/tools.py`](src/tools.py)) : 12 requêtes-graines curées couvrant
  les secteurs cibles et les salons phares. Pour chaque requête, on privilégie le
  résultat dont le *snippet* porte une date exploitable.
- **Extraction** ([`src/extraction.py`](src/extraction.py)) :
  - **Date** reprise *verbatim* par regex (ISO, jour+mois FR/EN, mois+année, intervalles) ;
  - **Secteur** déduit par mots-clés (« IA Santé » / « IA Légal ») ; le bruit (sans
    mot-clé sectoriel) est écarté ;
  - **Poids stratégique (1-5)** par heuristique transparente (salon phare, date précise).
- **Filtrage par dates** (optionnel) avec politique **« garder + flaguer »** : hors plage
  → écarté ; date imprécise → conservée mais flaguée `⚠️ à vérifier` (arbitrage humain).
- **Anti-hallucination** ([`src/verification.py`](src/verification.py)) : chaque URL du
  livrable doit exister à l'identique dans le corpus source réellement collecté.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download fr_core_news_lg   # modèle français requis par Presidio
```

> Aucune clé API, aucun LLM, aucun service à lancer. Le `.env` est facultatif
> (seule surcharge utile : `PRESIDIO_LANG`, défaut `fr`).

## Exécution

```bash
python main.py                                       # veille 2026 globale
python main.py --debut 2026-04-01 --fin 2026-06-30   # entre deux dates (bornes incluses)
```

Le livrable est écrit dans `rapport_veille_2026.md`. Le contrôle de fiabilité signale
toute URL absente du corpus source (potentielle hallucination → arbitrage humain).

## Tests

```bash
pytest
```

`test_verification.py` et `test_extraction.py` (logique pure) tournent sans dépendance ;
`test_anonymizer.py` est ignoré automatiquement si Presidio n'est pas installé.

## Structure

| Fichier | Rôle |
| :--- | :--- |
| [`src/config.py`](src/config.py) | Configuration centralisée (langue Presidio). |
| [`src/anonymizer.py`](src/anonymizer.py) | Anonymisation locale stricte (Presidio + spaCy `fr_core_news_lg` / RGPD). |
| [`src/tools.py`](src/tools.py) | Découverte par requêtes-graines curées (DuckDuckGo), snippets anonymisés. |
| [`src/extraction.py`](src/extraction.py) | Extraction déterministe : date (regex) + secteur (mots-clés) + poids. |
| [`src/verification.py`](src/verification.py) | Parsing de dates (FR/EN) + rétro-vérification anti-hallucination des URL. |
| [`main.py`](main.py) | Point d'entrée + CLI `--debut/--fin` + sanity check. |

## Sécurité & RGPD

- **Zéro cloud** : recherche, anonymisation et extraction s'exécutent intégralement
  sur le Mac M1. Aucune donnée ne sort de la machine.
- **Anonymisation avant traitement** : les DCP (noms, emails, téléphones) sont
  expurgées par Presidio **avant** tout traitement.
- **Aucune clé API** : pipeline entièrement open source et gratuit.
- **Anti-hallucination par construction** : dates et URL reprises *verbatim* du corpus
  source (jamais générées) ; une passe regex confronte les URL du livrable au corpus
  réellement collecté.
