"""
stt.py — Speech-to-Text Module
Uses OpenAI Whisper API (remote) to transcribe Tamil/Hindi audio.
Falls back to langdetect for language confirmation.
"""

import os
import shutil
from typing import Optional

from openai import OpenAI  # type: ignore # pyright: ignore
from langdetect import detect, LangDetectException  # type: ignore # pyright: ignore
from .config import OPENAI_API_KEY, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES  # type: ignore # pyright: ignore

# ── Initialize OpenAI Client ───────────────────────────────────────────────
# This uses the API key from config.py
client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe(audio_path: str, language: Optional[str] = None) -> dict:
    """
    Transcribe an audio file using OpenAI's Whisper API.

    Args:
        audio_path: Path to the audio file (WAV, MP3, etc.)
        language: Optional language code ('ta', 'hi', 'en').

    Returns:
        dict with keys:
            - "text": The transcribed text
            - "language": Detected language code (e.g., "hi", "ta")
    """
    try:
        # ── Verify API Key ───────────────────────────────────────────────
        if not OPENAI_API_KEY:
            print("[STT] ERROR: OPENAI_API_KEY is not set in environment variables.")
            return {"text": "", "language": DEFAULT_LANGUAGE}

        # ── Run OpenAI Whisper API transcription ──────────────────────────
        # Open the audio file in binary read mode
        with open(audio_path, "rb") as audio_file:
            print(f"[STT] Sending file to OpenAI: {audio_path}")
            # API call to Whisper
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                # If language is provided, pass it to the API
                language=language if language in SUPPORTED_LANGUAGES else None
            )

        transcribed_text = response.text.strip()
        
        # ── Confirm Language ─────────────────────────────────────────────
        # OpenAI API doesn't return the detected language code in the simple 
        # transcription response. We use langdetect to identify/confirm it.
        detected_lang = language if language else _confirm_language(transcribed_text, DEFAULT_LANGUAGE)

        print(f"[STT] Success: '{transcribed_text}' (lang={detected_lang})")

        return {
            "text": transcribed_text,
            "language": detected_lang,
        }

    except Exception as e:
        print(f"[STT] CRITICAL ERROR during transcription: {str(e)}")
        # Log more details if possible
        if "api_key" in str(e).lower():
            print("[STT] Likely an API Key issue.")
        return {
            "text": "",
            "language": DEFAULT_LANGUAGE,
        }


def _confirm_language(text: str, default_lang: str) -> str:
    """
    Use langdetect to identify the language of the transcribed text.

    Args:
        text: The transcribed text
        default_lang: fallback language

    Returns:
        Detected language code or default
    """
    if not text:
        return default_lang

    try:
        detected = detect(text)
        # langdetect returns ISO 639-1 codes (e.g., "hi", "ta", "en")
        if detected in SUPPORTED_LANGUAGES:
            return detected
    except LangDetectException:
        pass  # langdetect couldn't determine language

    return default_lang
