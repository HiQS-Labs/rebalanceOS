---
title: "Phase su2 Timestamp Handling Consolidation"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su2 — Timestamp Handling Consolidation (#25)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su2 in marathon harness. |

## Objective
Consolidate remaining timestamp handling through `src/rebalance/lib/time_ops.py`, eliminating alias wrappers and inline cutoff-date implementations.

## Context & Files
- Target files: `src/rebalance/lib/time_ops.py`, `src/rebalance/ingest/sleuth_reminders.py`, `src/rebalance/ingest/pulse_health.py`, `src/rebalance/ingest/claude_cloud.py`, `src/rebalance/ingest/index_ops.py`
- Issue: #25 — Four one-line alias wrappers and multiple inline cutoff calculations bypass the canonical freeze-clock seam.

## Tasks
1. Collapse alias wrappers (`_parse_datetime`, `_parse_utc`, `_parse_ts`, `_parse_status_timestamp`) onto direct `parse_utc_iso` imports.
2. Standardize cutoff-date expressions onto `time_ops.now_utc()` or a dedicated cutoff helper.
3. Switch private imports (`_parse_iso`, `_now`) to public exports in `time_ops.py`.

## Definition of Done
- `pytest tests/test_time_ops.py` green; 0 datetime alias wrappers remain in active ingest modules.
