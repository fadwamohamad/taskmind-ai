import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app


@pytest.fixture()
def client(tmp_path):
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
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def created(client):
    response = client.post(
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
    assert response.status_code == 201
    return response.json()


def test_create_valid_task(client):
    response = client.post(
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
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Write report"
    assert data["details"] == "Quarterly summary"
    assert data["assignee"] == "Sara"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-11-20"
    assert data["status"] == "todo"
    assert data["language"] == "en"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_defaults_priority_medium_and_status_todo(client):
    response = client.post("/api/tasks", json={"title": "Simple task"})
    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "medium"
    assert data["status"] == "todo"
    assert data["details"] == ""
    assert data["assignee"] is None
    assert data["due_date"] is None
    assert data["language"] == "unknown"


def test_create_strips_title_and_normalizes_assignee(client):
    response = client.post(
        "/api/tasks", json={"title": "   Padded title   ", "assignee": "   "}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Padded title"
    assert data["assignee"] is None


@pytest.mark.parametrize("title", ["", "   "])
def test_reject_empty_title(client, title):
    response = client.post("/api/tasks", json={"title": title})
    assert response.status_code == 422


def test_reject_invalid_priority(client):
    response = client.post(
        "/api/tasks", json={"title": "Valid title", "priority": "urgent"}
    )
    assert response.status_code == 422


def test_list_tasks(client, created):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Write report"


def test_list_tasks_ordered_newest_first(client, created):
    client.post("/api/tasks", json={"title": "Second task"})
    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert [t["title"] for t in tasks] == ["Second task", "Write report"]


def test_retrieve_a_task(client, created):
    response = client.get(f"/api/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_retrieve_missing_returns_404(client):
    response = client.get("/api/tasks/9999")
    assert response.status_code == 404


def test_update_task_title(client, created):
    response = client.patch(
        f"/api/tasks/{created['id']}", json={"title": "  New title  "}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_update_task_status(client, created):
    response = client.patch(
        f"/api/tasks/{created['id']}", json={"status": "done"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_clear_assignee(client, created):
    response = client.patch(
        f"/api/tasks/{created['id']}", json={"assignee": None}
    )
    assert response.status_code == 200
    assert response.json()["assignee"] is None


def test_clear_due_date(client, created):
    response = client.patch(
        f"/api/tasks/{created['id']}", json={"due_date": None}
    )
    assert response.status_code == 200
    assert response.json()["due_date"] is None


@pytest.mark.parametrize(
    "field",
    ["title", "details", "priority", "status", "language"],
)
def test_reject_invalid_patch_null_values(client, created, field):
    response = client.patch(
        f"/api/tasks/{created['id']}", json={field: None}
    )
    assert response.status_code == 422


def test_update_changes_updated_at(client, created):
    original_updated_at = created["updated_at"]
    response = client.patch(
        f"/api/tasks/{created['id']}", json={"title": "Updated title"}
    )
    assert response.status_code == 200
    assert response.json()["updated_at"] >= original_updated_at


def test_delete_task(client, created):
    response = client.delete(f"/api/tasks/{created['id']}")
    assert response.status_code == 204
    follow_up = client.get(f"/api/tasks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_missing_returns_404(client):
    response = client.delete("/api/tasks/9999")
    assert response.status_code == 404
