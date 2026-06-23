# Architecture Multi-Agents CrewAI - Veille Événementielle (IA Santé & Légal 2026)

Ce document définit la feuille de route de l'architecture multi-agents basée sur **CrewAI** et propulsée exclusivement par l'API d'**Anthropic (Claude 4.6 Sonnet)**.

## 1. L'infrastructure cloud Anthropic

*   **Choix du Modèle :** `claude-3-5-sonnet-20240620` (ou version la plus récente). C'est le compromis parfait entre intelligence contextuelle, vitesse d'exécution et rapport coût/performance.
*   **Configuration de l'API :** Utilisation de l'intégration CrewAI (`ChatAnthropic`). La clé `ANTHROPIC_API_KEY` sera stockée et gérée de manière sécurisée via un fichier `.env` local.
*   **Gestion des Tokens :** Claude 3.5 Sonnet dispose d'une fenêtre de contexte massive de 200k tokens. Néanmoins, un système de suivi et de troncature (chunking) préventive sera mis en place pour maîtriser le budget API lors de l'ingestion de sites web entiers.

## 2. Le pipeline de données sécurisé (RGPD Compliant)

Le flux de données se décompose en trois phases critiques pour garantir la conformité RGPD avant que toute donnée ne quitte le Mac M1 :

1.  **Scraping via l'API Firecrawl :** Utilisation de Firecrawl pour contourner les protections anti-bot et récupérer le contenu brut des sites événementiels directement dans un format **Markdown propre**, idéal pour l'ingestion LLM.
2.  **Anonymisation Locale Stricte (Microsoft Presidio) :** Les données récupérées par Firecrawl passent par un module de traitement hébergé localement sur le Mac M1, basé sur **Microsoft Presidio**. Presidio analyse le texte et expurge toute Donnée à Caractère Personnel (DCP : noms, adresses email, téléphones) avant la transmission.
3.  **Appel LLM Sécurisé :** Seul le texte Markdown anonymisé est transmis à l'API d'Anthropic pour traitement par les agents.

## 3. La définition des deux agents Claude

### Agent 1 : Le Chercheur de niche (Niche Researcher)
*   **Rôle :** Identifier, scraper et filtrer à la source les événements émergents, salons professionnels et webinaires confidentiels programmés pour l'année 2026 dans les écosystèmes de la Santé Digitale et de la LegalTech.
*   **Backstory & Prompt :** "Tu es un documentaliste technologique de pointe. Ton but est d'extraire la substantifique moelle d'un ensemble de plannings bruts, en excluant le bruit commercial et en te concentrant sur l'innovation IA réelle."
*   **Outils fournis :** Outil de recherche Web (Tavily/Serper), Outils intégrés Firecrawl.

### Agent 2 : L'Analyste/Rédacteur (Analyst & Writer)
*   **Rôle :** Consolider les trouvailles du Chercheur, valider l'adéquation stratégique avec les thématiques cibles (IA Santé, IA Légal) et rédiger le reporting Markdown final.
*   **Backstory & Prompt :** "Tu es un analyste stratégique rigoureux. Tu transformes des listes d'événements disparates en une veille technologique et stratégique actionnable pour les décideurs."

## 4. Le contrôle de fiabilité indirect

Puisque nous déléguons la synthèse au LLM à distance, un contrôle de fiabilité (anti-hallucination) sera mis en place spécifiquement pour certifier les **dates** et les **URL** générées par l'IA :
*   **Directive de Prompting (Strict Parsing) :** Les instructions système forceront Claude à renvoyer textuellement l'URL et les dates exactes trouvées dans le contexte injecté. Si l'information est absente, l'agent devra obligatoirement mentionner "Information non fournie au lieu de l'extrapoler.
*   **Rétro-vérification Locale (Sanity Check) :** Le résultat final json/markdown généré par Claude subit une passe regex/Python en local pour valider que chaque URL ressortie par le LLM est bien présente de manière identique dans le Markdown original issu de Firecrawl, avant l'injection vers le livrable.

## 5. Livrables : Tableau de Reporting

### A. Structure du Tableau Markdown de Reporting
Le format de sortie final généré par l'Analyste respectera cette structure :

| Date & Lieu | Événement | Secteur | Thème IA 2026 | Poids Stratégique (1-5) | Lien Source / Inscription |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *Avril 2026 - Paris* | *HealthTech AI Summit* | *IA Santé* | *Diagnostic prédictif* | *4* | *[Lien](#)* |
| *Juin 2026 - Londres* | *Legal Prompting Conf* | *IA Légal* | *Automatisation contrats* | *3* | *[Lien](#)* |