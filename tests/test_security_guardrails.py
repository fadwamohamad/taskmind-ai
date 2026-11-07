import subprocess
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models import ExtractedTask, ExtractResponse
from app.services.ai_service import AiBadResponseError, AiUnavailableError

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client, monkeypatch
    app.dependency_overrides.clear()


def _mock_extract(monkeypatch, func):
    monkeypatch.setattr("app.routers.extract.extract_tasks", func, raising=True)


def _node(code):
    result = subprocess.run(
        ["node", "-e", textwrap.dedent(code).strip()],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"node failed:\n{result.stdout}\n{result.stderr}"


def test_maximum_title_length_rejected_not_truncated(client):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "x" * 201})
    assert r.status_code == 422
    assert c.get("/api/tasks").json() == []


def test_title_exactly_200_accepted(client):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "x" * 200})
    assert r.status_code == 201
    assert r.json()["title"] == "x" * 200


def test_max_details_length_rejected(client):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "ok", "details": "d" * 5001})
    assert r.status_code == 422
    assert c.get("/api/tasks").json() == []


def test_max_assignee_length_rejected(client):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "ok", "assignee": "a" * 121})
    assert r.status_code == 422
    assert c.get("/api/tasks").json() == []


def test_short_title_stripped_rejected(client):
    c, _ = client
    assert c.post("/api/tasks", json={"title": "   "}).status_code == 422
    created = c.post("/api/tasks", json={"title": "  padded  "})
    assert created.status_code == 201
    assert created.json()["title"] == "padded"
    patched = c.patch(f"/api/tasks/{created.json()['id']}", json={"title": "   "})
    assert patched.status_code == 422


def test_invalid_status_rejected(client):
    c, _ = client
    created = c.post("/api/tasks", json={"title": "ok"})
    assert created.status_code == 201
    r = c.patch(f"/api/tasks/{created.json()['id']}", json={"status": "pending"})
    assert r.status_code == 422


@pytest.mark.parametrize("lang", ["de", "DE", "xx", ""])
def test_invalid_language_rejected(client, lang):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "ok", "language": lang})
    assert r.status_code == 422


def test_invalid_language_patch_rejected(client):
    c, _ = client
    created = c.post("/api/tasks", json={"title": "ok"})
    r = c.patch(f"/api/tasks/{created.json()['id']}", json={"language": "de"})
    assert r.status_code == 422


@pytest.mark.parametrize("bad_date", ["not-a-date", "2026-13-01", "20/11/2026", "2026-02-30"])
def test_malformed_date_rejected(client, bad_date):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "ok", "due_date": bad_date})
    assert r.status_code == 422


def test_malformed_date_patch_rejected(client):
    c, _ = client
    created = c.post("/api/tasks", json={"title": "ok"})
    r = c.patch(f"/api/tasks/{created.json()['id']}", json={"due_date": "bad"})
    assert r.status_code == 422


@pytest.mark.parametrize("field", ["title", "details", "priority", "status", "language"])
def test_patch_explicit_null_rejected(client, field):
    c, _ = client
    created = c.post("/api/tasks", json={"title": "ok", "assignee": "Sara", "due_date": "2026-11-20"})
    assert created.status_code == 201
    r = c.patch(f"/api/tasks/{created.json()['id']}", json={field: None})
    assert r.status_code == 422


def test_patch_null_clears_nullable_fields(client):
    c, _ = client
    created = c.post(
        "/api/tasks",
        json={"title": "ok", "assignee": "Sara", "due_date": "2026-11-20"},
    )
    tid = created.json()["id"]
    r1 = c.patch(f"/api/tasks/{tid}", json={"assignee": None})
    assert r1.status_code == 200 and r1.json()["assignee"] is None
    r2 = c.patch(f"/api/tasks/{tid}", json={"due_date": None})
    assert r2.status_code == 200 and r2.json()["due_date"] is None


def test_create_priority_null_rejected(client):
    c, _ = client
    r = c.post("/api/tasks", json={"title": "ok", "priority": None})
    assert r.status_code == 422


def test_extract_empty_and_oversized_rejected(client):
    c, monkeypatch = client
    _mock_extract(monkeypatch, lambda text: ExtractResponse(tasks=[]))
    assert c.post("/api/extract", json={"text": "short"}).status_code == 422
    assert c.post("/api/extract", json={"text": "x" * 8001}).status_code == 422


def test_extract_exactly_8000_accepted(client):
    c, monkeypatch = client
    _mock_extract(monkeypatch, lambda text: ExtractResponse(tasks=[]))
    r = c.post("/api/extract", json={"text": "x" * 8000})
    assert r.status_code == 200


def test_more_than_10_tasks_enforced_at_api(client):
    c, monkeypatch = client

    def fake(text):
        tasks = [
            ExtractedTask(title=f"T{i}", details="", assignee=None, priority=None, due_date=None, language="en")
            for i in range(11)
        ]
        return ExtractResponse(tasks=tasks)

    _mock_extract(monkeypatch, fake)
    r = c.post("/api/extract", json={"text": "notes with many tasks inside"})
    assert r.status_code == 502
    assert c.get("/api/tasks").json() == []


def test_extract_never_persists(client):
    c, monkeypatch = client

    def fake(text):
        return ExtractResponse(tasks=[ExtractedTask(title="T", details="", assignee=None, priority=None, due_date=None, language="en")])

    _mock_extract(monkeypatch, fake)
    r = c.post("/api/extract", json={"text": "notes with a task to extract"})
    assert r.status_code == 200
    assert c.get("/api/tasks").json() == []


def test_ai_html_output_preserved_as_text(client):
    c, monkeypatch = client
    payload = "<script>alert(1)</script>"
    details = '<img src=x onerror="alert(1)">'

    def fake(text):
        return ExtractResponse(tasks=[ExtractedTask(title=payload, details=details, assignee=None, priority=None, due_date=None, language="en")])

    _mock_extract(monkeypatch, fake)
    r = c.post("/api/extract", json={"text": "notes with html-like content"})
    assert r.status_code == 200
    assert r.json()["tasks"][0]["title"] == payload
    assert c.get("/api/tasks").json() == []

    created = c.post("/api/tasks", json={"title": payload, "details": details})
    assert created.status_code == 201
    fetched = c.get(f"/api/tasks/{created.json()['id']}")
    assert fetched.json()["title"] == payload


def test_api_errors_do_not_expose_internal_details(client):
    c, monkeypatch = client
    secret = "SECRET_NOTE_PHRASE_XYZ"

    def unavailable(text):
        raise AiUnavailableError("AI service is not configured.")

    _mock_extract(monkeypatch, unavailable)
    r = c.post("/api/extract", json={"text": f"meeting {secret} plus more text"})
    assert r.status_code == 503
    for body in [r.text]:
        assert "Traceback" not in body
        assert "ANTHROPIC_API_KEY" not in body
        assert "sk-ant-" not in body
        assert secret not in body
        assert "File \"" not in body

    def bad(text):
        raise AiBadResponseError("AI extraction failed.")

    _mock_extract(monkeypatch, bad)
    r2 = c.post("/api/extract", json={"text": f"meeting {secret} plus more text"})
    assert r2.status_code == 502
    assert "Traceback" not in r2.text
    assert secret not in r2.text

    assert c.get("/api/tasks/999999").status_code == 404
    body404 = c.get("/api/tasks/999999").text
    assert "Traceback" not in body404


def test_no_api_key_exposure_in_static_assets(client):
    c, _ = client
    for path in ["/", "/static/index.html", "/static/app.js", "/static/styles.css"]:
        r = c.get(path)
        assert r.status_code == 200
        assert "ANTHROPIC_API_KEY" not in r.text
        assert "sk-ant-" not in r.text
    for name in ["index.html", "app.js", "styles.css"]:
        content = (STATIC / name).read_text(encoding="utf-8")
        assert "ANTHROPIC_API_KEY" not in content
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js
    assert "textContent" in js
    assert "/api/extract" in js
    assert "/api/tasks" in js


def test_sql_injection_treated_as_data(client):
    c, _ = client
    payload = "'; DROP TABLE task; --"
    created = c.post("/api/tasks", json={"title": payload})
    assert created.status_code == 201
    assert created.json()["title"] == payload
    tid = created.json()["id"]
    assert c.get(f"/api/tasks/{tid}").json()["title"] == payload
    assert len(c.get("/api/tasks").json()) == 1
    assert c.delete(f"/api/tasks/{tid}").status_code == 204
    assert c.get("/api/tasks").json() == []


def test_path_traversal_blocked(client):
    c, _ = client
    for path in ["/static/../app/main.py", "/app/main.py", "/static/%2e%2e/app/main.py"]:
        r = c.get(path)
        assert "FastAPI(title" not in r.text
        assert "from fastapi" not in r.text


def test_no_sensitive_logging_in_code():
    assert "print(" not in (ROOT / "app" / "services" / "ai_service.py").read_text(encoding="utf-8")
    assert "print(" not in (ROOT / "app" / "routers" / "extract.py").read_text(encoding="utf-8")
    assert "print(" not in (ROOT / "app" / "routers" / "tasks.py").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" not in (ROOT / "app" / "static" / "app.js").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" not in (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")


def test_duplicate_action_prevention():
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert js.count("disabled = true") >= 4
    assert "disabled = false" in js
    assert "extractBtn.disabled" in js


def test_delete_confirmation():
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "confirm(" in js
    assert "deleteConfirm" in js
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        for (const lg of ["en", "ar", "fr"]) {
          const v = i18n.TRANSLATIONS[lg]["deleteConfirm"];
          if (!v || !String(v).trim()) process.exit(1);
        }
        """
    )
    confirm_idx = js.find("confirm(")
    delete_idx = js.find("method: \"DELETE\"")
    assert 0 <= confirm_idx < delete_idx


def test_frontend_network_failure_handled():
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "await fetch" in js
    fetch_idx = js.find("await fetch")
    snippet = js[max(0, fetch_idx - 300):fetch_idx]
    assert "try" in snippet


def test_existing_crud_and_multilingual_intact(client):
    c, _ = client
    created = c.post(
        "/api/tasks",
        json={"title": "Write report", "details": "Summary", "assignee": "Sara", "priority": "high", "due_date": "2026-11-20", "language": "en"},
    )
    assert created.status_code == 201
    tid = created.json()["id"]
    assert c.get(f"/api/tasks/{tid}").status_code == 200
    assert c.patch(f"/api/tasks/{tid}", json={"status": "done"}).status_code == 200
    assert c.delete(f"/api/tasks/{tid}").status_code == 204
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const en = Object.keys(i18n.TRANSLATIONS.en).sort();
        for (const lg of ["ar", "fr"]) {
          if (JSON.stringify(Object.keys(i18n.TRANSLATIONS[lg]).sort()) !== JSON.stringify(en)) process.exit(1);
        }
        """
    )
