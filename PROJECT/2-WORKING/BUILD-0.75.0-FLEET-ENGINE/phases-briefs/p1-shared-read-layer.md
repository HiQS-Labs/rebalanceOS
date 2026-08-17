---
title: "Phase fe1 Shared SQL Read Layer"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase fe1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase fe1 — Shared SQL Read Layer & Web App Mount (#29)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase fe1 in marathon harness. |

## Objective
Extract the 6 duplicate SQL read query families into `src/rebalance/ingest/db/queries.py` and unify router mounting between `scripts/pulse_server.py` and `src/rebalance/web.py`.

## Context & Files
- Target files: `src/rebalance/ingest/db/queries.py`, `scripts/pulse_server.py`, `scripts/dashboard.py`, `src/rebalance/ingest/pulse.py`, `src/rebalance/ingest/note_builder.py`, `src/rebalance/web_components.py`
- Issue: #29 — Seven surfaces duplicate data queries, badge styles, and route declarations.

## Tasks
1. Extract `fetch_org_activity`, `fetch_recent_github_activity`, `fetch_recent_vault_notes`, `fetch_calendar_events`, `fetch_recent_emails`, `fetch_recent_figma` into `src/rebalance/ingest/db/queries.py`.
2. Refactor dashboard, pulse markdown, and note builder to use the shared queries.
3. Mount `web.py` routers symmetrically in `scripts/pulse_server.py`.
4. Unify badge CSS styling and What's Next markup tokens.

## Definition of Done
- `pytest tests/test_web_surface.py tests/test_pulse_server.py` green; zero duplicate activity SQL queries.
