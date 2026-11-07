# Architecture

## Overview

```
Browser (vanilla HTML/CSS/JS) ──► FastAPI ──► Gemini extraction (structured JSON)
                                      └──► SQLModel ──► SQLite (taskmind.db)
```

Single-page UI talks to the same FastAPI process. Extraction never writes to the database; saving is explicit via task CRUD.

## Frontend

- `app/static/index.html` — hero, notes textarea, drafts, saved list; `dir`/`lang` set by JS.
- `app/static/styles.css` — white/lavender design system, responsive, `[dir="rtl"]` aware.
- `app/static/app.js` — `TaskMindI18n` dictionary (en/ar/fr), `POST /api/extract`, `GET/POST/PATCH/DELETE /api/tasks`. Renders only via `textContent`/`value` (no `innerHTML`); language persisted in `localStorage["taskmind-lang"]`; task content never translated.

## Backend

- `app/main.py` — FastAPI app, lifespan `create_db()`, `GET /health`, `GET /` static, `/static` mount, routers included.
- `app/models.py` — `Task` ((SQLite `task`) + Pydantic `TaskCreate/TaskUpdate/TaskRead`, `ExtractRequest/ExtractedTask/ExtractResponse` (title 1–200, details ≤5000, assignee ≤120, priority `low|medium|high`, ISO `due_date`, language `ar|en|fr|unknown`, strip/normalize + explicit-null rejection on PATCH).
- `app/db.py` — `create_engine(sqlite:///./taskmind.db)`, `create_db()`, per-request `Session` via `get_session`.
- `app/routers/extract.py` — `POST /api/extract` (10–8000 chars → `ExtractResponse`); 422 invalid input, 503 missing `GEMINI_API_KEY`, 502 provider/validation failure, >10 tasks → 502. No DB writes.
- `app/routers/tasks.py` — CRUD on `Task`; newest-first list; `updated_at` on PATCH.

## AI service (`app/services/ai_service.py`)

- `google.genai.Client(api_key=$GEMINI_API_KEY)`, model `$GEMINI_MODEL` (default `gemini-3.5-flash-lite`).
- System prompt: explicit actions only, never invent assignee/date, `null` when unsupported, preserve language, untrusted-input guardrails.
- Structured JSON (`response_mime_type="application/json"`, `response_schema` mirroring `ExtractResponse`) → `ExtractResponse` validation → ≤10 check → return (never persist). Diagnostics log only `exception_type/code/gemini_status/category/model` (no keys/notes/messages).

## Evaluation

`evaluation/` (runner + metrics + `dataset.json`, 24 examples) is offline fixture evaluation; see [evaluation.md](evaluation.md). Live Gemini evaluation reuses `compute_metrics` with live predictions.

## Key config

- `GEMINI_API_KEY` (server-only), `GEMINI_MODEL` (overridable), `DATABASE_URL` (default local SQLite). Copy `.env.example` → `.env`.
