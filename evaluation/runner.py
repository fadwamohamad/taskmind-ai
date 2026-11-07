import argparse
import json
from datetime import date
from pathlib import Path

from evaluation.metrics import compute_metrics, evaluate_example

DEFAULT_DATASET = Path(__file__).resolve().parent / "dataset.json"
DEFAULT_THRESHOLDS = {
    "precision": 0.8,
    "recall": 0.8,
    "f1_score": 0.8,
    "title_match_rate": 0.8,
    "assignee_accuracy": 0.8,
    "due_date_accuracy": 0.8,
    "priority_accuracy": 0.8,
    "language_preservation_accuracy": 0.8,
    "empty_result_accuracy": 0.8,
}

_ALLOWED_PRIORITIES = {None, "low", "medium", "high"}
_ALLOWED_LANGUAGES = {"ar", "en", "fr"}


def _validate_task(task, ctx):
    if not isinstance(task, dict):
        raise ValueError(f"{ctx}: task must be an object")
    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{ctx}: title must be non-empty")
    if len(title.strip()) > 200:
        raise ValueError(f"{ctx}: title too long")
    details = task.get("details", "")
    if not isinstance(details, str) or len(details) > 5000:
        raise ValueError(f"{ctx}: invalid details")
    assignee = task.get("assignee")
    if assignee is not None:
        if not isinstance(assignee, str):
            raise ValueError(f"{ctx}: invalid assignee")
        if len(assignee.strip()) > 120:
            raise ValueError(f"{ctx}: assignee too long")
    if task.get("priority") not in _ALLOWED_PRIORITIES:
        raise ValueError(f"{ctx}: invalid priority")
    due = task.get("due_date")
    if due is not None:
        if not isinstance(due, str):
            raise ValueError(f"{ctx}: invalid due_date")
        try:
            date.fromisoformat(due.strip())
        except ValueError:
            raise ValueError(f"{ctx}: invalid due_date")
    if task.get("language") not in {"ar", "en", "fr", "unknown"}:
        raise ValueError(f"{ctx}: invalid language")


def validate_dataset(examples):
    if not isinstance(examples, list) or not examples:
        raise ValueError("dataset must be a non-empty list")
    for idx, ex in enumerate(examples):
        ctx = f"example[{idx}]"
        if not isinstance(ex, dict):
            raise ValueError(f"{ctx}: must be an object")
        if not isinstance(ex.get("id"), str) or not ex["id"].strip():
            raise ValueError(f"{ctx}: id required")
        if ex.get("language") not in _ALLOWED_LANGUAGES:
            raise ValueError(f"{ctx}: invalid language")
        notes = ex.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            raise ValueError(f"{ctx}: notes required")
        for field in ("expected", "predicted"):
            items = ex.get(field)
            if not isinstance(items, list):
                raise ValueError(f"{ctx}: {field} must be a list")
            for t_idx, task in enumerate(items):
                _validate_task(task, f"{ctx}.{field}[{t_idx}]")
    return True


def load_dataset(path):
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, dict) and "examples" in data:
        data = data["examples"]
    validate_dataset(data)
    return data


def check_thresholds(metrics, thresholds):
    failures = []
    for key, minimum in thresholds.items():
        value = metrics.get(key, 0.0)
        if value < minimum:
            failures.append(f"{key}={value:.3f} < {minimum:.3f}")
    return failures


def format_report(metrics, failures_by_example):
    lines = []
    lines.append("=== TaskMind AI Evaluation Report ===")
    lines.append(f"examples: {metrics['example_count']}")
    lines.append(f"expected: {metrics['expected_total']} predicted: {metrics['predicted_total']} tp: {metrics['tp']} fp: {metrics['fp']} fn: {metrics['fn']}")
    for key in ["precision", "recall", "f1_score", "title_match_rate", "assignee_accuracy", "due_date_accuracy", "priority_accuracy", "language_preservation_accuracy", "empty_result_accuracy"]:
        lines.append(f"{key}: {metrics[key]:.3f}")
    failures = [(ex_id, fl) for ex_id, fl in failures_by_example if fl]
    lines.append(f"failures: {len(failures)} example(s) with mismatches")
    for ex_id, fl in failures:
        lines.append(f"  {ex_id}: {'; '.join(fl)}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TaskMind AI evaluation runner")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--min-precision", type=float, default=DEFAULT_THRESHOLDS["precision"])
    parser.add_argument("--min-recall", type=float, default=DEFAULT_THRESHOLDS["recall"])
    parser.add_argument("--min-f1", type=float, default=DEFAULT_THRESHOLDS["f1_score"])
    parser.add_argument("--min-title", type=float, default=DEFAULT_THRESHOLDS["title_match_rate"])
    parser.add_argument("--min-assignee", type=float, default=DEFAULT_THRESHOLDS["assignee_accuracy"])
    parser.add_argument("--min-due-date", type=float, default=DEFAULT_THRESHOLDS["due_date_accuracy"])
    parser.add_argument("--min-priority", type=float, default=DEFAULT_THRESHOLDS["priority_accuracy"])
    parser.add_argument("--min-language", type=float, default=DEFAULT_THRESHOLDS["language_preservation_accuracy"])
    parser.add_argument("--min-empty", type=float, default=DEFAULT_THRESHOLDS["empty_result_accuracy"])
    args = parser.parse_args(argv)
    examples = load_dataset(args.dataset)
    metrics = compute_metrics(examples)
    per_example = [evaluate_example(ex) for ex in examples]
    failures_by_example = [(row["id"], row["failures"]) for row in per_example]
    thresholds = {
        "precision": args.min_precision,
        "recall": args.min_recall,
        "f1_score": args.min_f1,
        "title_match_rate": args.min_title,
        "assignee_accuracy": args.min_assignee,
        "due_date_accuracy": args.min_due_date,
        "priority_accuracy": args.min_priority,
        "language_preservation_accuracy": args.min_language,
        "empty_result_accuracy": args.min_empty,
    }
    print(format_report(metrics, failures_by_example))
    below = check_thresholds(metrics, thresholds)
    if below:
        print("BELOW THRESHOLD: " + "; ".join(below))
        return 1
    print("ALL THRESHOLDS MET")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
