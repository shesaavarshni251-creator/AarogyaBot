"""
logger.py — Chat History & Logging Module
Stores conversation history per session and provides dashboard stats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import CHAT_LOGS_DIR  # type: ignore # pyright: ignore


def _get_session_file(session_id: str) -> Path:
    """Get the path to a session's log file."""
    return CHAT_LOGS_DIR / f"{session_id}.json"


def log_interaction(
    session_id: str,
    user_text: str,
    bot_response: str,
    urgency: str = "low",
    language: str = "hi",
    tool_calls: Optional[list] = None,
) -> None:
    """
    Log a single interaction (user message + bot response) to a session file.

    Args:
        session_id: Unique session identifier
        user_text: What the user said (transcribed text)
        bot_response: What the bot replied
        urgency: Triage level — "low", "medium", or "high"
        language: Detected language code
        tool_calls: List of tool calls made (if any)
    """
    session_file = _get_session_file(session_id)

    # ── Load existing history or start fresh ─────────────────────────────
    history: list[dict[str, Any]] = []
    if session_file.exists():
        try:
            history = json.loads(session_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            history = []

    # ── Append new interaction ───────────────────────────────────────────
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "user": user_text,
        "bot": bot_response,
        "urgency": urgency,
        "language": language,
        "tool_calls": tool_calls or [],
    }
    history.append(interaction)

    # ── Save back to file ────────────────────────────────────────────────
    session_file.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Logger] Logged interaction for session {session_id}")


def get_history(session_id: str) -> list[dict[str, Any]]:
    """
    Get all interactions for a given session.

    Args:
        session_id: The session to retrieve history for

    Returns:
        List of interaction dictionaries
    """
    session_file = _get_session_file(session_id)
    if session_file.exists():
        try:
            return json.loads(session_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return []
    return []


def get_dashboard_stats() -> dict[str, Any]:
    """
    Aggregate stats across all sessions for the dashboard.

    Returns:
        dict with:
            - total_sessions: Number of unique sessions
            - total_interactions: Total messages across all sessions
            - urgency_distribution: {"low": N, "medium": N, "high": N}
            - language_distribution: {"hi": N, "ta": N, ...}
            - recent_interactions: Last 10 interactions across all sessions
    """
    # Use separate typed variables to avoid type confusion
    total_sessions: int = 0
    total_interactions: int = 0
    urgency_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    language_dist: dict[str, int] = {}
    all_interactions: list[dict[str, Any]] = []

    # ── Scan all session files ───────────────────────────────────────────
    for session_file in CHAT_LOGS_DIR.glob("*.json"):
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            total_sessions += 1

            for interaction in data:
                total_interactions += 1  # type: ignore # pyright: ignore

                # Count urgency levels
                urgency: str = interaction.get("urgency", "low")
                if urgency in urgency_dist:
                    urgency_dist[urgency] += 1  # type: ignore # pyright: ignore

                # Count languages
                lang: str = interaction.get("language", "unknown")
                language_dist[lang] = language_dist.get(lang, 0) + 1

                all_interactions.append(interaction)

        except (json.JSONDecodeError, IOError):
            continue

    # ── Get 10 most recent interactions ──────────────────────────────────
    all_interactions.sort(
        key=lambda x: x.get("timestamp", ""), reverse=True
    )

    return {
        "total_sessions": total_sessions,
        "total_interactions": total_interactions,
        "urgency_distribution": urgency_dist,
        "language_distribution": language_dist,
        "recent_interactions": all_interactions[:10],  # type: ignore # pyright: ignore
    }
