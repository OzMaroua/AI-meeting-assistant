# config.py

# Ollama
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:4b"

# Whisper
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_LANGUAGE = "fr"

# Files
TRANSCRIPT_FILE = "recordings/live_transcript.txt"
MEETING_STATE_FILE = "meeting_state.json"

# Audio
SAMPLE_RATE = 48000

# Analysis
ANALYSIS_INTERVAL = 30