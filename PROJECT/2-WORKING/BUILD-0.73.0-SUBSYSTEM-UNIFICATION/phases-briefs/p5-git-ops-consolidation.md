---
title: "Phase su5 One Git Subprocess Wrapper"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su5 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su5 — One Git Subprocess Wrapper (#28)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su5 in marathon harness. |

## Objective
Consolidate all private git subprocess runners across pulse, snapshot, sleuth, and ask-self modules onto `src/rebalance/lib/git_ops.py`.

## Context & Files
- Target files: `src/rebalance/lib/git_ops.py`, `src/rebalance/ingest/pulse.py`, `src/rebalance/ingest/sync_snapshot.py`, `src/rebalance/ingest/sleuth_reminders.py`, `src/rebalance/ingest/ask_self_scan.py`
- Issue: #28 — Four private git runners with divergent timeout/error contracts.

## Tasks
1. Export `run_git(repo_path, *args, timeout=30.0)` and `git_pull_rebase_safe(repo_path)` from `lib/git_ops.py`.
2. Replace private `_run_git` and `_git` across `pulse.py`, `sync_snapshot.py`, `sleuth_reminders.py`, and `ask_self_scan.py`.
3. Add contract test asserting no direct `subprocess.run(["git", ...])` calls outside `git_ops.py`.

## Definition of Done
- `pytest tests/test_git_ops.py tests/test_sync_snapshot.py tests/test_pulse.py` green; zero private git runners.
