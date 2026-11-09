from fastapi.testclient import TestClient

from api.index import app


def _get_with_matched(path: str, matched: bytes | None):
    client = TestClient(app)
    headers = {}
    if matched is not None:
        headers["x-matched-path"] = matched.decode("utf-8", errors="ignore")
    return client.get(path, headers=headers)


def test_root_via_matched_header():
    r = _get_with_matched("/api/index", b"/")
    assert r.status_code == 200
    # root serves HTML in local/static mode or JSON fallback; either is 200
    assert r.headers.get("content-type", "").startswith(("text/html", "application/json"))


def test_health_via_matched_header():
    r = _get_with_matched("/api/index", b"/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_tasks_via_matched_header():
    r = _get_with_matched("/api/index", b"/api/tasks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_static_via_matched_header():
    r = _get_with_matched("/api/index", b"/static/styles.css")
    assert r.status_code == 200


def test_missing_header_falls_back():
    # Direct ASGI path (TestClient, no rewrite) still works
    client = TestClient(app)
    assert client.get("/health").status_code == 200


def test_malformed_header_falls_back():
    client = TestClient(app)
    r = client.get(
        "/health", headers={"x-matched-path": "not-a-path"}
    )
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
