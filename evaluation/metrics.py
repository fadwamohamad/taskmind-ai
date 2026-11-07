from datetime import date


def _norm_title(value):
    return " ".join(str(value or "").strip().split())


def _norm_assignee(value):
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _norm_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    s = str(value).strip()
    return s or None


def _field_equal(a, b, kind):
    if kind == "assignee":
        return _norm_assignee(a) == _norm_assignee(b)
    if kind == "due_date":
        return _norm_date(a) == _norm_date(b)
    return a == b


def match_tasks(expected, predicted):
    used = set()
    matches = []
    for ei, exp in enumerate(expected):
        key = _norm_title(exp.get("title", ""))
        for pi, pred in enumerate(predicted):
            if pi in used:
                continue
            if _norm_title(pred.get("title", "")) == key:
                used.add(pi)
                matches.append((ei, pi))
                break
    return matches, len(matches)


def _per_example_counts(example):
    expected = example.get("expected", [])
    predicted = example.get("predicted", [])
    matches, tp = match_tasks(expected, predicted)
    return expected, predicted, matches, tp


def _safe_div(num, den):
    if den == 0:
        return None
    return num / den


def compute_metrics(examples):
    e_total = 0
    p_total = 0
    tp_total = 0
    assignee_correct = 0
    date_correct = 0
    priority_correct = 0
    language_correct = 0
    empty_total = 0
    empty_correct = 0

    for ex in examples:
        expected, predicted, matches, tp = _per_example_counts(ex)
        e_total += len(expected)
        p_total += len(predicted)
        tp_total += tp
        for ei, pi in matches:
            e_item = expected[ei]
            p_item = predicted[pi]
            if _field_equal(e_item.get("assignee"), p_item.get("assignee"), "assignee"):
                assignee_correct += 1
            if _field_equal(e_item.get("due_date"), p_item.get("due_date"), "due_date"):
                date_correct += 1
            if _field_equal(e_item.get("priority"), p_item.get("priority"), "priority"):
                priority_correct += 1
            if _field_equal(e_item.get("language"), p_item.get("language"), "language"):
                language_correct += 1
        if len(expected) == 0:
            empty_total += 1
            if len(predicted) == 0:
                empty_correct += 1

    fp_total = p_total - tp_total
    fn_total = e_total - tp_total

    if p_total > 0:
        precision = tp_total / p_total
    else:
        precision = 1.0 if e_total == 0 else 0.0
    if e_total > 0:
        recall = tp_total / e_total
    else:
        recall = 1.0 if p_total == 0 else 0.0
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 1.0 if (e_total == 0 and p_total == 0) else 0.0
    if e_total > 0:
        title_rate = tp_total / e_total
    else:
        title_rate = 1.0 if p_total == 0 else 0.0
    if tp_total > 0:
        assignee_acc = assignee_correct / tp_total
        date_acc = date_correct / tp_total
        priority_acc = priority_correct / tp_total
        language_acc = language_correct / tp_total
    else:
        assignee_acc = 1.0 if e_total == 0 else 0.0
        date_acc = 1.0 if e_total == 0 else 0.0
        priority_acc = 1.0 if e_total == 0 else 0.0
        language_acc = 1.0 if e_total == 0 else 0.0
    if empty_total > 0:
        empty_acc = empty_correct / empty_total
    else:
        empty_acc = 1.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "title_match_rate": title_rate,
        "assignee_accuracy": assignee_acc,
        "due_date_accuracy": date_acc,
        "priority_accuracy": priority_acc,
        "language_preservation_accuracy": language_acc,
        "empty_result_accuracy": empty_acc,
        "tp": tp_total,
        "fp": fp_total,
        "fn": fn_total,
        "expected_total": e_total,
        "predicted_total": p_total,
        "example_count": len(examples),
    }


def evaluate_example(example):
    expected, predicted, matches, tp = _per_example_counts(example)
    matched_e = {ei for ei, _ in matches}
    matched_p = {pi for _, pi in matches}
    failures = []
    for ei, exp in enumerate(expected):
        if ei not in matched_e:
            failures.append(f"missing: {_norm_title(exp.get('title', ''))}")
    for pi, pred in enumerate(predicted):
        if pi not in matched_p:
            failures.append(f"extra: {_norm_title(pred.get('title', ''))}")
    for ei, pi in matches:
        e_item = expected[ei]
        p_item = predicted[pi]
        title = _norm_title(e_item.get("title", ""))
        if not _field_equal(e_item.get("assignee"), p_item.get("assignee"), "assignee"):
            failures.append(f"assignee mismatch: {title}")
        if not _field_equal(e_item.get("due_date"), p_item.get("due_date"), "due_date"):
            failures.append(f"due_date mismatch: {title}")
        if not _field_equal(e_item.get("priority"), p_item.get("priority"), "priority"):
            failures.append(f"priority mismatch: {title}")
        if not _field_equal(e_item.get("language"), p_item.get("language"), "language"):
            failures.append(f"language mismatch: {title}")
    p_count = len(predicted)
    e_count = len(expected)
    if p_count > 0:
        precision = tp / p_count
    else:
        precision = 1.0 if e_count == 0 else 0.0
    if e_count > 0:
        recall = tp / e_count
    else:
        recall = 1.0 if p_count == 0 else 0.0
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 1.0 if (e_count == 0 and p_count == 0) else 0.0
    failures = sorted(failures)
    return {
        "id": example.get("id", ""),
        "language": example.get("language", ""),
        "tp": tp,
        "fp": p_count - tp,
        "fn": e_count - tp,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "failures": failures,
    }
