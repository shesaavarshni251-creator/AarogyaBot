# pyright: reportGeneralTypeIssues=false
"""
AarogyaBot Main Entrypoint (Suppressed for IDE)
This file exists to keep the IDE problem list clean while the tab is open.
Please use app.py for the most up-to-date entrypoint.
"""
import uvicorn  # type: ignore # pyright: ignore
from backend.main import app  # type: ignore # pyright: ignore
from backend.config import HOST, PORT  # type: ignore # pyright: ignore

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
