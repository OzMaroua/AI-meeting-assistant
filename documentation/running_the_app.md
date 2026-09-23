# Running the Application

## Prerequisites

Before launching the application, ensure that:

- Python is installed
- The virtual environment is activated
- Dependencies are installed
- Ollama is running
- The required model is available
- The Jitsi server is accessible

---

# 1. Activate the Virtual Environment

Linux/macOS:

```bash
cd ~/meeting-assistant

source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

Expected result:

```text
(venv) user@machine:~/meeting-assistant$
```

---

# 2. Verify Ollama

Check that Ollama is installed:

```bash
ollama --version
```

List available models:

```bash
ollama list
```

Example:

```text
NAME      ID      SIZE
qwen3     xxxx    5.2 GB
```

If the model is missing:

```bash
ollama pull qwen3
```

---

# 3. Start Ollama

If Ollama is not already running:

```bash
ollama serve
```

Default API endpoint:

```text
http://127.0.0.1:11434
```

Verify:

```bash
curl http://127.0.0.1:11434/api/tags
```

---

# 4. Verify Jitsi Access

Launch Jitsi local client 

```bash
python jitsi-client/server.py 
```
---

# 5. Launch the Application

From the project root:

```bash
python main.py
```

Expected behavior:

```text
✓ GUI started
✓ MeetingController initialized
✓ Configuration loaded
✓ Ollama connection available
```

The graphical interface should open.

---

# 6. Start a Meeting

1. Enter the meeting name
2. Enter the Jitsi room name
3. Click **Start bot**

The application will:

```text
Launch Bot
    │
    ▼
Join Jitsi Room
    │
    ▼
Detect Participants
    │
    ▼
Start Audio Capture
    │
    ▼
Start Transcription
```

---

# 7. During the Meeting

The GUI should display:

- Connected participants
- Live transcript
- Generated summary
- Decisions
- Action items

Generated files:

```text
recordings/
├── participants.json
├── live_transcript.txt
├── meeting_state.json
└── bot.log
```

---

# 8. Export Results

After the meeting:

1. Stop the meeting
2. Review the generated content
3. Click **Export PDF** or **Export DOCX**

Output:

```text
exports/
├── meeting_report.pdf
└── meeting_report.docx
```

---

# 9. Stop the Application

Stop the meeting from the GUI.

Then close the application window.

If running from terminal:

```bash
CTRL+C
```

---

# Troubleshooting

## GUI Does Not Start

Verify:

```bash
python --version
pip list | grep PySide6
```

---

## Ollama Connection Error

Verify:

```bash
ollama serve
```

Test:

```bash
curl http://127.0.0.1:11434/api/tags
```

---

## Model Not Found

Install the model:

```bash
ollama pull qwen3
```

---

## Jitsi Connection Failure

Verify:

```text
https://192.168.10.151
```

Check:

- Network access
- HTTPS certificate
- Server availability

---

## No Transcript Produced

Verify:

```text
recordings/live_transcript.txt
```

Check:

- Microphone permissions
- Audio capture
- PCM Server
- Faster-Whisper initialization

---

# Quick Start

```bash
cd ~/meeting-assistant

source venv/bin/activate

ollama serve

python jitsi-client/server.py 

python main.py
```

Then:

```text
Open GUI
    ↓
Start Meeting
    ↓
Join Jitsi
    ↓
Transcribe
    ↓
Analyze
    ↓
Export PDF/DOCX
```