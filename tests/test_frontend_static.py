from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "app" / "static"


def test_static_files_exist():
    assert (STATIC / "index.html").exists()
    assert (STATIC / "styles.css").exists()
    assert (STATIC / "app.js").exists()


def test_frontend_contains_core_flow_hooks_and_security():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" not in html
    assert "ANTHROPIC_API_KEY" not in js
    for required in ["textarea", "extract", "/api/extract", "/api/tasks"]:
        assert required in (html + js)
    assert "innerHTML" not in js
    assert "textContent" in js
