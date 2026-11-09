"""Vercel serverless entry point.

Vercel's official FastAPI detection loads the `app` instance from a
recognized entrypoint (here ``api/index.py``) and serves the whole FastAPI
router natively — every request path is forwarded to FastAPI, so no
catch-all rewrite or path-restoration middleware is needed.
"""

from app.main import app

__all__ = ["app"]
