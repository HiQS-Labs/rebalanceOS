---
title: "Phase fe5 Sustained Auto Promotion"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase fe5 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase fe5 — Sustained-Activity Auto-Promotion Engine (#1)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase fe5 in marathon harness. |

## Objective
Deliver multi-signal sustained-activity project auto-promotion (commits + PRs + issues + comments + reviews), replacing the commit-only 3-commit gate with a 5-action threshold protected by a 20h 2-observation wall-clock burst guard.

## Context & Files
- Target files: `src/rebalance/ingest/project_inference.py`, `src/rebalance/ingest/config.py`, `src/rebalance/ingest/auth_log.py`, `src/rebalance/ingest/db/`, `tests/test_auto_promote.py`
- Issue: #1 — Commit-only threshold promotes on 3 commits in a single sitting without checking multi-signal engagement or time spread.

## Tasks
1. Create `auto_promote_watch` table to record `first_seen_over_threshold_at`.
2. Implement `_count_operator_actions()` combining operator GitHub activity types + bot PR commits.
3. Enforce the two-observation ≥20h wall-clock promotion predicate during `refresh_index()`.
4. Update `get_auto_promote_config()`, machine-owned markers (`activity_threshold_v1`), and auth log payload.
5. Add comprehensive unit tests in `tests/test_auto_promote.py`.

## Definition of Done
- `pytest tests/test_auto_promote.py -v` passes; multi-signal auto-promotion operational.
