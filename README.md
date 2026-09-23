# Meeting Assistant

## Présentation

Meeting Assistant est une solution de prise de notes automatisée pour les réunions Jitsi.

L'application permet de :

- rejoindre automatiquement une réunion Jitsi ;
- récupérer les participants ;
- capturer les flux audio ;
- transcrire les échanges en temps réel ;
- analyser le contenu de la réunion grâce à un modèle de langage local ;
- générer un compte rendu structuré ;
- exporter les résultats au format PDF et DOCX.

L'objectif principal est d'automatiser la production de comptes rendus tout en garantissant la confidentialité des données grâce à une infrastructure entièrement locale.

---

# Fonctionnalités principales

## Gestion des réunions

- Création d'une nouvelle réunion
- Connexion automatique à une salle Jitsi
- Arrêt contrôlé de la réunion
- Sauvegarde de l'état de la réunion

## Gestion des participants

- Détection automatique des participants
- Mise à jour dynamique de la liste
- Personnalisation des noms affichés

## Transcription

- Capture audio temps réel
- Transcription automatique via Faster-Whisper
- Mise à jour continue de la transcription

## Analyse

- Analyse locale avec Ollama
- Génération de :
  - résumé
  - sujets abordés
  - décisions
  - actions à réaliser
  - questions ouvertes

## Export

- Export PDF
- Export DOCX

---

# Architecture générale

```text
GUI (PySide6)
       │
       ▼
MeetingController
       │
 ┌─────┼──────────┬──────────┐
 ▼     ▼          ▼          ▼
Jitsi Whisper   Ollama   Exporter
Bot
       │
       ▼
MeetingState
```

Le système repose sur une architecture modulaire où chaque composant possède une responsabilité clairement définie.

---

# Technologies utilisées

## Interface utilisateur

- PySide6

## Automatisation navigateur

- Playwright

## Réunion vidéo

- Jitsi Meet
- Jitsi IFrame API

## Transcription

- Faster-Whisper

## Intelligence artificielle

- Ollama
- Qwen3

## Export

- PDF
- DOCX

## Langage

- Python 3

---

# Pipeline de traitement

```text
Réunion Jitsi
      │
      ▼
Participants ─────────────► participants.json
      │
      ▼
Audio
      │
      ▼
PCM
      │
      ▼
Faster-Whisper
      │
      ▼
live_transcript.txt
      │
      ▼
Analyzer
      │
      ▼
Ollama
      │
      ▼
MeetingState
      │
      ▼
meeting_state.json
      │
 ┌────┴─────┐
 ▼          ▼
GUI      Exporter
            │
       ┌────┴────┐
       ▼         ▼
      PDF      DOCX
```

---

# Structure du projet

```text
meeting-assistant/
│
├── main.py
├── config.py
├── meeting_controller.py
├── meeting_state.py
├── exporter.py
├── jitsi-bot.py
│
├── gui/
│   └── gui.py
│
├── realtime/
│   └── jitsi_transcriber.py
│
├── transcription/
│   └── analyzer.py
│
├── jitsi_client/
│   ├── index.html
│   └── server.py
│
├── recordings/
├── docs/
└── tests/
```

---

# Installation

## Cloner le dépôt

```bash
git clone <repository-url>
cd meeting-assistant
```

## Créer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

## Installer les dépendances

```bash
pip install -r requirements.txt
```

## Installer Playwright

```bash
playwright install
```

---

# Lancement

## Exécution complète

```bash
python main.py
```

## Vérification de l'environnement

```bash
python --version
ollama list
git status
```

---

# Fichiers générés

## participants.json

Liste des participants détectés.

## live_transcript.txt

Transcription en temps réel.

## meeting_state.json

Compte rendu structuré généré par le système.

## bot.log

Journal d'exécution du bot.

---

# Organisation de la documentation technique

Afin d'améliorer la maintenabilité, la compréhension et l'évolution de la solution, une documentation technique structurée a été mise en place.

La documentation est organisée en plusieurs fichiers complémentaires, chacun répondant à un objectif précis.

```text
docs/
├── architecture.md
├── pipeline.md
├── components.md
├── data_formats.md
└── development.md
```

Ces documents permettent de décrire respectivement :

| Document | Description |
|-----------|-------------|
| architecture.md | Architecture globale du système |
| pipeline.md | Cycle complet de traitement des données |
| components.md | Description détaillée des composants logiciels |
| data_formats.md | Formats et structures de données |
| development.md | Guide de développement et maintenance |

---

## 1. architecture.md

Ce document fournit une vue d'ensemble de la solution.

Il décrit :

- les objectifs fonctionnels ;
- les objectifs techniques ;
- l'architecture générale ;
- les interactions entre composants ;
- les processus d'exécution ;
- les principes architecturaux ;
- les limitations connues.

Les principaux composants présentés sont :

- GUI PySide6
- MeetingController
- Jitsi Bot
- Faster-Whisper
- Ollama
- MeetingState
- Exporter

Le document explique également comment ces composants collaborent afin de produire le compte rendu final.

---

## 2. pipeline.md

Ce document décrit le cycle complet des données.

Il détaille :

### Initialisation

- création de la réunion ;
- réinitialisation des fichiers ;
- démarrage du bot.

### Connexion Jitsi

- chargement du client local ;
- connexion au serveur Jitsi ;
- initialisation de l'API.

### Gestion des participants

- récupération des identifiants ;
- récupération des noms ;
- mise à jour de participants.json.

### Traitement audio

- récupération des flux ;
- conversion PCM ;
- transmission au transcripteur.

### Transcription

- traitement par Faster-Whisper ;
- génération de live_transcript.txt.

### Analyse

- construction du prompt ;
- appel du modèle Ollama ;
- création du MeetingState.

### Finalisation

- sauvegarde ;
- export PDF ;
- export DOCX.

Le document présente également les mécanismes de récupération après erreur :

- indisponibilité Jitsi ;
- erreur de transcription ;
- erreur Ollama ;
- JSON invalide.

---

## 3. components.md

Ce document est orienté code source.

Il décrit le rôle précis de chaque module du projet.

Les principaux composants documentés sont :

### main.py

Point d'entrée de l'application.

### meeting_controller.py

Coordination du cycle de vie des réunions.

### meeting_state.py

Modèle central représentant l'état d'une réunion.

### jitsi-bot.py

Interaction avec Jitsi et Playwright.

### realtime/jitsi_transcriber.py

Transcription audio.

### transcription/analyzer.py

Analyse via Ollama.

### gui/gui.py

Interface utilisateur.

### exporter.py

Export PDF et DOCX.

Pour chaque composant, la documentation précise :

- responsabilités ;
- dépendances ;
- interfaces ;
- limites ;
- comportements attendus.

---

## 4. data_formats.md

Ce document définit toutes les structures de données utilisées par le système.

Les formats documentés incluent :

### participants.json

Informations relatives aux participants.

### live_transcript.txt

Transcription brute.

### meeting_state.json

Compte rendu structuré.

### Réponse Ollama

Format JSON attendu du modèle.

### PCM Audio

Structure et transmission des données audio.

### bot.log

Format des journaux d'exécution.

Le document définit également :

- les conventions d'encodage UTF-8 ;
- les règles de validation ;
- les contraintes de cohérence ;
- les exigences de fidélité des informations.

---

## 5. development.md

Guide destiné aux développeurs.

Il couvre :

### Environnement

- Ubuntu
- Python
- Virtualenv
- Ollama
- Playwright

### Installation

- récupération du dépôt ;
- création de l'environnement ;
- installation des dépendances.

### Configuration

- paramètres Jitsi ;
- paramètres Ollama ;
- chemins ;
- ports.

### Exécution

- démarrage complet ;
- exécution des composants individuellement.

### Tests

- tests unitaires ;
- tests d'intégration ;
- validation fonctionnelle.

### Diagnostic

- utilisation des logs ;
- vérification des fichiers intermédiaires ;
- résolution des erreurs courantes.

### Journalisation

Évolution progressive vers :

```python
logging.debug()
logging.info()
logging.warning()
logging.error()
```

### Gestion Git

- branche principale stable ;
- branches de développement ;
- modifications progressives ;
- validation continue.

Le document rappelle également les règles de développement :

- respecter la séparation des responsabilités ;
- éviter la duplication de configuration ;
- effectuer des changements incrémentaux ;
- tester avant fusion ;
- ne jamais versionner des données confidentielles.

---

# Principes de conception

Le projet repose sur plusieurs principes fondamentaux :

## Séparation des responsabilités

Chaque composant possède une fonction unique.

## Source unique 

L'objet MeetingState représente l'état officiel de la réunion.

## Traitement local

Les données restent sur l'infrastructure locale.

## Modularité

Les moteurs de transcription ou d'analyse peuvent être remplacés indépendamment.

## Maintenabilité

La documentation et la structure du projet facilitent les évolutions futures.

---

# Roadmap

Améliorations envisagées :

- transcription mieux structurée ;
- architecture événementielle ;
- amélioration de la journalisation ;
- tests automatisés complets ;
- enrichissement des exports;
- amelioration du rendu des exports;
- amelioraion de l'interface graphique;
- tester avec LLM local de l'entreprise.

---

# Auteurs

Projet développé dans le cadre du projet Meeting Assistant.

Maroua Ouldzmirli / ESI 