# Architecture Multi-Agents CrewAI - Veille Événementielle (IA Santé & Légal 2026)

Ce document définit la feuille de route de l'architecture multi-agents basée sur **CrewAI** et propulsée par **Ollama avec le modèle qwen2.5:3b**.

## 1. L'infrastructure locale (Ollama + qwen2.5:3b)

*   **Choix du Modèle :** `qwen2.5:3b` exécuté localement via **Ollama**. Ce modèle est retenu car il **supporte nativement le tool calling** (function calling) requis par CrewAI, tout en restant léger (~1.9 Go) — adapté à un Mac M1 8 Go où des modèles plus lourds (llama3.1:8b) provoqueraient du swap. Cette approche garantit zéro coût d'API, confidentialité complète (zéro donnée quittant le Mac M1) et contrôle total sur le pipeline.
    *   **Note de compatibilité :** tout modèle ne supporte pas le tool calling. `openchat` et `phi4-mini` échouent ou n'appellent pas les outils CrewAI ; le modèle choisi **doit** exposer la capacité `tools` côté Ollama.
*   **Configuration de Ollama :** Installation via Homebrew (`brew install ollama`), puis `ollama pull qwen2.5:3b` et `ollama serve` en arrière-plan. Intégration via la classe `LLM` de CrewAI (LiteLLM), configurée dans `src/agents.py`.
*   **Gestion des Tokens :** Un système de troncature (`MAX_CHARS_PER_PAGE`, défaut 20000) limite le contexte injecté par page scrapée pour ne pas surcharger le modèle local.

## 2. Le pipeline de données sécurisé (RGPD Compliant, Zero-Cloud)

Le flux de données se décompose en trois phases pour garantir la conformité RGPD et la confidentialité intégrale (zéro transmission cloud) :

1.  **Recherche & Scraping 100% open source (sans clé API) :** La découverte de sources passe par **DuckDuckGo** (`ddgs`) et l'extraction de contenu par **trafilatura** — tous deux en pur Python, exécutés localement, sans navigateur ni service cloud propriétaire. trafilatura extrait le contenu principal des pages en **Markdown propre**, idéal pour l'ingestion LLM. (Firecrawl et Tavily ont été abandonnés pour supprimer toute dépendance à des API payantes.)
2.  **Anonymisation Locale Stricte (Microsoft Presidio) :** Les données récupérées passent par un module de traitement hébergé localement sur le Mac M1, basé sur **Microsoft Presidio** couplé au modèle spaCy français `fr_core_news_lg`. Presidio analyse le texte et expurge toute Donnée à Caractère Personnel (DCP : noms, adresses email, téléphones). Le moteur NLP est configuré explicitement pour la langue cible (`PRESIDIO_LANG`, défaut `fr`).
3.  **Traitement LLM 100% Local :** Le texte Markdown anonymisé est traité entièrement localement via qwen2.5:3b/Ollama. Aucune donnée ne quitte le Mac M1. Le pipeline reste sécurisé et conforme RGPD par construction.

## 3. La définition des deux agents CrewAI

### Agent 1 : Le Chercheur de niche (Niche Researcher)
*   **Rôle :** Identifier, scraper et filtrer à la source les événements émergents, salons professionnels et webinaires confidentiels programmés pour l'année 2026 dans les écosystèmes de la Santé Digitale et de la LegalTech.
*   **Backstory & Prompt :** "Tu es un documentaliste technologique de pointe. Ton but est d'extraire la substantifique moelle d'un ensemble de plannings bruts, en excluant le bruit commercial et en te concentrant sur l'innovation IA réelle."
*   **LLM** : qwen2.5:3b via Ollama (classe `LLM` de CrewAI).
*   **Outils fournis :** `web_search` (recherche DuckDuckGo via `ddgs`) et `web_scrape` (extraction trafilatura), définis dans `src/tools.py`.

### Agent 2 : L'Analyste/Rédacteur (Analyst & Writer)
*   **Rôle :** Consolider les trouvailles du Chercheur, valider l'adéquation stratégique avec les thématiques cibles (IA Santé, IA Légal) et rédiger le reporting Markdown final.
*   **Backstory & Prompt :** "Tu es un analyste stratégique rigoureux. Tu transformes des listes d'événements disparates en une veille technologique et stratégique actionnable pour les décideurs."
*   **LLM** : qwen2.5:3b via Ollama (classe `LLM` de CrewAI).

## 4. Le contrôle de fiabilité strict (anti-hallucination local)

Puisque nous utilisons un modèle local (qwen2.5:3b) potentiellement moins robuste qu'un modèle cloud, un contrôle de fiabilité renforcé sera mis en place pour certifier les **dates**, les **URL** et la cohérence des événements :
*   **Directive de Prompting (Strict Parsing)** : Les prompts des agents forceront une extraction textuelle stricte des URL et dates exactes trouvées dans le contexte injecté. Si l'information est absente, l'agent devra obligatoirement mentionner "Information non fournie" au lieu d'extrapoler ou d'halluciner.
*   **Rétro-vérification Locale (Sanity Check)** : Le résultat final json/markdown généré par les agents subit une passe regex/Python en local pour valider que :
    - Chaque URL ressortie par le LLM est bien présente de manière identique dans le corpus source scrapé (trafilatura) / les résultats de recherche (DuckDuckGo).
    - Les dates respectent un format cohérent (YYYY-MM-DD ou "Mois YYYY").
    - Les événements font sens dans leur secteur respectif.
*   **Logique de Fallback** : Si une hallucination est détectée, l'événement est flaggé pour vérification manuelle avant injection au livrable.

## 5. Livrables : Tableau de Reporting

### A. Structure du Tableau Markdown de Reporting
Le format de sortie final généré par l'Analyste respectera cette structure :

| Date & Lieu | Événement | Secteur | Thème IA 2026 | Poids Stratégique (1-5) | Lien Source / Inscription |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *Avril 2026 - Paris* | *HealthTech AI Summit* | *IA Santé* | *Diagnostic prédictif* | *4* | *[Lien](#)* |
| *Juin 2026 - Londres* | *Legal Prompting Conf* | *IA Légal* | *Automatisation contrats* | *3* | *[Lien](#)* |