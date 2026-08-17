---
title: "Phase su1 HiQS Test Process Isolation"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su1 — HiQS Test Process Isolation (#7)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su1 in marathon harness. |

## Objective
Isolate and eliminate mutable state leakage between `tests/` and `HiQS/tests` so that running both test directories in a single pytest process succeeds.

## Context & Files
- Target files: `HiQS/tests/test_github.py`, `HiQS/hiqs/sources/github.py`, `tests/`
- Issue: #7 — `AssertionError: assert 'warn' == 'error'` in `test_github_failure_continues_logs_error_and_keeps_watermark` when run after `tests/`.

## Tasks
1. Bisect `tests/` to identify the test setting an environment variable or modifying a global logger/severity singleton.
2. Add proper cleanup/teardown in the offending test or make `HiQS/hiqs/sources/github.py` resilient against external ambient state.
3. Verify `pytest tests/ HiQS/tests/` passes in a single process invocation.

## Definition of Done
- `pytest tests/ HiQS/tests/ -q` passes with 0 failures.
