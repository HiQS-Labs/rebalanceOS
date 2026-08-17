---
title: "Phase su4 Deduplicate Persistence and Upsert Paths"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su4 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su4 — Deduplicate Persistence/Upsert Paths Across Collectors (#27)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su4 in marathon harness. |

## Objective
Extract shared `table_exists` and `db_connection_readonly` helpers in `src/rebalance/ingest/db/connection.py`, deduplicating persistence loops in Gmail and GitHub knowledge collectors.

## Context & Files
- Target files: `src/rebalance/ingest/db/connection.py`, `src/rebalance/ingest/gmail.py`, `src/rebalance/ingest/github_knowledge.py`, `src/rebalance/ingest/sleuth_reminders.py`
- Issue: #27 — Duplicate 9-column email insert, duplicate 100-line issue/PR persist loops, and multiple `_table_exists` copies.

## Tasks
1. Add `table_exists()` and `db_connection_readonly()` in `src/rebalance/ingest/db/connection.py`.
2. Deduplicate message persistence in `gmail.py` into a single persister function.
3. Deduplicate issue/PR loops in `github_knowledge.py` by extracting shared item record builder and upsert steps.
4. Route `sleuth_reminders.py` through standard `db_connection()`.

## Definition of Done
- `pytest tests/test_db_connection.py tests/test_gmail.py tests/test_github_knowledge.py tests/test_sleuth_reminders.py` passes cleanly.
