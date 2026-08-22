---
title: "Phase ro2 Missing slack_users Diagnostic and Lifecycle Onboarding Stage"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase ro2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase ro2 — Missing slack_users Diagnostic & Lifecycle Onboarding Stage (#115)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase ro2 in marathon harness. |

## Objective
Add a doctor diagnostic check in `src/rebalance/doctor.py` that flags when `temp/slack_users.json` is absent while Sleuth activity exists in the database, and add an optional `slack_users_configured` stage to the setup lifecycle in `src/rebalance/ingest/lifecycle.py`.

## Context & Files
- Target files: `src/rebalance/doctor.py`, `src/rebalance/ingest/lifecycle.py`, `tests/test_doctor.py`, `tests/test_lifecycle_contract.py`
- Issue: #115 — Missing `temp/slack_users.json` degrades silently with no signal in doctor or onboarding.

## Tasks
1. Implement `_check_slack_users(db_path)` in `src/rebalance/doctor.py`: reports `WARN` only if Sleuth records are present in DB and `temp/slack_users.json` does not exist; returns `OK` if file exists or no Sleuth rows exist.
2. Add optional stage `slack_users_configured` in `src/rebalance/ingest/lifecycle.py` with remediation and executor hints.
3. Update `tests/test_doctor.py` and `tests/test_lifecycle_contract.py` to cover the new check and lifecycle stage.
4. Verify tests pass with `.venv/bin/pytest tests/test_doctor.py tests/test_lifecycle_contract.py -q`.

## Definition of Done
- `pytest tests/test_doctor.py tests/test_lifecycle_contract.py` passes.
