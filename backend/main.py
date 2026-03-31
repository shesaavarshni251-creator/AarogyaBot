"""
main.py — FastAPI Application Entry Point
Defines all API routes and serves the frontend.
"""

import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form  # type: ignore # pyright: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore # pyright: ignore
from fastapi.responses import FileResponse, JSONResponse  # type: ignore # pyright: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore # pyright: ignore

from backend.config import AUDIO_OUTPUT_DIR, UPLOAD_DIR, PROJECT_ROOT  # type: ignore # pyright: ignore
from backend.stt import transcribe  # type: ignore # pyright: ignore
from backend.tts import synthesize  # type: ignore # pyright: ignore
from backend.ai_processor import process  # type: ignore # pyright: ignore
from backend.logger import log_interaction, get_history, get_dashboard_stats  # type: ignore # pyright: ignore

# ── Create FastAPI App ───────────────────────────────────────────────────────
app = FastAPI(
    title="AarogyaBot",
    description="Multilingual Healthcare Voice Assistant",
    version="1.0.0",
)

# ── CORS Middleware ──────────────────────────────────────────────────────────
# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API Routes ───────────────────────────────────────────────────────────────


@app.post("/chat")
async def chat(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    language: str = Form(default=""),
):
    """
    Main chat endpoint — accepts audio, runs the full pipeline.

    Pipeline:
        1. Save uploaded audio
        2. Transcribe audio to text (STT)
        3. Process text with AI (symptom understanding + triage)
        4. Convert response to speech (TTS)
        5. Log the interaction
        6. Return results

    Args:
        audio: Audio file upload (WAV, WebM, etc.)
        session_id: Session identifier for chat history (auto-generated if empty)
        language: Optional language hint ('hi', 'ta')

    Returns:
        JSON with transcription, AI response, urgency, audio URL, and tool results
    """
    # ── Generate session ID if not provided ──────────────────────────────
    if not session_id:
        session_id = uuid.uuid4().hex[:12]  # type: ignore # pyright: ignore

    try:
        # ── Step 1: Save uploaded audio ──────────────────────────────────
        file_ext = Path(audio.filename).suffix or ".webm"
        upload_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{file_ext}"

        with open(upload_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        print(f"[Main] Audio saved: {upload_path}")

        # ── Step 2: Speech-to-Text ───────────────────────────────────────
        stt_result = transcribe(
            audio_path=str(upload_path),
            language=language if language else None,
        )
        user_text = stt_result["text"]
        detected_lang = stt_result["language"]

        if not user_text:
            return JSONResponse(
                content={
                    "error": "Could not transcribe audio. Please try again.",
                    "session_id": session_id,
                },
                status_code=400,
            )

        # ── Step 3: AI Processing ────────────────────────────────────────
        chat_hist = get_history(session_id)
        ai_result = process(
            text=user_text,
            language=detected_lang,
            chat_history=chat_hist,
        )

        bot_response = ai_result["response"]
        urgency = ai_result["urgency"]
        tool_calls = ai_result["tool_calls"]

        # ── Step 4: Text-to-Speech ───────────────────────────────────────
        audio_filename = synthesize(
            text=bot_response,
            language=detected_lang,
        )

        # ── Step 5: Log the interaction ──────────────────────────────────
        log_interaction(
            session_id=session_id,
            user_text=user_text,
            bot_response=bot_response,
            urgency=urgency,
            language=detected_lang,
            tool_calls=tool_calls,
        )

        # ── Step 6: Clean up uploaded file ───────────────────────────────
        try:
            upload_path.unlink()
        except OSError:
            pass

        # ── Return response ──────────────────────────────────────────────
        return {
            "session_id": session_id,
            "user_text": user_text,
            "bot_response": bot_response,
            "urgency": urgency,
            "language": detected_lang,
            "audio_url": f"/audio/{audio_filename}" if audio_filename else "",
            "tool_calls": tool_calls,
        }

    except Exception as e:
        print(f"[Main] Error in /chat: {e}")
        return JSONResponse(
            content={"error": str(e), "session_id": session_id},
            status_code=500,
        )


@app.get("/history/{session_id}")
async def history(session_id: str):
    """
    Get chat history for a specific session.

    Args:
        session_id: The session to retrieve history for

    Returns:
        JSON list of interactions
    """
    return get_history(session_id)


@app.get("/logs")
async def logs():
    """
    Get aggregated dashboard statistics.

    Returns:
        JSON with total sessions, interactions, urgency/language distribution
    """
    return get_dashboard_stats()


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """
    Serve a generated TTS audio file.

    Args:
        filename: Name of the audio file

    Returns:
        MP3 audio file
    """
    filepath = AUDIO_OUTPUT_DIR / filename
    if filepath.exists():
        return FileResponse(
            path=str(filepath),
            media_type="audio/mpeg",
            filename=filename,
        )
    return JSONResponse(content={"error": "Audio not found"}, status_code=404)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "AarogyaBot"}


# ── Serve Frontend Static Files ─────────────────────────────────────────────
# Mount the frontend directory to serve HTML, CSS, and JS files
frontend_dir = PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn  # type: ignore # pyright: ignore
    from backend.config import HOST, PORT  # type: ignore # pyright: ignore
    uvicorn.run(app, host=HOST, port=PORT)
