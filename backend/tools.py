"""
tools.py — Tool Calling System
Implements mock healthcare tools: clinic finder, SMS alerts, emergency escalation.
These simulate real services without requiring external API keys.
"""

import json
from datetime import datetime
from typing import Any

from .config import CLINICS_DATA_PATH  # type: ignore # pyright: ignore


def _load_clinics() -> list[dict[str, Any]]:
    """Load the mock clinic dataset from JSON file."""
    try:
        with open(CLINICS_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[Tools] Warning: Could not load clinics.json")
        return []


def find_nearby_clinics(location: str = "", specialty: str = "") -> dict:
    """
    Find nearby clinics based on location and specialty.
    Uses the mock clinics.json dataset.

    Args:
        location: Area or city name (e.g., "Chennai", "Delhi")
        specialty: Medical specialty (e.g., "Cardiology", "General Medicine")

    Returns:
        dict with "clinics" list (top 3 matches) and "message"
    """
    clinics = _load_clinics()

    # ── Filter clinics ───────────────────────────────────────────────────
    results = []
    for clinic in clinics:
        # Match by location (check address or region)
        location_match = (
            not location
            or location.lower() in clinic.get("address", "").lower()
            or location.lower() in clinic.get("region", "").lower()
        )

        # Match by specialty
        specialty_match = (
            not specialty
            or specialty.lower() in clinic.get("specialty", "").lower()
        )

        if location_match and specialty_match:
            results.append(clinic)

    # If no specific matches, return top-rated clinics
    if not results:
        results = clinics

    # ── Sort by rating and return top 3 ──────────────────────────────────
    results.sort(key=lambda c: c.get("rating", 0), reverse=True)
    top_clinics = results[:3]  # type: ignore # pyright: ignore

    message = f"Found {len(top_clinics)} clinics"
    if location:
        message += f" near {location}"
    if specialty:
        message += f" for {specialty}"

    print(f"[Tools] Clinic search: {message}")

    return {
        "clinics": top_clinics,
        "message": message,
    }


def send_sms_alert(phone: str = "", message: str = "") -> dict:
    """
    Simulate sending an SMS alert (mock Twilio).
    In a real app, this would call the Twilio API.

    Args:
        phone: Recipient phone number
        message: SMS message content

    Returns:
        dict with confirmation details
    """
    timestamp = datetime.now().isoformat()

    # ── Simulate SMS sending ─────────────────────────────────────────────
    print(f"[Tools] 📱 SMS ALERT (simulated)")
    print(f"        To: {phone}")
    print(f"        Message: {message}")
    print(f"        Time: {timestamp}")

    return {
        "status": "sent",
        "to": phone,
        "message": message,
        "timestamp": timestamp,
        "note": "This is a simulated SMS. In production, integrate Twilio API.",
    }


def escalate_emergency(patient_info: str = "") -> dict:
    """
    Simulate emergency escalation (mock ambulance dispatch).
    In a real app, this would trigger actual emergency services.

    Args:
        patient_info: Description of the patient's condition

    Returns:
        dict with mock emergency response details
    """
    timestamp = datetime.now().isoformat()

    # ── Simulate emergency dispatch ──────────────────────────────────────
    print(f"[Tools] 🚨 EMERGENCY ESCALATION (simulated)")
    print(f"        Patient: {patient_info}")
    print(f"        Time: {timestamp}")

    return {
        "status": "dispatched",
        "ambulance_id": "AMB-2024-001",
        "eta_minutes": 12,
        "patient_info": patient_info,
        "timestamp": timestamp,
        "emergency_number": "108",
        "note": "This is a simulated emergency. In production, call real emergency services.",
    }


# ── Tool Registry ───────────────────────────────────────────────────────────
# Maps tool names to their functions, used by the AI processor
TOOL_REGISTRY = {
    "find_nearby_clinics": find_nearby_clinics,
    "send_sms_alert": send_sms_alert,
    "escalate_emergency": escalate_emergency,
}

# ── Tool Definitions for OpenAI Function Calling ────────────────────────────
# These are passed to the OpenAI API so GPT knows what tools are available
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "find_nearby_clinics",
            "description": "Find nearby hospitals or clinics based on the user's location and required medical specialty. Use this when the user asks about hospitals, clinics, or where to get medical help.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or area name, e.g., 'Chennai', 'Delhi', 'Lucknow'",
                    },
                    "specialty": {
                        "type": "string",
                        "description": "Medical specialty needed, e.g., 'Cardiology', 'General Medicine', 'Pediatrics'",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_sms_alert",
            "description": "Send an SMS alert to a phone number. Use this when the user wants to notify a family member or caregiver about their health condition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number to send SMS to",
                    },
                    "message": {
                        "type": "string",
                        "description": "The alert message content",
                    },
                },
                "required": ["phone", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_emergency",
            "description": "Escalate to emergency services when the patient has severe or life-threatening symptoms. Use this for chest pain, breathing difficulty, stroke symptoms, severe bleeding, or loss of consciousness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_info": {
                        "type": "string",
                        "description": "Description of the patient's condition and symptoms",
                    },
                },
                "required": ["patient_info"],
            },
        },
    },
]
