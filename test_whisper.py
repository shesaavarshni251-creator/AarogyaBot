import whisper  # type: ignore # pyright: ignore
import os
import shutil

def test():
    """
    Diagnostic script to check Whisper and FFmpeg health.
    Includes suppressions to keep the IDE clean.
    """
    print("--- Whisper Environment Check ---")
    
    # ── FFmpeg Path Fix ──────────────────────────────────────────────────
    if not shutil.which("ffmpeg"):
        winget_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
        )
        if os.path.exists(winget_path):
            os.environ["PATH"] += os.pathsep + winget_path
            print(f"Added FFmpeg to PATH from: {winget_path}")

    # 1. Check FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    print(f"FFmpeg path: {ffmpeg_path}")
    if not ffmpeg_path:
        print("CRITICAL: FFmpeg not found in PATH!")
    else:
        print("SUCCESS: FFmpeg found.")
    
    # 2. Check Whisper Model Loading
    model_name = "base"
    print(f"Attempting to load Whisper model: {model_name}...")
    try:
        model = whisper.load_model(model_name)  # type: ignore # pyright: ignore
        print("SUCCESS: Whisper model loaded correctly.")
    except Exception as e:
        print(f"FAILURE: Could not load Whisper model: {e}")

if __name__ == "__main__":
    test()
