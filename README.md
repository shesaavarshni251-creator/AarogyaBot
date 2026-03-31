# 🏥 AarogyaBot — Multilingual Healthcare Voice Assistant

An AI-powered voice assistant that listens in **Tamil**, **Hindi**, or **English**, understands symptoms using AI, and responds with helpful healthcare advice — all through voice.

---

## 📐 Architecture

```
┌─────────────────────────────────────────────┐
│            Frontend (HTML/JS)               │
│  🎤 Record → 💬 Chat Panel → 🔊 Playback   │
├─────────────────────────────────────────────┤
│            FastAPI Backend                  │
│  1. STT (Whisper)     → text               │
│  2. Language detect   → hi / ta / en       │
│  3. AI (GPT-4o)       → response + triage  │
│     ├─ find_nearby_clinics                  │
│     ├─ send_sms_alert                      │
│     └─ escalate_emergency                  │
│  4. TTS (gTTS)        → audio file         │
├─────────────────────────────────────────────┤
│  📁 clinics.json   📁 chat_logs/           │
└─────────────────────────────────────────────┘
```

---

## 🚀 Setup Instructions

### Prerequisites
- **Python 3.9+** installed
- **FFmpeg** installed (required by Whisper for audio processing)
  - Windows: `winget install FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### Step 1: Clone / Navigate to the project
```bash
cd AarogyaBot
```

### Step 2: Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure API key
```bash
# Copy the example env file
copy .env.example .env     # Windows
cp .env.example .env       # Mac/Linux

# Edit .env and add your OpenAI API key
# If you skip this, the app works in offline mode with rule-based responses
```

### Step 5: Run the server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### Step 6: Open in browser
Navigate to: **http://localhost:8000**

---

## 🎮 How to Use

1. **Select language** (optional) — choose Hindi, Tamil, or English from the dropdown, or leave on "Auto Detect"
2. **Click the 🎤 microphone button** — or press the **Space** key
3. **Speak your symptoms** — e.g., "मुझे बुखार है" (I have a fever)
4. **Click again to stop** recording
5. **Read the response** in the chat panel
6. **Listen to the voice response** — audio plays automatically
7. **Check the 📊 Dashboard tab** for session statistics

---

## 📁 Project Structure

```
AarogyaBot/
├── backend/
│   ├── main.py            # FastAPI routes & pipeline
│   ├── stt.py             # Speech-to-Text (Whisper)
│   ├── tts.py             # Text-to-Speech (gTTS)
│   ├── ai_processor.py    # AI processing (GPT-4o + fallback)
│   ├── tools.py           # Mock tools (clinics, SMS, emergency)
│   ├── config.py          # Configuration & settings
│   ├── logger.py          # Chat history & logging
│   └── data/
│       └── clinics.json   # Mock clinic dataset
├── frontend/
│   ├── index.html         # Main UI
│   ├── style.css          # Dark-mode glassmorphism styles
│   └── app.js             # Client-side logic
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
└── README.md              # This file
```

---

## ⚙️ Features

| Feature | Description |
|---------|-------------|
| 🎤 Voice Input | Record speech in Hindi, Tamil, or English |
| 🧠 AI Triage | GPT-4o understands symptoms and classifies urgency |
| 🏥 Clinic Finder | Suggests nearby hospitals from mock dataset |
| 📱 SMS Alerts | Simulates sending alerts to family members |
| 🚨 Emergency Escalation | Auto-escalates severe symptoms |
| 🔊 Voice Response | Bot speaks back using gTTS |
| 💬 Chat History | Full conversation log per session |
| 📊 Dashboard | Statistics and recent activity log |
| 🌐 Auto Language Detection | Whisper + langdetect for accuracy |
| 🔌 Offline Mode | Rule-based fallback when no API key |

---

## 🧠 AI Safety Rules

The bot follows strict healthcare safety guidelines:
- ❌ **Never gives definitive medical diagnoses**
- ✅ Only provides general health advice
- 🚨 Suggests emergency services (108) for severe symptoms
- 🗣️ Responds in the same language as the user
- 👨‍⚕️ Always recommends consulting a doctor for serious concerns

---

## 🔮 Future Improvements

- [ ] Add WebSocket for real-time streaming responses
- [ ] Integrate real Google Maps API for clinic search
- [ ] Add Twilio integration for actual SMS alerts
- [ ] Support more languages (Kannada, Telugu, Bengali)
- [ ] Add user authentication and profile management
- [ ] Implement appointment booking feature
- [ ] Add symptom history tracking and trends
- [ ] Deploy with Docker for easy setup
- [ ] Add voice activity detection (auto start/stop recording)
- [ ] Implement end-to-end encryption for patient data

---

## 📝 License

This project is for educational purposes. Always consult a qualified medical professional for health concerns.
