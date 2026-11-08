"""Vercel serverless entry point.

Delegates all traffic to the existing FastAPI application in ``app.main``.
No business logic lives here — `app/main.py` remains the single source of
truth for routes, models, and static serving (preserved verbatim so Vercel's
global `/(.*) -> /api/index` rewrite does not duplicate or conflict).
"""

from app.main import app

__all__ = ["app"]
