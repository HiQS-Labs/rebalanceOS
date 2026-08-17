---
gh_issue: 7
source: https://github.com/HiQS-Suite/rebalanceOS/issues/7
title: "GH-7 HiQS suite polluted by state leaked from tests/ when sharing pytest process"
status: "Completed — shipped in the Build 0.73.0 Subsystem Unification marathon (phase su1) as PR #40 (0.73.0)"
created: 2026-08-16
updated: 2026-08-17
owner: noel
doc_type: bugfix
goal: >
  Isolate and eliminate mutable state leakage (environment variables or module singletons)
  between tests/ and HiQS/tests so the entire test suite can execute in a single pytest process.
effort: 2
complexity: 2
risk: 2
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-7 — HiQS Suite State Leak from tests/

## Status

| What was just completed | What's next |
|---|---|
| Issue documented on pristine main. CI was mitigated by running `HiQS/tests` in its own isolated pytest step. | Phase 0 bisection to locate the exact source of shared mutable state between `tests/` and `HiQS/hiqs/sources/github.py`. |

## Why

`HiQS/tests/test_github.py::test_github_failure_continues_logs_error_and_keeps_watermark` passes in isolation but fails when run in the same process after `tests/`:
```
assert logged[-1][2] == "error"
AssertionError: assert 'warn' == 'error'
```

While CI runs them separately, the bug reveals unwanted coupling / state pollution across packages that should be hermetic.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Bisection and root-cause fix](#phase-1--bisection-and-root-cause-fix)
- [Phase 2 — Hermeticity regression tests](#phase-2--hermeticity-regression-tests)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `HiQS/tests/test_github.py`: tests event logging severity (`error` vs `warn`).
- `HiQS/hiqs/sources/github.py`: logs events via `log_event`.
- `tests/`: test modules in incumbent package modifying environment variables, logging levels, or global registries without restoring them.

**Spike / Research approach:**
1. Run binary search / bisection:
   `python -m pytest tests/<subset> HiQS/tests/test_github.py -q`
2. Identify the smallest subset of `tests/` that flips the assertion from `error` to `warn`.
3. Check `os.environ`, global monkeypatches, or singleton imports in that subset.

**Acceptance criteria for Phase 0:**
- Exact offending test file and leaking variable/singleton identified.
- Minimal reproduction command documented.

## Phase 1 — Bisection and root-cause fix

- [ ] Execute pytest bisection to pin down the leaking test in `tests/`.
- [ ] Add fixture teardown or monkeypatch cleanup to the offending test in `tests/` (e.g. `monkeypatch.delenv`, resetting log level, or isolating global state).
- [ ] Verify `HiQS/hiqs/sources/github.py` has explicit fallback / defense against environment pollution.

**QA gate:**
- `python -m pytest tests/ HiQS/tests/test_github.py -q` passes with 0 failures.

## Phase 2 — Hermeticity regression tests

- [ ] Run the combined suite: `python -m pytest tests/ HiQS/tests/ utils/3-eyes/tests -q`.
- [ ] Verify clean room invariant tests in `HiQS/tests/test_clean_room.py` remain green.

**QA gate:**
- Combined pytest execution passes cleanly in a single process.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
