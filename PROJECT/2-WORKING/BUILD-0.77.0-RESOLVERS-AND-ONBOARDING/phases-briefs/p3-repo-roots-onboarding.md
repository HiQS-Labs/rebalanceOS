---
title: "Phase ro3 Empty local_repo_roots Summary and Onboarding Discovery"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase ro3 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase ro3 — Empty local_repo_roots Summary & Onboarding Discovery (#116)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase ro3 in marathon harness. |

## Objective
Condense the 60+ individual "uncoverable" repo lines in `src/rebalance/ingest/github_coverage.py` into a single summary line when `local_repo_roots` is unset/empty, add doctor remediation discoverability, and add an onboarding auto-detect stage in `src/rebalance/ingest/lifecycle.py`.

## Context & Files
- Target files: `src/rebalance/ingest/github_coverage.py`, `src/rebalance/doctor.py`, `src/rebalance/ingest/lifecycle.py`, `tests/test_github_coverage.py`
- Issue: #116 — Empty `local_repo_roots` spams every repo as 'uncoverable' with no setup path.

## Tasks
1. Update `coverage_health` / `check_coverage` in `src/rebalance/ingest/github_coverage.py` so that when `local_repo_roots` is empty, it returns a single concise summary reason (`"local repo scanning is off (set local_repo_roots) — N repos not checked"`) matching doctor semantics.
2. Add an optional `local_repo_roots_configured` stage in `src/rebalance/ingest/lifecycle.py` with auto-detection suggestions under standard directories (e.g. `~/Documents/GH Repos`).
3. Add a clear hint to `_check_commit_coverage` in `src/rebalance/doctor.py` pointing to `rebalance config set-local-repo-roots`.
4. Update `tests/test_github_coverage.py` to assert the single-line summary behavior when roots are empty.
5. Verify tests pass with `.venv/bin/pytest tests/test_github_coverage.py -q`.

## Definition of Done
- `pytest tests/test_github_coverage.py` passes with single summary verification.
