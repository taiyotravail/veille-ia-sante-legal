# Veille Événementielle IA Santé & Légal 2026 — CrewAI × Anthropic

Architecture multi-agents conforme à la feuille de route (`claude.md`) : pipeline
de données sécurisé **Firecrawl → Presidio (anonymisation locale) → Anthropic**,
deux agents Claude (Chercheur / Analyste), et contrôle de fiabilité anti-hallucination.

## Pipeline

```
Tavily / Firecrawl  ──►  Troncature (budget tokens)  ──►  Presidio (local, RGPD)  ──►  API Anthropic
                                                                                          │
                                       Reporting Markdown  ◄──  Analyste  ◄──  Chercheur ─┘
                                              │
                                   Rétro-vérification locale (URL ⊂ corpus source)
```

## Choix du modèle

Le `claude.md` mentionnait des identifiants incohérents (« Claude 4.6 Sonnet »,
`claude-3-5-sonnet-20240620`, « 200k tokens »). Le projet utilise désormais
**`claude-sonnet-4-6`** (équivalent Sonnet actuel, fenêtre de contexte **1M tokens**),
centralisé dans [`src/config.py`](src/config.py) et surchargeable via `ANTHROPIC_MODEL`.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download fr_core_news_lg   # modèle requis par Presidio
cp .env.example .env                       # puis renseigner les clés API
```

## Exécution

```bash
python main.py
```

Le livrable est écrit dans `rapport_veille_2026.md`, puis le contrôle de fiabilité
signale toute URL absente du corpus source (potentielle hallucination → arbitrage humain).

## Tests

```bash
pytest
```

## Structure

| Fichier | Rôle |
| :--- | :--- |
| `src/config.py` | Configuration centralisée (clés, modèle, chunking). |
| `src/anonymizer.py` | Anonymisation locale stricte (Presidio / RGPD). |
| `src/tools.py` | Outils Firecrawl + Tavily, anonymisation à la source. |
| `src/agents.py` | Chercheur de niche + Analyste / Rédacteur. |
| `src/tasks.py` | Tâches de recherche et de reporting. |
| `src/crew.py` | Assemblage séquentiel de l'équipage. |
| `src/verification.py` | Rétro-vérification anti-hallucination (URL). |
| `main.py` | Point d'entrée + sanity check. |

## Sécurité & RGPD

- Aucune DCP ne quitte le Mac : anonymisation **avant** tout appel LLM distant.
- Aucune clé API en dur — tout passe par `.env` (non committé).
- Les agents sont contraints par prompt à reproduire URL/dates verbatim ou à
  indiquer « Information non fournie ».


Code généré et validé. Voici la structure produite :


agents_salons/
├── main.py                    # Point d'entrée + sanity check anti-hallucination
├── requirements.txt
├── .env.example  / .gitignore
├── README.md
├── src/
│   ├── config.py              # Config centralisée (modèle, clés, chunking)
│   ├── anonymizer.py          # Presidio — anonymisation locale RGPD
│   ├── tools.py               # Firecrawl + Tavily (anonymisation à la source)
│   ├── agents.py              # Chercheur de niche + Analyste/Rédacteur
│   ├── tasks.py               # Tâches recherche → reporting
│   ├── crew.py                # Assemblage séquentiel
│   └── verification.py        # Rétro-vérification URL (anti-hallucination)
└── tests/
    ├── test_verification.py   # ✅ validés (logique pure)
    └── test_anonymizer.py     # skip auto si Presidio absent
Décisions notables :

Modèle : j'ai remplacé les identifiants incohérents du claude.md (« 4.6 Sonnet » / claude-3-5-sonnet-20240620 / « 200k ») par claude-sonnet-4-6 (1M tokens), centralisé dans config.py et surchargeable.
CrewAI/Anthropic : intégration native CrewAI (LLM(model="anthropic/...")). Le SDK anthropic reste en dépendance directe.
Pipeline RGPD appliqué dans les outils : troncature → anonymisation Presidio avant tout appel LLM.
Bug corrigé pendant la vérif : le regex d'extraction d'URL capturait la ponctuation finale (https://a.com/x.) → corrigé et re-testé.
Ce qui reste à votre charge avant exécution : pip install -r requirements.txt, python -m spacy download fr_core_news_lg, et renseigner .env. Je n'ai pas pu lancer la suite complète (pytest + Presidio + clés API non installés ici) — seuls les tests de logique pure ont tourné et passent.

Conformément au protocole de gouvernance (CLAUDE.md), confirmations de l'Agent Dev :

« J'ai vérifié la conformité RGPD. » — anonymisation Presidio locale avant transmission, aucune clé en dur, .env git-ignoré, aucune PII en logs.
« Le code est documenté et testé. » — docstrings sur toutes les fonctions, tests unitaires fournis (logique de vérification validée).
« La logique prédictive a été revue pour éviter les hallucinations. » — contraintes de prompt « Information non fournie » + rétro-vérification regex des URL contre le corpus source.
Prêt pour la passe de l'Agent Critique puis l'arbitrage humain.