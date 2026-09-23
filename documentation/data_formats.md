# Composants du système

## Vue d'ensemble

Le système est organisé autour de plusieurs composants spécialisés :

```text
GUI
 │
 ▼
MeetingController
 │
 ├── Jitsi Bot
 ├── Transcriber
 ├── Analyzer
 ├── MeetingState
 └── Exporter
```

Chaque composant possède une responsabilité unique afin de garantir la modularité et la maintenabilité du système.

---

# Structure du projet

```text
meeting-assistant/
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

# Principaux composants

## `main.py`

**Rôle :** Point d'entrée de l'application.

**Responsabilités :**

- Démarrer l'application
- Initialiser l'interface graphique
- Lancer le système

```text
main.py
   │
   ▼
 GUI
```

---

## `gui/gui.py`

**Rôle :** Interface graphique PySide6.

**Fonctionnalités :**

- Gestion des réunions
- Consultation des participants
- Affichage de la transcription
- Édition du compte rendu
- Export PDF / DOCX

**Dépendance unique :**

```text
GUI
 │
 ▼
MeetingController
```

La GUI ne communique jamais directement avec Jitsi, Whisper ou Ollama.

---

## `meeting_controller.py`

**Rôle :** Orchestrateur central.

**Responsabilités :**

- Démarrer / arrêter une réunion
- Lancer le bot Jitsi
- Gérer les participants
- Lire la transcription
- Maintenir le MeetingState
- Déclencher les exports

```text
GUI
 │
 ▼
MeetingController
 │
 ├── Jitsi Bot
 ├── MeetingState
 └── Exporter
```

---

## `jitsi-bot.py`

**Rôle :** Intégration Jitsi via Playwright.

**Responsabilités :**

- Rejoindre une salle Jitsi
- Détecter les participants
- Capturer les flux audio
- Alimenter le système de transcription

```text
Playwright
    │
    ▼
Client Jitsi Local
    │
    ▼
Serveur Jitsi
```

---

## `jitsi_client/index.html`

**Rôle :** Wrapper web local autour de l'API Jitsi.

**Fonctions :**

- Charger l'API Jitsi
- Rejoindre automatiquement une salle
- Exposer l'instance Jitsi à Playwright

```javascript
window.jitsiApi
```

---

## `jitsi_client/server.py`

**Rôle :** Serveur HTTP local.

**Adresse :**

```text
http://127.0.0.1:8000
```

**Fonction :**

- Servir `index.html`
- Fournir un environnement web local au bot

---

## `realtime/jitsi_transcriber.py`

**Rôle :** Transcription audio temps réel.

### Pipeline

```text
Audio
 │
 ▼
WebSocket
 │
 ▼
LiveJitsiTranscriber
 │
 ▼
faster-whisper
 │
 ▼
Texte
```

### Sortie

```text
live_transcript.txt
```

---

## Serveur PCM

**Adresse :**

```text
127.0.0.1:8765
```

**Fonction :**

- Réception des flux PCM
- Routage des données audio
- Communication avec le transcripteur

```text
Browser
 │
 ▼
PCM Server
 │
 ▼
Transcriber
```

---

## `transcription/analyzer.py`

**Rôle :** Analyse de la transcription via Ollama.

### Pipeline

```text
Transcript
 │
 ▼
Analyzer
 │
 ▼
Ollama
 │
 ▼
MeetingState
```

### Informations extraites

- Summary
- Topics
- Decisions
- Action Items
- Open Questions

### Contrainte

Le modèle ne doit jamais inventer d'informations absentes de la transcription.

---

## `meeting_state.py`

**Rôle :** Modèle central de données.

### Structure

```text
MeetingState
├── summary
├── topics
├── decisions
├── action_items
└── open_questions
```

### Utilisateurs

```text
Analyzer
    │
    ▼
MeetingState
    │
 ┌──┴──┐
 ▼     ▼
GUI Exporter
```

---

## `exporter.py`

**Rôle :** Génération du compte rendu final.

### Entrée

```text
MeetingState
```

### Sorties

```text
PDF
DOCX
```

L'exporteur ne réalise aucun traitement métier.

---

## `config.py`

**Rôle :** Configuration centralisée.

### Paramètres

- Serveur Jitsi
- Ports réseau
- Configuration Whisper
- Configuration Ollama
- Chemins de stockage

```text
config.py
 ├── Jitsi
 ├── Audio
 ├── Whisper
 ├── Ollama
 └── Paths
```

---

## `recordings/`

Contient les données produites pendant les réunions :

```text
recordings/
├── participants.json
├── live_transcript.txt
├── meeting_state.json
└── bot.log
```

| Fichier | Description |
|----------|-------------|
| participants.json | Participants détectés |
| live_transcript.txt | Transcription brute |
| meeting_state.json | Résultat structuré |
| bot.log | Logs du bot |

---

# Communications

Le système utilise trois mécanismes de communication :

## 1. Appels Python

```text
GUI
 │
 ▼
MeetingController
```

## 2. Fichiers locaux

```text
participants.json
live_transcript.txt
meeting_state.json
bot.log
```

## 3. Réseau local

| Service | Adresse |
|----------|----------|
| Client Web | 127.0.0.1:8000 |
| PCM WebSocket | 127.0.0.1:8765 |
| Ollama | 127.0.0.1:11434 |

---

# Résumé des responsabilités

| Composant | Responsabilité |
|------------|---------------|
| `main.py` | Point d'entrée |
| `gui.py` | Interface utilisateur |
| `meeting_controller.py` | Orchestration |
| `jitsi-bot.py` | Intégration Jitsi |
| `jitsi_transcriber.py` | Transcription |
| `analyzer.py` | Analyse LLM |
| `meeting_state.py` | Modèle de données |
| `exporter.py` | Export PDF / DOCX |
| `config.py` | Configuration |
| `recordings/` | Stockage des données |

---

# Principe architectural

```text
Présentation (GUI)
        │
        ▼
Coordination (MeetingController)
        │
 ┌──────┼──────┬───────┐
 ▼      ▼      ▼       ▼
Jitsi Whisper Ollama Export
        │
        ▼
   MeetingState
```

Chaque composant reste indépendant et spécialisé dans son domaine afin de faciliter les tests, la maintenance et les évolutions futures.