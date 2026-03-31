"""
AarogyaBot Root Entrypoint
This file allows the IDE to find the FastAPI application easily.
"""
import uvicorn
from backend.main import app
from backend.config import HOST, PORT

if __name__ == "__main__":
    # This matches the internal backend entrypoint for consistency
    uvicorn.run(app, host=HOST, port=PORT)
