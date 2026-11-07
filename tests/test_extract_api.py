import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models import ExtractedTask, ExtractResponse
from app.services.ai_service import AiBadResponseError, AiUnavailableError


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
    yield (TestClient(app), monkeypatch)
    app.dependency_overrides.clear()


@pytest.fixture()
def mocked_extract(client):
    test_client, monkeypatch = client
    calls = []

    def fake_extract(text):
        calls.append(text)
        return ExtractResponse(
            tasks=[
                ExtractedTask(
                    title="Write report",
                    details="Quarterly summary",
                    assignee="Sara",
                    priority="high",
                    due_date="2026-11-20",
                    language="en",
                ),
                ExtractedTask(
                    title="Prepare slides",
                    details="",
                    assignee=None,
                    priority=None,
                    due_date=None,
                    language="en",
                ),
            ]
        )

    monkeypatch.setattr(
        "app.routers.extract.extract_tasks", fake_extract, raising=True
    )
    return test_client, calls


def test_extract_successful_response(mocked_extract):
    test_client, calls = mocked_extract
    response = test_client.post(
        "/api/extract", json={"text": "Sara will write the report"}
    )
    assert response.status_code == 200
    data = response.json()
    assert calls == ["Sara will write the report"]
    assert len(data["tasks"]) == 2
    assert data["tasks"][0]["title"] == "Write report"
    assert data["tasks"][1]["priority"] is None
    assert data["tasks"][1]["assignee"] is None


def test_extract_invalid_input_returns_422(client):
    test_client, _ = client
    response = test_client.post("/api/extract", json={"text": "short"})
    assert response.status_code == 422
    too_long = test_client.post(
        "/api/extract", json={"text": "x" * 8001}
    )
    assert too_long.status_code == 422


def test_extract_missing_api_config_returns_503(client):
    test_client, monkeypatch = client

    def fake_extract(text):
        raise AiUnavailableError("AI service is not configured.")

    monkeypatch.setattr(
        "app.routers.extract.extract_tasks", fake_extract, raising=True
    )
    response = test_client.post(
        "/api/extract", json={"text": "Sara will write the report"}
    )
    assert response.status_code == 503
    body = response.text
    assert "ANTHROPIC_API_KEY" not in body
    assert "Sara will write" not in body
    assert "Traceback" not in body


def test_extract_extraction_failure_returns_502(client):
    test_client, monkeypatch = client

    def fake_extract(text):
        raise AiBadResponseError("AI extraction failed.")

    monkeypatch.setattr(
        "app.routers.extract.extract_tasks", fake_extract, raising=True
    )
    response = test_client.post(
        "/api/extract", json={"text": "Sara will write the report"}
    )
    assert response.status_code == 502
    assert "Traceback" not in response.text


def test_extracted_tasks_are_not_automatically_saved(mocked_extract):
    test_client, _ = mocked_extract
    extract = test_client.post(
        "/api/extract", json={"text": "Sara will write the report"}
    )
    assert extract.status_code == 200
    listing = test_client.get("/api/tasks")
    assert listing.status_code == 200
    assert listing.json() == []


def test_existing_crud_still_works(client):
    test_client, _ = client
    created = test_client.post(
        "/api/tasks",
        json={
            "title": "Write report",
            "details": "Quarterly summary",
            "assignee": "Sara",
            "priority": "high",
            "due_date": "2026-11-20",
            "language": "en",
        },
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    fetched = test_client.get(f"/api/tasks/{task_id}")
    assert fetched.status_code == 200
    updated = test_client.patch(
        f"/api/tasks/{task_id}", json={"status": "done"}
    )
    assert updated.status_code == 200
    deleted = test_client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 204
