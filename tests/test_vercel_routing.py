from fastapi.testclient import TestClient

from api.index import app


def test_native_routing_root():
    assert TestClient(app).get("/").status_code == 200


def test_native_routing_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_native_routing_tasks():
    r = TestClient(app).get("/api/tasks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_native_routing_static():
    assert TestClient(app).get("/static/styles.css").status_code == 200
    assert TestClient(app).get("/static/app.js").status_code == 200
