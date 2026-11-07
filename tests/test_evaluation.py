import json
import subprocess
import sys
from pathlib import Path

import pytest

from evaluation.metrics import compute_metrics, evaluate_example, match_tasks
from evaluation.runner import load_dataset, main, validate_dataset

DATASET_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "dataset.json"


def _task(title, details="", assignee=None, priority=None, due_date=None, language="en"):
    return {
        "title": title,
        "details": details,
        "assignee": assignee,
        "priority": priority,
        "due_date": due_date,
        "language": language,
    }


def test_dataset_loads_and_has_at_least_20():
    data = load_dataset(str(DATASET_PATH))
    assert isinstance(data, list)
    assert len(data) >= 20


def test_dataset_covers_languages():
    data = load_dataset(str(DATASET_PATH))
    langs = {ex.get("language") for ex in data}
    assert {"ar", "en", "fr"} <= langs
    for lang in ["ar", "en", "fr"]:
        assert sum(1 for ex in data if ex["language"] == lang) >= 2


def test_dataset_covers_scenarios():
    data = load_dataset(str(DATASET_PATH))
    all_tags = {t for ex in data for t in ex.get("tags", [])}
    for tag in [
        "multiple-actions",
        "no-tasks",
        "explicit-assignee",
        "no-assignee",
        "explicit-date",
        "ambiguous-date",
        "priority-support",
        "priority-null",
        "prompt-injection",
        "duplicates",
        "long-notes",
        "irrelevant-discussion",
    ]:
        assert tag in all_tags, f"missing scenario tag: {tag}"
    assert any(ex["expected"] == [] for ex in data)
    assert any(
        t["assignee"] for ex in data for t in ex["expected"] if t["assignee"]
    )
    assert any(
        t["assignee"] is None for ex in data for t in ex["expected"]
    )
    assert any(t["due_date"] for ex in data for t in ex["expected"] if t["due_date"])
    assert any(t["priority"] == "high" for ex in data for t in ex["expected"])
    assert any(t["priority"] == "medium" for ex in data for t in ex["expected"])
    assert any(t["priority"] == "low" for ex in data for t in ex["expected"])
    assert any(t["priority"] is None for ex in data for t in ex["expected"])


def test_dataset_validation_rejects_bad_examples():
    bad = [
        {
            "id": "bad-1",
            "language": "en",
            "tags": [],
            "notes": "Some meeting notes with enough text here",
            "expected": [_task("T", priority="urgent")],
            "predicted": [_task("T")],
        }
    ]
    with pytest.raises(ValueError):
        validate_dataset(bad)
    bad_date = [
        {
            "id": "bad-2",
            "language": "en",
            "tags": [],
            "notes": "Some meeting notes with enough text here",
            "expected": [_task("T", due_date="20/11/2026")],
            "predicted": [_task("T")],
        }
    ]
    with pytest.raises(ValueError):
        validate_dataset(bad_date)
    good = [
        {
            "id": "good-1",
            "language": "en",
            "tags": [],
            "notes": "Some meeting notes with enough text here",
            "expected": [_task("T")],
            "predicted": [_task("T")],
        }
    ]
    validate_dataset(good)


def test_perfect_predictions_score_one():
    expected = [_task("Write report", assignee="Sara", priority="high", due_date="2026-11-20")]
    predicted = [_task("  Write   report  ", assignee="Sara", priority="high", due_date="2026-11-20")]
    metrics = compute_metrics(
        [{"id": "e1", "language": "en", "tags": [], "notes": "x", "expected": expected, "predicted": predicted}]
    )
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["title_match_rate"] == 1.0
    assert metrics["assignee_accuracy"] == 1.0
    assert metrics["due_date_accuracy"] == 1.0
    assert metrics["priority_accuracy"] == 1.0
    assert metrics["language_preservation_accuracy"] == 1.0


def test_one_to_one_matching():
    expected = [_task("Same title")]
    predicted = [_task("Same title"), _task("Same title")]
    matches, tp = match_tasks(expected, predicted)
    assert tp == 1
    assert len(matches) == 1
    assert matches[0][0] == 0


def test_reordered_predictions():
    expected = [_task("A"), _task("B")]
    predicted = [_task("B"), _task("A")]
    metrics = compute_metrics(
        [{"id": "e1", "language": "en", "tags": [], "notes": "x", "expected": expected, "predicted": predicted}]
    )
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0


def test_empty_expected_and_predicted():
    metrics = compute_metrics(
        [{"id": "e1", "language": "en", "tags": [], "notes": "x", "expected": [], "predicted": []}]
    )
    assert metrics["empty_result_accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0


def test_missing_and_extra_tasks():
    metrics_missing = compute_metrics(
        [
            {
                "id": "e1",
                "language": "en",
                "tags": [],
                "notes": "x",
                "expected": [_task("A"), _task("B")],
                "predicted": [_task("A")],
            }
        ]
    )
    assert metrics_missing["recall"] == 0.5
    assert metrics_missing["precision"] == 1.0
    metrics_extra = compute_metrics(
        [
            {
                "id": "e1",
                "language": "en",
                "tags": [],
                "notes": "x",
                "expected": [_task("A")],
                "predicted": [_task("A"), _task("B")],
            }
        ]
    )
    assert metrics_extra["precision"] == 0.5
    assert metrics_extra["recall"] == 1.0
    expected_f1 = 2 * 1.0 * 0.5 / (1.0 + 0.5)
    assert metrics_extra["f1_score"] == pytest.approx(expected_f1)


def test_incorrect_fields_lower_accuracy():
    expected = [_task("A", assignee="Sara", priority="high", due_date="2026-11-20", language="en")]
    predicted = [_task("A", assignee="Omar", priority="low", due_date="2026-11-21", language="fr")]
    metrics = compute_metrics(
        [{"id": "e1", "language": "en", "tags": [], "notes": "x", "expected": expected, "predicted": predicted}]
    )
    assert metrics["precision"] == 1.0
    assert metrics["title_match_rate"] == 1.0
    assert metrics["assignee_accuracy"] == 0.0
    assert metrics["due_date_accuracy"] == 0.0
    assert metrics["priority_accuracy"] == 0.0
    assert metrics["language_preservation_accuracy"] == 0.0


def test_deterministic_output():
    examples = [
        {"id": "e1", "language": "en", "tags": [], "notes": "x", "expected": [_task("A")], "predicted": [_task("A")]}
    ]
    m1 = compute_metrics(examples)
    m2 = compute_metrics(examples)
    assert m1 == m2
    f1 = evaluate_example(examples[0])
    f2 = evaluate_example(examples[0])
    assert f1 == f2


def test_threshold_failure_exit_nonzero():
    code = main(["--min-f1", "2.0"])
    assert code != 0
    code_ok = main(["--min-f1", "0.0"])
    assert code_ok == 0


def test_dataset_file_is_valid_json_with_expected_shape():
    raw = DATASET_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert len(data) >= 20
    validate_dataset(data)


def test_no_network_calls_during_evaluation(monkeypatch):
    import socket

    def blocked(*args, **kwargs):
        raise RuntimeError("network blocked")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    code = main(["--min-f1", "0.0"])
    assert code == 0
