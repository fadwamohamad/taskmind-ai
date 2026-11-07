# TaskMind AI — Evaluation

## Purpose

Deterministic quality measurement for task extraction: detection, field accuracy, language preservation, and empty-result behavior. This suite uses **fixed fixtures** — no live Gemini calls — so results are reproducible in CI.

## Dataset (`evaluation/dataset.json`)

- Format: JSON array of examples.
- Fields:
  - `id`: unique string (e.g. `en-001`).
  - `language`: notes language (`ar` | `en` | `fr`).
  - `tags`: scenario tags (see below).
  - `notes`: meeting-note text (treat as untrusted data).
  - `expected`: gold tasks `[{title, details, assignee, priority, due_date, language}]`.
  - `predicted`: fixture predictions evaluated by the runner (mirrors `expected` for the golden run).
- Gold rules: assignee/date/priority are only non-null when explicitly supported by `notes`; `due_date` is ISO `YYYY-MM-DD` or `null`; `priority` is `low|medium|high|null`; task `language` matches note language. No invented values.
- Coverage (24 examples): `ar`/`en`/`fr` × 8; multiple actions, explicit/no assignee, explicit/ambiguous dates, high/medium/low + null priority, prompt-injection (quoted), duplicates (single deduplicated task), long notes with irrelevant discussion/decisions, and empty (no-task) notes.

## Methodology

1. Load + validate dataset (`validate_dataset`).
2. For each example, match predicted to expected one-to-one (see below).
3. Micro-average TP/FP/FN across examples; field accuracies over matched pairs only.
4. Print per-example failures (missing/extra/field mismatches by normalized title) and aggregate metrics.
5. Exit `0` if all thresholds met, else `1`.

No LLM is used as evaluator; matching is deterministic string comparison.

## Matching Strategy

- Normalize titles: ` " ".join(title.strip().split())` (handles harmless whitespace only; case/accents kept).
- Greedy one-to-one in expected order: each expected task claims the first unmatched predicted with equal normalized title.
- Handles reordered predictions; duplicates require duplicate titles to match (extra duplicates count as FP).
- Field equality: assignee (stripped, `""→null`), due_date (string/`date` normalized), priority/language exact.

## Metric Formulas

Let `E`=expected, `P`=predicted, `TP`=matched, `FP=P−TP`, `FN=E−TP` (micro totals).

- `precision = TP/P` (`P=0 → 1.0 if E=0 else 0.0`)
- `recall = TP/E` (`E=0 → 1.0 if P=0 else 0.0`)
- `F1 = 2·P·R/(P+R)` (`P+R=0 → 1.0 if all empty else 0.0`)
- `title_match_rate = TP/E` (equals recall by construction since matching keys on title; measures whitespace-tolerant title detection)
- `assignee/due_date/priority/language accuracy = correct_fields / TP` over matched pairs (`TP=0 → 1.0 if E=0 else 0.0`)
- `empty_result_accuracy = correct_empty / empty_expected` (`1.0` if no empty-expected examples)

Defaults thresholds: all metrics ≥ `0.8` (overridable). Documented per-flag below.

## Running

```bash
python -m evaluation.runner                 # golden fixture run
python -m evaluation.runner --min-f1 0.9
python -m evaluation.runner --dataset evaluation/dataset.json --min-precision 0.9 --min-recall 0.9
pytest tests/test_evaluation.py -v
pytest -q
```

Runner prints aggregate metrics + per-example failures; exit code is `0`/`1` for thresholds. Results are deterministic (fixed file order, sorted failure lists).

To evaluate live Gemini (manual, needs key):

```bash
export GEMINI_API_KEY=...   # or $env:ANTHROPIC_API_KEY in PowerShell
# Replace fixture predictions with live calls in your own script using app/services/ai_service.extract_tasks(),
# then feed the returned tasks as `predicted` into compute_metrics().
```

## Adding Examples

1. Copy a nearby example; keep `expected` grounded in `notes` (no invented assignee/date/priority).
2. Add tags; keep titles/details in the note language.
3. Set `predicted` for fixture runs (golden = `expected`; adversarial cases can differ to exercise metrics).
4. Validate: `python -m evaluation.runner --min-f1 0.0` must pass `validate_dataset`.

## Known Limitations

- Title-keyed matching: paraphrased titles count as miss (no fuzzy/embedding matching by design).
- Duplicate policy: repeated mentions are gold-coded as one task — penalizes extractors emitting two.
- Field accuracy conditions on detection; missing tasks don't directly lower assignee accuracy.
- Small dataset (24): high variance; not statistically powered.
- No semantic/nuance judgment (e.g. ambiguous responsibility) beyond explicit-field checks.

## Fixture vs Live Evaluation

- **Fixture (this suite):** zero cost/network/key; measures harness + gold alignment; cannot detect prompt/model drift.
- **Live:** calls Gemini per note; measures real prompt/model quality but is non-deterministic, costly, and needs human spot-checks. Reuse `compute_metrics` on live predictions for comparability.

## Quality Review (prompt vs cases)

Risks identified without changing approved rules:

- **False positives:** decisions/discussion misread as tasks (covered by `*-003` empty cases); mitigated by review-before-save + `explicit actionable only` rule.
- **False negatives:** vague actions (“prepare update”) may be skipped; cases `*-002` show minimal gold.
- **Assignee hallucination:** names mentioned but not assigned; gold is `null` unless explicit (tests `no-assignee`).
- **Date hallucination:** relative dates (“soon/next week”) must stay `null` (`ambiguous-date` cases); explicit ISO only.
- **Priority inference:** weak signals (“please”) must stay `null` (`priority-null` cases); only urgent/medium/low wording maps to high/medium/low.
- **Multilingual:** Arabic/French titles must stay in source language; injection cases verify no translation triggered.
- **Duplicates:** repeated mentions gold-coded once; extractors emitting both are penalized as FP — policy choice, documented above.

**Proposed change (pending approval — not applied):** Reword system prompt to explicitly say “If the same action is mentioned more than once, return it once” and “Relative dates like ‘tomorrow’ or ‘next week’ must be `null`, never converted.” Expected effect: fewer duplicate FPs and fewer date hallucinations. **Do not apply without approval.**
