import os
from pathlib import Path

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "lucy-optimized")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))

# Paths
BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
VOICE_DIR = BASE_DIR / "voice"

# Voice
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
PIPER_VOICE = os.getenv("PIPER_VOICE", "pt_BR-faber-medium")
