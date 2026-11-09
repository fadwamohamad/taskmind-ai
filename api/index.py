"""Vercel serverless entry point.

Delegates all traffic to the existing FastAPI application in ``app.main``.
No business logic lives here — `app/main.py` remains the single source of
truth for routes, models, and static serving (preserved verbatim so Vercel's
global `/(.*) -> /api/index` rewrite does not duplicate or conflict).
"""

from app.main import app as _fastapi_app


class _RestorePathMiddleware:
    """Restore the original request path after Vercel's rewrite.

    Vercel rewrites ``/(.*)`` to ``/api/index``; the Python function receives
    ``scope["path"] == "/api/index"`` but forwards the original path in the
    ``x-matched-path`` header. A plain ``from app.main import app`` would
    therefore only ever route ``/api/index`` and return FastAPI's default
    404 for ``/``, ``/api/tasks``, etc.

    This ASGI shim restores ``scope["path"]``/``scope["raw_path"]`` from that
    header when present and well-formed, and otherwise leaves the request
    untouched (local ``TestClient`` / direct ``uvicorn`` behaviour).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers") or [])
            matched = headers.get(b"x-matched-path")
            if matched:
                try:
                    decoded = matched.decode("utf-8", errors="ignore").strip()
                except Exception:
                    decoded = ""
                if decoded.startswith("/") and decoded != "/api/index":
                    scope["path"] = decoded
                    scope["raw_path"] = decoded.encode("utf-8")
        await self.app(scope, receive, send)


app = _RestorePathMiddleware(_fastapi_app)

__all__ = ["app"]
