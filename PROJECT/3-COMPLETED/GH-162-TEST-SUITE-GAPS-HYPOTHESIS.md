---
gh_issue: 162
source: https://github.com/HiQS-Labs/rebalanceOS/issues/162
title: "GH-162 Test suite gaps: Hypothesis setup, pytest configuration, and property testing"
status: "Merged 2026-09-04 as 8dd120b via PR #165. The md_parser regex change it originally carried was severed to #167 and landed separately as 7cee094 via PR #169."
created: 2026-09-03
updated: 2026-09-04
owner: antigravity
doc_type: plan
goal: >
  Modernize the test suite by adding pytest configuration in pyproject.toml, adopting
  Hypothesis in dev optional-dependencies, and establishing property tests for untested
  parsers and numeric invariants.
effort: 2
complexity: 2
risk: 1
phases: 4
ratings_provisional: false
roadmap_exempt: false
---

# GH-162 — Test suite gaps: Hypothesis setup, pytest configuration, and property testing

## Status

| What was just completed | What's next |
|---|---|
| Sharpened implementation plan on GitHub issue #162 with four structured workstreams. | Execute Phase 1: add pytest configuration in `pyproject.toml`, wire `hypothesis>=6.100` into `dev` optional-dependencies, configure `tests/conftest.py`, and implement `tests/test_md_parser_property.py`. |

## Why

The test suite contains 2,164 tests with 343 `monkeypatch` mocks, but only 7 `@pytest.mark.parametrize` sites, 15 `pytest.raises`, and 0 property-based tests. Critical pure-function modules like `src/rebalance/ingest/md_parser.py` (205 LOC, 6 regexes) have zero test coverage, and `pyproject.toml` lacks a `[tool.pytest.ini_options]` block (causing CWD-dependent test collection issues, #67).

## Proposed Phases

### Phase 1 — Foundational Configuration & Hypothesis Setup
- Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["src"]` to `pyproject.toml`.
- Add `"hypothesis>=6.100.0"` to `[project.optional-dependencies] dev` in `pyproject.toml`.
- Add `.hypothesis/` to `.gitignore`.
- Register shared `ci` and `dev` Hypothesis profiles in `tests/conftest.py`.
- Pilot property testing on `tests/test_md_parser_property.py`.

### Phase 2 — Numeric & Time Invariants
- Invariant tests on `time_ops.py` and `calendar_helpers.py`.
- Monotonicity and roundtrip properties.

### Phase 3 — Negative Space Backfill
- Increase `pytest.raises` coverage across public entrypoints.

### Phase 4 — Test Isolation & Leak Triage
- Order-independence audit (#7).

## Verification

- `pytest tests/test_md_parser_property.py` passes cleanly across randomized Hypothesis examples.
- `pytest` runs cleanly from both repo root and subdirectories (confirming #67 resolution).
