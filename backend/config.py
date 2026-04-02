"""
config.py — AarogyaBot Configuration
Loads settings from environment variables or .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv  # type: ignore

# ── Load .env file if it exists ──────────────────────────────────────────────
load_dotenv()

# ── Project Paths ────────────────────────────────────────────────────────────
# Root directory of the project (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Vercel has a read-only filesystem, except for /tmp
IS_VERCEL = bool(os.getenv("VERCEL"))
BASE_WRITABLE_DIR = Path("/tmp") if IS_VERCEL else PROJECT_ROOT

# Directory where TTS audio files are saved
AUDIO_OUTPUT_DIR = BASE_WRITABLE_DIR / "audio_output"
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Directory where chat session logs are stored
CHAT_LOGS_DIR = BASE_WRITABLE_DIR / "chat_logs"
CHAT_LOGS_DIR.mkdir(exist_ok=True, parents=True)

# Path to the mock clinics dataset
CLINICS_DATA_PATH = Path(__file__).resolve().parent / "data" / "clinics.json"

# Directory for temporary uploaded audio files
UPLOAD_DIR = BASE_WRITABLE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

# ── API Keys ─────────────────────────────────────────────────────────────────
# OpenAI API key — required for GPT-4o processing
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Debugging check (Safe for production)
if OPENAI_API_KEY:
    # Shows first 4 and last 3 chars for confirmation without leaking the secret
    print(f"[Config] OpenAI API Key found: {OPENAI_API_KEY[:4]}...{OPENAI_API_KEY[-3:]}")
else:
    print("[Config] CRITICAL ERROR: OpenAI API Key is EXPLICITLY EMPTY. Please check Project-level Env Vars.")


# ── Whisper Settings ─────────────────────────────────────────────────────────
# Model size: tiny, base, small, medium, large
# "base" is a good balance of speed vs accuracy for beginners
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# ── Language Settings ────────────────────────────────────────────────────────
# Supported languages and their codes
SUPPORTED_LANGUAGES = {
    "ta": "Tamil",
    "hi": "Hindi",
    "en": "English",  # English fallback
}

# Default language if detection fails
DEFAULT_LANGUAGE = "hi"

# ── Server Settings ──────────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
