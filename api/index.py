"""
Vercel API Entrypoint
This file is the specific entrypoint for Vercel's Python runtime.
"""
from backend.main import app

# This name is standard for Vercel
# Usage: vercel.json -> "dest": "api/index.py"
app = app
