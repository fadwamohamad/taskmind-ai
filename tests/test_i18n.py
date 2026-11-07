import subprocess
import textwrap

from fastapi.testclient import TestClient
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "app" / "static"


def _node(code):
    script = textwrap.dedent(code).strip()
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"node failed:\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout


def test_default_language_is_english():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const store = new Map();
        const storage = {
          getItem: (k) => (store.has(k) ? store.get(k) : null),
          setItem: (k, v) => store.set(k, String(v)),
        };
        if (i18n.readPreferredLanguage(storage) !== "en") process.exit(1);
        if (i18n.directionFor("en") !== "ltr") process.exit(1);
        """
    )


def test_arabic_selection_sets_rtl():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const doc = { documentElement: { lang: "", dir: "" } };
        i18n.applyDocumentLanguage(doc, "ar");
        if (doc.documentElement.lang !== "ar") process.exit(1);
        if (doc.documentElement.dir !== "rtl") process.exit(1);
        """
    )


def test_english_selection_sets_ltr():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const doc = { documentElement: { lang: "", dir: "" } };
        i18n.applyDocumentLanguage(doc, "en");
        if (doc.documentElement.lang !== "en") process.exit(1);
        if (doc.documentElement.dir !== "ltr") process.exit(1);
        """
    )


def test_french_selection_sets_ltr():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const doc = { documentElement: { lang: "", dir: "" } };
        i18n.applyDocumentLanguage(doc, "fr");
        if (doc.documentElement.lang !== "fr") process.exit(1);
        if (doc.documentElement.dir !== "ltr") process.exit(1);
        """
    )


def test_selected_language_persists_in_localstorage():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const store = new Map();
        const storage = {
          getItem: (k) => (store.has(k) ? store.get(k) : null),
          setItem: (k, v) => store.set(k, String(v)),
        };
        i18n.persistLanguage(storage, "ar");
        if (store.get(i18n.STORAGE_KEY) !== "ar") process.exit(1);
        if (i18n.readPreferredLanguage(storage) !== "ar") process.exit(1);
        """
    )


def test_saved_language_restored_after_reload():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const store = new Map([[ "taskmind-lang", "fr" ]]);
        const storage = {
          getItem: (k) => (store.has(k) ? store.get(k) : null),
          setItem: (k, v) => store.set(k, String(v)),
        };
        const lang = i18n.readPreferredLanguage(storage);
        if (lang !== "fr") process.exit(1);
        const doc = { documentElement: { lang: "", dir: "" } };
        i18n.applyDocumentLanguage(doc, lang);
        if (doc.documentElement.dir !== "ltr") process.exit(1);
        """
    )


def test_invalid_localstorage_falls_back_to_english():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const mk = (v) => {
          const store = new Map([["taskmind-lang", v]]);
          return {
            getItem: (k) => (store.has(k) ? store.get(k) : null),
            setItem: (k, v) => store.set(k, String(v)),
          };
        };
        for (const bad of ["xx", "de", "", "EN", null]) {
          if (i18n.readPreferredLanguage(mk(bad)) !== "en") process.exit(1);
        }
        """
    )


def test_all_required_translation_keys_exist():
    _node(
        r"""
        const i18n = require("./app/static/app.js");
        const t = i18n.TRANSLATIONS;
        const langs = ["en", "ar", "fr"];
        for (const lg of langs) if (!t[lg]) process.exit(1);
        const en = Object.keys(t.en).sort();
        if (!en.length) process.exit(1);
        for (const lg of langs) {
          const keys = Object.keys(t[lg]).sort();
          if (JSON.stringify(keys) !== JSON.stringify(en)) process.exit(1);
          for (const k of en) if (!String(t[lg][k]).trim()) process.exit(1);
        }
        for (const k of ["tagline","extractBtn","draftsEmpty","savedEmpty","saveBtn","markDone","deleteBtn","todo","done","low","medium","high"]) {
          if (!t.en[k] || !t.ar[k] || !t.fr[k]) process.exit(1);
        }
        """
    )


def test_changing_ui_language_does_not_modify_task_content():
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" not in js
    for forbidden in ["t(draft.title", "t(draft.details", "t(task.title", "t(task.details"]:
        assert forbidden not in js
    assert "draft.language" in js
    assert "task.language" in js


def test_existing_extraction_and_crud_unaffected():
    from sqlmodel import Session, SQLModel, create_engine

    from app.db import get_session
    from app.main import app
    import app.routers.extract as ex
    from app.models import ExtractedTask, ExtractResponse

    engine = create_engine(
        "sqlite:///./test_i18n_tmp.db", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    original = ex.extract_tasks
    ex.extract_tasks = lambda text: ExtractResponse(
        tasks=[ExtractedTask(title="Write report", details="", assignee=None, priority=None, due_date=None, language="en")]
    )
    try:
        with TestClient(app) as c:
            assert c.get("/health").json() == {"status": "ok"}
            r = c.post("/api/extract", json={"text": "Sara will write the report"})
            assert r.status_code == 200
            assert r.json()["tasks"][0]["title"] == "Write report"
            created = c.post(
                "/api/tasks",
                json={"title": "Write report", "language": "en"},
            )
            assert created.status_code == 201
    finally:
        ex.extract_tasks = original
        app.dependency_overrides.clear()
        SQLModel.metadata.drop_all(engine)
