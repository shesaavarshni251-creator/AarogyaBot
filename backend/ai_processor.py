"""
ai_processor.py — AI Processing Layer
Uses OpenAI GPT-4o for symptom understanding, triage, and response generation.
Falls back to a rule-based system when no API key is available.
"""

import json
from typing import Any, Optional
from openai import OpenAI  # type: ignore # pyright: ignore
from .config import OPENAI_API_KEY  # type: ignore # pyright: ignore
from .tools import TOOL_DEFINITIONS, TOOL_REGISTRY  # type: ignore # pyright: ignore

# ── System Prompt ────────────────────────────────────────────────────────────
# This prompt enforces healthcare safety rules and defines the bot's behavior
SYSTEM_PROMPT = """You are AarogyaBot (आरोग्यBot), a friendly and helpful multilingual healthcare voice assistant.

## Your Core Rules:
1. **NEVER give a definitive medical diagnosis.** You are NOT a doctor.
2. **Only provide general health advice** and suggest the user consult a doctor.
3. **If symptoms sound severe** (chest pain, difficulty breathing, stroke signs, severe bleeding, loss of consciousness), immediately suggest calling emergency services (108) and use the escalate_emergency tool.
4. **Always respond in the SAME LANGUAGE** the user speaks (Tamil or Hindi or English).
5. **Be polite, clear, and simple.** Use easy-to-understand language.
6. **Perform basic triage**: classify the urgency as "low", "medium", or "high".

## Your Capabilities:
- Understand symptoms described by the user
- Provide general health advice (rest, hydration, basic remedies)
- Suggest when to see a doctor
- Find nearby clinics using the find_nearby_clinics tool
- Send SMS alerts to family members using the send_sms_alert tool
- Escalate emergencies using the escalate_emergency tool

## Response Format:
Always structure your response naturally in the user's language. Include:
- Acknowledgment of their symptoms
- General advice
- Whether they should see a doctor
- Offer to find nearby clinics if appropriate

## Urgency Classification:
- **low**: Common cold, mild headache, minor aches, general wellness questions
- **medium**: Persistent fever, stomach pain, recurring issues, symptoms lasting >3 days
- **high**: Chest pain, severe breathing difficulty, high fever (>103°F), stroke symptoms, severe bleeding, unconsciousness

Remember: You are a helpful assistant, NOT a replacement for professional medical care."""


# ── Offline Fallback Rules ───────────────────────────────────────────────────
# Simple keyword-based responses when OpenAI API is not available
FALLBACK_RULES = {
    "hi": {
        "fever": {
            "response": "आपको बुखार है। कृपया आराम करें, पानी पिएं, और पैरासिटामोल लें। अगर बुखार 3 दिन से ज़्यादा रहे तो डॉक्टर से मिलें।",
            "urgency": "medium",
        },
        "headache": {
            "response": "सिरदर्द के लिए आराम करें, पानी पिएं। अगर दर्द गंभीर है या बार-बार होता है तो डॉक्टर से मिलें।",
            "urgency": "low",
        },
        "cold": {
            "response": "सर्दी-जुकाम के लिए गर्म पानी पिएं, भाप लें, और आराम करें। अगर बुखार भी है तो डॉक्टर से मिलें।",
            "urgency": "low",
        },
        "chest": {
            "response": "⚠️ छाती में दर्द गंभीर हो सकता है। कृपया तुरंत 108 पर कॉल करें या नज़दीकी अस्पताल जाएं!",
            "urgency": "high",
        },
        "breathing": {
            "response": "⚠️ सांस लेने में तकलीफ गंभीर हो सकती है। कृपया तुरंत 108 पर कॉल करें!",
            "urgency": "high",
        },
        "default": {
            "response": "मैं आपकी बात समझ गया। कृपया अपने लक्षण बताएं ताकि मैं आपकी मदद कर सकूं। अगर आप गंभीर रूप से बीमार हैं तो डॉक्टर से मिलें।",
            "urgency": "low",
        },
    },
    "ta": {
        "fever": {
            "response": "உங்களுக்கு காய்ச்சல் இருக்கிறது. தயவுசெய்து ஓய்வெடுங்கள், தண்ணீர் குடியுங்கள், பாராசிட்டமால் எடுங்கள். காய்ச்சல் 3 நாட்களுக்கு மேல் இருந்தால் மருத்துவரிடம் செல்லுங்கள்.",
            "urgency": "medium",
        },
        "headache": {
            "response": "தலைவலிக்கு ஓய்வெடுங்கள், தண்ணீர் குடியுங்கள். வலி கடுமையாக இருந்தால் மருத்துவரிடம் செல்லுங்கள்.",
            "urgency": "low",
        },
        "cold": {
            "response": "சளி, இருமலுக்கு சூடான தண்ணீர் குடியுங்கள், ஆவி பிடியுங்கள். காய்ச்சல் இருந்தால் மருத்துவரிடம் செல்லுங்கள்.",
            "urgency": "low",
        },
        "chest": {
            "response": "⚠️ நெஞ்சு வலி தீவிரமாக இருக்கலாம். உடனடியாக 108 அழைக்கவும் அல்லது அருகிலுள்ள மருத்துவமனைக்குச் செல்லுங்கள்!",
            "urgency": "high",
        },
        "breathing": {
            "response": "⚠️ சுவாசிப்பதில் சிரமம் தீவிரமாக இருக்கலாம். உடனடியாக 108 அழைக்கவும்!",
            "urgency": "high",
        },
        "default": {
            "response": "நான் புரிந்துகொண்டேன். உங்கள் அறிகுறிகளை தெரிவிக்கவும். நீங்கள் மிகவும் உடல்நிலை சரியில்லை என்றால் மருத்துவரிடம் செல்லுங்கள்.",
            "urgency": "low",
        },
    },
    "en": {
        "fever": {
            "response": "You seem to have a fever. Please rest, drink plenty of water, and take paracetamol. If fever persists for more than 3 days, please see a doctor.",
            "urgency": "medium",
        },
        "headache": {
            "response": "For headaches, please rest and stay hydrated. If the pain is severe or recurring, consult a doctor.",
            "urgency": "low",
        },
        "cold": {
            "response": "For cold and cough, drink warm water, try steam inhalation, and rest. If you also have fever, see a doctor.",
            "urgency": "low",
        },
        "chest": {
            "response": "⚠️ Chest pain can be serious. Please call 108 immediately or go to the nearest hospital!",
            "urgency": "high",
        },
        "breathing": {
            "response": "⚠️ Difficulty breathing can be serious. Please call 108 immediately!",
            "urgency": "high",
        },
        "default": {
            "response": "I understand. Please describe your symptoms so I can help. If you're feeling very unwell, please consult a doctor.",
            "urgency": "low",
        },
    },
}

# Keywords mapped to the rule keys above (works across languages)
SYMPTOM_KEYWORDS = {
    "fever": ["fever", "बुखार", "தகாய்ச்சல்", "காய்ச்சல்", "ज्वर", "temperature", "तापमान"],
    "headache": ["headache", "सिरदर्द", "சிர", "தலைவலி", "head", "सिर"],
    "cold": ["cold", "सर्दी", "जुकाम", "cough", "खांसी", "இருமல்", "சளி", "sneeze"],
    "chest": ["chest", "छाती", "நெஞ்சு", "heart", "दिल", "இதயம்"],
    "breathing": ["breathing", "सांस", "breath", "சுவாச", "மூச்சு", "asthma", "दम"],
}


def process(text: str, language: str = "hi", chat_history: Optional[list[dict[str, str]]] = None) -> dict:
    """
    Process user text through AI to understand symptoms and generate response.

    Args:
        text: User's transcribed text
        language: Detected language code ('hi', 'ta', 'en')
        chat_history: Previous conversation messages for context

    Returns:
        dict with:
            - "response": Bot's text response
            - "urgency": "low", "medium", or "high"
            - "tool_calls": List of tool calls made (if any)
    """
    # ── Try OpenAI GPT first ─────────────────────────────────────────────
    if OPENAI_API_KEY:
        return _process_with_gpt(text, language, chat_history or [])

    # ── Fallback to rule-based system ────────────────────────────────────
    print("[AI] No API key found, using offline fallback rules")
    return _process_with_rules(text, language)


def _process_with_gpt(text: str, language: str, chat_history: list[dict[str, str]]) -> dict:
    """Process using OpenAI GPT-4o with tool calling."""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # ── Build message history ────────────────────────────────────────
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add previous conversation for context
        for entry in chat_history[-6:]:  # type: ignore
            messages.append({"role": "user", "content": entry.get("user", "")})
            messages.append({"role": "assistant", "content": entry.get("bot", "")})

        # Add current user message
        messages.append({
            "role": "user",
            "content": f"[Language: {language}] {text}",
        })

        # ── Call OpenAI API with tools ───────────────────────────────────
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=500,
        )

        message = response.choices[0].message
        tool_results = []

        # ── Handle tool calls if any ─────────────────────────────────────
        if message.tool_calls:
            # Add assistant's message with tool calls
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"[AI] Tool call: {func_name}({func_args})")

                # Execute the tool
                if func_name in TOOL_REGISTRY:
                    result = TOOL_REGISTRY[func_name](**func_args)
                    tool_results.append({
                        "tool": func_name,
                        "args": func_args,
                        "result": result,
                    })
                else:
                    result = {"error": f"Unknown tool: {func_name}"}

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            # ── Get final response after tool calls ──────────────────────
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            response_text = final_response.choices[0].message.content
        else:
            response_text = message.content

        # ── Determine urgency from response ──────────────────────────────
        urgency = _detect_urgency(text, response_text)

        print(f"[AI] Response generated (urgency={urgency})")

        return {
            "response": response_text or "I'm sorry, I couldn't process that.",
            "urgency": urgency,
            "tool_calls": tool_results,
        }

    except Exception as e:
        print(f"[AI] GPT error: {e}, falling back to rules")
        return _process_with_rules(text, language)


def _process_with_rules(text: str, language: str) -> dict:
    """Fallback rule-based symptom matching when no API key is available."""
    text_lower = text.lower()
    lang_rules: dict[str, Any] = FALLBACK_RULES.get(language, FALLBACK_RULES["en"])

    # ── Check each symptom category ──────────────────────────────────────
    for category, keywords in SYMPTOM_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                if category in lang_rules:
                    rule = lang_rules[category]  # type: ignore # pyright: ignore
                else:
                    rule = lang_rules["default"]  # type: ignore # pyright: ignore
                return {
                    "response": rule["response"],
                    "urgency": rule["urgency"],
                    "tool_calls": [],
                }

    # ── No symptom matched, use default response ────────────────────────
    default = lang_rules["default"]
    return {
        "response": default["response"],
        "urgency": default["urgency"],
        "tool_calls": [],
    }


def _detect_urgency(user_text: str, bot_response: str) -> str:
    """
    Detect urgency level from the conversation content.
    Checks for high-urgency keywords first, then medium, then defaults to low.
    """
    combined = (user_text + " " + (bot_response or "")).lower()

    # High urgency indicators
    high_keywords = [
        "emergency", "ambulance", "108", "chest pain", "heart attack",
        "breathing difficulty", "stroke", "unconscious", "severe bleeding",
        "छाती में दर्द", "सांस", "बेहोश", "நெஞ்சு வலி", "மூச்சு",
        "escalate", "immediately", "तुरंत", "உடனடியாக",
    ]
    if any(kw in combined for kw in high_keywords):
        return "high"

    # Medium urgency indicators
    medium_keywords = [
        "persistent", "recurring", "days", "fever", "infection",
        "बुखार", "संक्रमण", "காய்ச்சல்", "doctor", "डॉक्टर", "மருத்துவர்",
    ]
    if any(kw in combined for kw in medium_keywords):
        return "medium"

    return "low"
