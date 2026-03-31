"""
stt.py — Speech-to-Text Module
Uses OpenAI Whisper (runs locally) to transcribe Tamil/Hindi audio.
Falls back to langdetect for language confirmation.
"""

import os
import shutil
from typing import Optional

import whisper  # type: ignore # pyright: ignore
from langdetect import detect, LangDetectException  # type: ignore # pyright: ignore
from .config import WHISPER_MODEL, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES  # type: ignore # pyright: ignore

# ── FFmpeg Path Fix ──────────────────────────────────────────────────────────
# If winget installed FFmpeg but it's not yet in the PATH, we add the default 
# winget location to ensure Whisper can find it immediately.
if not shutil.which("ffmpeg"):
    winget_path = os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
    )
    if os.path.exists(winget_path):
        os.environ["PATH"] += os.pathsep + winget_path
        print(f"[STT] Added FFmpeg to PATH from: {winget_path}")

# ── Load Whisper Model ───────────────────────────────────────────────────────
# The model is loaded once when this module is first imported.
# "base" model is ~140MB and works well for most languages.
print(f"[STT] Loading Whisper model: {WHISPER_MODEL} ...")
model = whisper.load_model(WHISPER_MODEL)
print("[STT] Whisper model loaded successfully!")


def transcribe(audio_path: str, language: Optional[str] = None) -> dict:
    """
    Transcribe an audio file to text.

    Args:
        audio_path: Path to the audio file (WAV, MP3, etc.)
        language: Optional language code ('ta', 'hi', 'en').
                  If None, Whisper will auto-detect the language.

    Returns:
        dict with keys:
            - "text": The transcribed text
            - "language": Detected language code (e.g., "hi", "ta")
    """
    try:
        # ── Run Whisper transcription ────────────────────────────────────
        # If language is specified, tell Whisper to use it for better accuracy
        options = {}
        if language and language in SUPPORTED_LANGUAGES:
            options["language"] = language

        result = model.transcribe(str(audio_path), **options)

        transcribed_text = result.get("text", "").strip()
        detected_lang = result.get("language", DEFAULT_LANGUAGE)

        # ── Confirm language using langdetect ────────────────────────────
        # Whisper's language detection is good, but we double-check with
        # langdetect for supported languages
        if not language:
            detected_lang = _confirm_language(transcribed_text, detected_lang)

        print(f"[STT] Transcribed: '{transcribed_text}' (lang={detected_lang})")

        return {
            "text": transcribed_text,
            "language": detected_lang,
        }

    except Exception as e:
        print(f"[STT] Error during transcription: {e}")
        return {
            "text": "",
            "language": DEFAULT_LANGUAGE,
        }


def _confirm_language(text: str, whisper_lang: str) -> str:
    """
    Use langdetect to confirm the language detected by Whisper.
    If langdetect agrees or can't decide, we trust Whisper.

    Args:
        text: The transcribed text
        whisper_lang: Language code from Whisper

    Returns:
        Final language code
    """
    if not text:
        return whisper_lang

    try:
        detected = detect(text)
        # langdetect returns ISO 639-1 codes (e.g., "hi", "ta", "en")
        if detected in SUPPORTED_LANGUAGES:
            return detected
    except LangDetectException:
        pass  # langdetect couldn't determine language

    # Fall back to Whisper's detection
    return whisper_lang if whisper_lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
