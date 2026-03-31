"""
tts.py — Text-to-Speech Module
Uses gTTS (Google Text-to-Speech) to convert text to audio.
Supports Tamil ('ta') and Hindi ('hi').
"""

import uuid
from gtts import gTTS  # type: ignore # pyright: ignore
from .config import AUDIO_OUTPUT_DIR  # type: ignore # pyright: ignore

# ── Language code mapping for gTTS ───────────────────────────────────────────
# gTTS uses standard language codes
GTTS_LANG_MAP = {
    "ta": "ta",   # Tamil
    "hi": "hi",   # Hindi
    "en": "en",   # English fallback
}


def synthesize(text: str, language: str = "hi") -> str:
    """
    Convert text to speech and save as an MP3 file.

    Args:
        text: The text to convert to speech
        language: Language code ('ta', 'hi', 'en')

    Returns:
        Filename of the generated audio file (e.g., "abc123.mp3")
    """
    try:
        # ── Map language code ────────────────────────────────────────────
        lang_code = GTTS_LANG_MAP.get(language, "hi")

        # ── Generate unique filename ─────────────────────────────────────
        # UUID ensures no two audio files overwrite each other
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_OUTPUT_DIR / filename

        # ── Create speech audio ──────────────────────────────────────────
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(str(filepath))

        print(f"[TTS] Generated audio: {filename} (lang={lang_code})")
        return filename

    except Exception as e:
        print(f"[TTS] Error during synthesis: {e}")
        return ""
