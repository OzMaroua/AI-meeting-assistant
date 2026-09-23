# Architecture du Système

## Présentation générale

Le projet consiste à développer un assistant intelligent capable d'automatiser la prise de notes et la génération de comptes rendus de réunions.

La solution repose sur :

- Une infrastructure Jitsi déployée localement
- Un bot automatisé de participation aux réunions
- Un moteur de transcription vocale
- Un modèle de langage exécuté localement
- Un système centralisé de gestion de l'état de réunion
- Un module d'exportation des comptes rendus

L'objectif est de transformer les échanges audio d'une réunion en un compte rendu structuré contenant :

- Un résumé
- Les sujets abordés
- Les décisions prises
- Les actions à réaliser
- Les questions ouvertes

---

# Objectifs de l'Architecture

## 1. Modularité

Chaque fonctionnalité principale est isolée dans un composant dédié :

- Interface graphique
- Coordination des réunions
- Intégration Jitsi
- Transcription
- Analyse du contenu
- Gestion de l'état
- Exportation

### Avantages

- Maintenance simplifiée
- Remplacement facile des composants
- Évolution indépendante des modules

---

## 2. Séparation des responsabilités

Chaque composant possède une responsabilité unique et clairement définie.

| Composant | Responsabilité |
|------------|---------------|
| Interface graphique | Interaction utilisateur |
| MeetingController | Orchestration |
| Bot Jitsi | Accès à la réunion |
| Module de transcription | Reconnaissance vocale |
| Analyseur | Exploitation du contenu |
| Exportateur | Génération des documents |

---

## 3. Traitement local des données

L'ensemble des traitements est exécuté localement :

- Serveur Jitsi local
- Faster-Whisper local
- Ollama local

### Bénéfices

- Protection des données
- Réduction des dépendances externes
- Fonctionnement hors ligne

---

## 4. Maintenabilité

L'architecture favorise :

- Des responsabilités clairement définies
- Une configuration centralisée
- Des structures de données partagées

---

## 5. Évolutivité

L'architecture permet l'ajout futur de :

- Gestion avancée des participants
- Diarisation des locuteurs
- Nouveaux moteurs de transcription
- Nouveaux modèles de langage
- Nouveaux formats d'export

---

# Vue d'ensemble du système

L'élément central de l'application est :


MeetingState


Tous les composants interagissent autour de cette représentation commune de la réunion.

## Flux général


Utilisateur
     │
     ▼
Interface graphique (PySide6)
     │
     ▼
MeetingController
     │
     ├── Gestion de réunion
     │
     ▼
Bot Jitsi (Playwright)
     │
     ├── Participants
     │         │
     │         ▼
     │   participants.json
     │
     └── Flux audio
               │
               ▼
         Faster-Whisper
               │
               ▼
      live_transcript.txt
               │
               ▼
            Analyseur
               │
               ▼
             Ollama
               │
               ▼
          MeetingState
               │
      ┌────────┴────────┐
      ▼                 ▼
 Interface        Exportateur
 Graphique             │
                  ┌────┴────┐
                  ▼         ▼
                 PDF      DOCX


---

# Architecture Logique

## Couche de Présentation

### Technologie

- PySide6

### Fonctionnalités

- Création d'une réunion
- Arrêt d'une réunion
- Consultation des participants
- Visualisation de la transcription
- Consultation du compte rendu
- Modification du contenu généré
- Sauvegarde des données
- Exportation

### Principe

L'interface graphique ne communique jamais directement avec :

- Jitsi
- Faster-Whisper
- Ollama

Toutes les interactions transitent par :


MeetingController


---

## Couche de Coordination

### Composant principal


MeetingController


### Responsabilités

- Initialisation d'une réunion
- Démarrage du bot
- Arrêt du bot
- Gestion des participants
- Gestion des transcriptions
- Sauvegarde de l'état
- Préparation de l'export

### Principe

Le contrôleur orchestre les services mais ne réalise pas lui-même :

- La transcription
- L'analyse du contenu

---

## Couche d'Intégration Jitsi

### Composants

- Bot Jitsi
- Client Web Jitsi local
- Playwright

### Responsabilités

- Connexion à la réunion
- Récupération des participants
- Capture des flux audio

### Limitation actuelle

La découverte des participants repose actuellement sur :

javascript
_participants
_numberOfParticipants


Ces propriétés étant internes à Jitsi, cette dépendance devra être isolée pour faciliter les évolutions futures.

---

## Couche de Transcription

### Pipeline


Audio participant
      │
      ▼
Capture audio
      │
      ▼
Flux PCM
      │
      ▼
WebSocket
      │
      ▼
LiveJitsiTranscriber
      │
      ▼
Faster-Whisper
      │
      ▼
Texte transcrit


### Sortie


live_transcript.txt


---

## Couche d'Analyse

### Technologies

- Ollama
- Modèle de langage local

### Entrée


Transcription


### Sortie


MeetingState


### Informations générées

- Résumé
- Sujets
- Décisions
- Actions
- Questions ouvertes

### Contrainte

Le modèle ne doit pas inventer d'informations.

Toutes les informations doivent être fondées sur la transcription.

---

## Couche de Gestion de l'État

### Modèle central


MeetingState


### Structure


MeetingState
│
├── meeting_name
├── summary
├── topics
├── decisions
├── action_items
├── open_questions
└── participants


### Persistance


meeting_state.json


---

## Couche d'Exportation

### Composant


MeetingExporter


### Entrée


MeetingState


### Sorties

- PDF
- DOCX

### Principe

L'exportateur ne modifie jamais les données de réunion.

Il exploite uniquement l'état final validé par l'utilisateur.

---

# Structure du Projet


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


---

# Communication entre les Composants

## Appels Python

Exemple :


GUI → MeetingController


Utilisé pour :

- Démarrer une réunion
- Arrêter une réunion
- Sauvegarder les données

---

## Fichiers Persistants

| Fichier | Rôle |
|----------|------|
| participants.json | Informations participants |
| live_transcript.txt | Transcription |
| meeting_state.json | État de réunion |
| bot.log | Journalisation |

Tous ces fichiers sont stockés dans :


recordings/


---

## Services Réseau Locaux

Services utilisés :

- Serveur HTTPS local
- Serveur WebSocket local
- API Ollama locale

---

# Gestion des Processus

## Processus principal


Application PySide6


---

## Processus secondaire


Bot Jitsi


Piloté par :


MeetingController


---

## Services d'arrière-plan

- Serveur Web local
- Serveur WebSocket
- Ollama

Cette séparation évite qu'un traitement long bloque l'interface utilisateur.

---

# Principes Architecturaux

## Responsabilité unique

Chaque composant possède une fonction principale clairement définie.

---

## Configuration centralisée

Tous les paramètres doivent être regroupés dans :


config.py


---

## Source unique de vérité


MeetingState


constitue la représentation officielle des données de réunion.

---

## Faible couplage

Les composants communiquent via des interfaces clairement définies.

---

## Isolation des dépendances externes

| Dépendance | Couche concernée |
|------------|-----------------|
| Jitsi | Intégration |
| Playwright | Intégration |
| Faster-Whisper | Transcription |
| Ollama | Analyse |

---

## Traçabilité

Les journaux et données intermédiaires doivent permettre :

- Le diagnostic des erreurs
- La compréhension du comportement du système

---

## Évolutivité

L'ajout de nouvelles fonctionnalités ne doit pas remettre en cause l'architecture globale.

---

# Limites Actuelles

## Gestion des participants

La récupération des participants dépend actuellement de propriétés internes de Jitsi.

---

## Communication par fichiers

### Avantages

- Simplicité
- Débogage facilité

### Inconvénients

- Risques de synchronisation
- Accès concurrents possibles

---

## Mise à jour de l'interface

L'interface repose actuellement en partie sur une lecture périodique des fichiers.

Une architecture événementielle serait préférable à terme.

---

## Attribution des locuteurs

L'association entre participant et flux audio nécessite encore une validation approfondie.

---

## Gestion des erreurs

Un système de journalisation plus structuré devra être mis en place.

---

# Évolutions Futures

## Centralisation complète de la configuration

Suppression des valeurs codées en dur.

---

## Renforcement de l'isolation des couches

Réduction des dépendances directes.

---

## Journalisation structurée

Remplacement progressif des :


print(...)


par un système de logging complet.

---

## Architecture événementielle

Réduction de la dépendance aux fichiers intermédiaires.

Solutions envisageables :

- Signals/Slots Qt
- Event Bus
- Architecture orientée événements

---

## Gestion avancée des participants

Amélioration de :

- L'identification des participants
- La diarisation
- La séparation des locuteurs

---

## Tests automatisés

Développement de :

- Tests unitaires
- Tests d'intégration
- Tests End-to-End

---

# Principe Fondamental

L'architecture repose sur une séparation stricte des responsabilités :

- L'interface gère la présentation
- Le contrôleur gère l'orchestration
- Les services spécialisés réalisent les traitements
- `MeetingState` fournit la représentation commune des données

Cette organisation garantit la maintenabilité, l'évolutivité et la robustesse du système.