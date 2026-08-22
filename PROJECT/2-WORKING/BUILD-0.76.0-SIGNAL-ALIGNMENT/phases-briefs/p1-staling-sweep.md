---
title: "Phase sa1 Sleuth Reminder Disappearance and Staling Sweep Validation"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase sa1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase sa1 — Sleuth Reminder Disappearance & Staling Sweep Validation (#113)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase sa1 in marathon harness. |

## Objective
Verify that reminders dropped from the Sleuth publisher export flip to `is_active=0` and `state='stale'` via `src/rebalance/ingest/sleuth_reminders.py`, and add behavioral regression tests in `tests/test_sleuth_reminders.py`.

## Context & Files
- Target files: `src/rebalance/ingest/sleuth_reminders.py`, `tests/test_sleuth_reminders.py`
- Issue: #113 (Point 3) — Verify how reminders get retired from What's next once completed/removed upstream.

## Tasks
1. Verify `sleuth_reminders.py` staling logic (`active_only=False` path) correctly transitions missing reminders to `is_active=0, state='stale'` without deleting the audit history.
2. Add `test_staling_sweep_reconciles_missing_reminders` and edge-case coverage (e.g., empty payload, partial disappearance, clock drift) in `tests/test_sleuth_reminders.py`.
3. Verify test suite passes cleanly with `.venv/bin/pytest tests/test_sleuth_reminders.py -q`.

## Definition of Done
- `pytest tests/test_sleuth_reminders.py` passes with full coverage over the staling sweep reconciliation paths.
