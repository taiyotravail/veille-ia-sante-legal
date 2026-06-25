# Veille Événementielle IA Santé & Légal 2026 — CrewAI × Ollama (local)

Architecture multi-agents conforme à la feuille de route ([`claude.md`](claude.md)) :
pipeline de données **100% local et open source**, sans aucune clé API ni service
cloud propriétaire. Deux agents CrewAI (Chercheur / Analyste) propulsés par un LLM
local via **Ollama**, anonymisation RGPD locale, et contrôle de fiabilité
anti-hallucination.

> **Zéro coût d'API · zéro donnée quittant le Mac · confidentialité par construction.**

## Pipeline

```
DuckDuckGo (ddgs)  ──►  trafilatura (Markdown)  ──►  Troncature  ──►  Presidio (local, RGPD)  ──►  Ollama (qwen2.5:3b)
   recherche               scraping               budget tokens        anonymisation              LLM 100% local
                                                                                                       │
                                              Reporting Markdown  ◄──  Analyste  ◄──  Chercheur ───────┘
                                                     │
                                          Rétro-vérification locale (URL ⊂ corpus source)
```

Chaque étape est exécutée localement sur le Mac M1. Le contenu scrapé est **tronqué
puis anonymisé (Presidio) avant** d'être transmis au LLM — voir [`src/tools.py`](src/tools.py).

## Choix du modèle

Le projet utilise **`qwen2.5:3b`** exécuté localement via Ollama : il supporte
nativement le *tool calling* requis par CrewAI tout en restant léger (~1.9 Go),
adapté à un Mac M1 8 Go.

> ⚠️ Tout modèle ne supporte pas le tool calling. `openchat` et `phi4-mini`
> échouent à appeler les outils CrewAI. Le modèle choisi **doit** exposer la
> capacité `tools` côté Ollama.

Le modèle est centralisé dans [`src/config.py`](src/config.py) et surchargeable via
la variable d'environnement `OLLAMA_MODEL`.

## Installation

### 1. Ollama + modèle local

```bash
brew install ollama
ollama pull qwen2.5:3b
ollama serve            # à laisser tourner en arrière-plan
```

### 2. Environnement Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download fr_core_news_lg   # modèle français requis par Presidio
cp .env.example .env                       # optionnel : surcharges (modèle, langue…)
```

> Le fichier `.env` est **facultatif** : aucune clé API n'est nécessaire. Il sert
> uniquement à surcharger les valeurs par défaut (`OLLAMA_MODEL`, `OLLAMA_BASE_URL`,
> `PRESIDIO_LANG`, `MAX_CHARS_PER_PAGE`).

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

Les tests de logique pure (`test_verification.py`) tournent sans dépendance ;
`test_anonymizer.py` est ignoré automatiquement si Presidio n'est pas installé.

## Structure

| Fichier | Rôle |
| :--- | :--- |
| [`src/config.py`](src/config.py) | Configuration centralisée (modèle Ollama, base URL, langue Presidio, chunking). |
| [`src/anonymizer.py`](src/anonymizer.py) | Anonymisation locale stricte (Presidio + spaCy `fr_core_news_lg` / RGPD). |
| [`src/tools.py`](src/tools.py) | Outils CrewAI : recherche DuckDuckGo (`web_search`) + scraping trafilatura (`web_scrape`), anonymisés à la source. |
| [`src/agents.py`](src/agents.py) | Chercheur de niche + Analyste / Rédacteur (LLM Ollama partagé). |
| [`src/tasks.py`](src/tasks.py) | Tâches de recherche et de reporting. |
| [`src/crew.py`](src/crew.py) | Assemblage séquentiel de l'équipage. |
| [`src/verification.py`](src/verification.py) | Rétro-vérification anti-hallucination (URL ⊂ corpus source). |
| [`main.py`](main.py) | Point d'entrée + sanity check. |

## Sécurité & RGPD

- **Zéro cloud** : recherche, scraping, anonymisation et inférence LLM s'exécutent
  intégralement sur le Mac M1. Aucune donnée ne sort de la machine.
- **Anonymisation avant traitement** : les DCP (noms, emails, téléphones) sont
  expurgées par Presidio **avant** que le contenu n'atteigne le LLM.
- **Aucune clé API** : le pipeline est entièrement open source et gratuit.
- **Anti-hallucination** : les agents sont contraints par prompt à reproduire
  URL/dates verbatim ou à indiquer « Information non fournie » ; une passe regex
  locale confronte ensuite les URL du livrable au corpus réellement scrapé.
