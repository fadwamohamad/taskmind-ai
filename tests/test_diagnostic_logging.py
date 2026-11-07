import json
import logging
from types import SimpleNamespace

import pytest

from app.services.ai_service import AiBadResponseError, extract_tasks


def _gemini_response(tasks):
    return SimpleNamespace(text=json.dumps({"tasks": tasks}))


class _FakeModels:
    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return self._response


class _FakeClient:
    def __init__(self, response=None, exc=None):
        self.models = _FakeModels(response=response, exc=exc)


def _api_error(code, status, message="failure"):
    from google.genai.errors import APIError

    return APIError(code, {"error": {"status": status, "message": message, "code": code}})


def _task(title="Write report", **overrides):
    base = {
        "title": title,
        "details": "Quarterly summary",
        "assignee": "Sara",
        "priority": "high",
        "due_date": "2026-11-20",
        "language": "en",
    }
    base.update(overrides)
    return base


SECRET_KEY = "VERY_SECRET_GEMINI_KEY_XYZ"
SECRET_NOTE = "SECRET_MEETING_NOTE_XYZ"


@pytest.fixture(autouse=True)
def _cap_log_level(caplog):
    caplog.set_level(logging.WARNING, logger="app.services.ai_service")


def test_authentication_error_logged_safely(caplog):
    exc = _api_error(401, "UNAUTHENTICATED", f"bad key {SECRET_KEY} {SECRET_NOTE}")
    client = _FakeClient(exc=exc)
    with pytest.raises(AiBadResponseError):
        extract_tasks(f"notes {SECRET_NOTE} with tasks", client=client)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    text = record.getMessage()
    assert "exception_type=APIError" in text
    assert "code=401" in text
    assert "gemini_status=UNAUTHENTICATED" in text
    assert "category=authentication" in text
    assert "gemini-3.5-flash-lite" in text
    assert SECRET_KEY not in text
    assert SECRET_NOTE not in text
    assert "bad key" not in text


def test_quota_error_logged_safely(caplog):
    exc = _api_error(429, "RESOURCE_EXHAUSTED", f"quota {SECRET_KEY}")
    client = _FakeClient(exc=exc)
    with pytest.raises(AiBadResponseError):
        extract_tasks(f"notes {SECRET_NOTE} tasks", client=client)
    text = caplog.records[0].getMessage()
    assert "code=429" in text
    assert "category=quota" in text
    assert SECRET_KEY not in text
    assert SECRET_NOTE not in text


def test_model_not_found_logged_safely(caplog):
    exc = _api_error(404, "NOT_FOUND", "model missing")
    client = _FakeClient(exc=exc)
    with pytest.raises(AiBadResponseError):
        extract_tasks("meeting notes with tasks inside", client=client)
    text = caplog.records[0].getMessage()
    assert "category=model-not-found" in text
    assert "code=404" in text


def test_invalid_request_logged_safely(caplog):
    exc = _api_error(400, "INVALID_ARGUMENT", "invalid request")
    client = _FakeClient(exc=exc)
    with pytest.raises(AiBadResponseError):
        extract_tasks("meeting notes with tasks inside", client=client)
    text = caplog.records[0].getMessage()
    assert "category=invalid-request" in text
    assert "code=400" in text


def test_unknown_error_logged_safely(caplog):
    client = _FakeClient(exc=RuntimeError(f"boom {SECRET_KEY}"))
    with pytest.raises(AiBadResponseError):
        extract_tasks("meeting notes with tasks inside", client=client)
    text = caplog.records[0].getMessage()
    assert "category=unknown" in text
    assert SECRET_KEY not in text
    assert "boom" not in text


def test_safety_block_logged_safely(caplog):
    response = SimpleNamespace(
        text="",
        candidates=[SimpleNamespace(finish_reason="SAFETY")],
    )
    client = _FakeClient(response=response)
    with pytest.raises(AiBadResponseError):
        extract_tasks(f"notes {SECRET_NOTE} tasks", client=client)
    text = caplog.records[0].getMessage()
    assert "category=safety-block" in text
    assert "SAFETY" in text
    assert SECRET_NOTE not in text


def test_empty_response_logged_safely(caplog):
    response = SimpleNamespace(
        text=None,
        candidates=[SimpleNamespace(finish_reason="STOP")],
    )
    client = _FakeClient(response=response)
    with pytest.raises(AiBadResponseError):
        extract_tasks("meeting notes with tasks inside", client=client)
    assert "category=empty-response" in caplog.records[0].getMessage()


def test_parsing_failure_logged_safely(caplog):
    response = SimpleNamespace(text="not-json")
    client = _FakeClient(response=response)
    with pytest.raises(AiBadResponseError):
        extract_tasks(f"notes {SECRET_NOTE} tasks", client=client)
    text = caplog.records[0].getMessage()
    assert "category=parsing" in text
    assert SECRET_NOTE not in text
    assert "not-json" not in text


def test_validation_failure_logged_safely(caplog):
    client = _FakeClient(response=_gemini_response([_task(due_date="not-a-date")]))
    with pytest.raises(AiBadResponseError):
        extract_tasks(f"notes {SECRET_NOTE} tasks", client=client)
    assert "category=validation" in caplog.records[0].getMessage()


def test_success_does_not_log_warning(caplog):
    client = _FakeClient(response=_gemini_response([_task()]))
    result = extract_tasks("meeting notes with tasks inside", client=client)
    assert len(result.tasks) == 1
    assert len(caplog.records) == 0
