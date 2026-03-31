"""
AarogyaBot Deployment Entrypoint
This file is the primary entrypoint for cloud platforms (Vercel, Render, Railway, etc.)
It exposes the FastAPI 'app' object at the root level.
"""
import uvicorn
from backend.main import app
from backend.config import HOST, PORT

# Expose 'app' for platforms that look for it by name
# Usage: uvicorn app:app
application = app 

if __name__ == "__main__":
    # Local run support
    uvicorn.run(app, host=HOST, port=PORT)
