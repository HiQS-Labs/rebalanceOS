---
title: "Phase su6 Dead Code Removal and Doc Reconciliation"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su6 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su6 — Dead Code Removal & Stale Architecture Docs (#30)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su6 in marathon harness. |

## Objective
Remove dead code (`_render_sleuth_groups`, CSS composite) and correct stale documentation references to removed legacy MCP tools.

## Context & Files
- Target files: `src/rebalance/web.py`, `tests/test_web_badges.py`, `scripts/pulse_web.py`, `ARCHITECTURE.md`, `AGENTS.md`, `src/rebalance/mcp/tools/index.py`
- Issue: #30 — Dead `_render_sleuth_groups` in `web.py:416` and 5 stale references in docs to `query_notes` / `query_github_context`.

## Tasks
1. Delete `_render_sleuth_groups` in `web.py` and align `tests/test_web_badges.py`.
2. Delete unused `CSS` composite in `scripts/pulse_web.py`.
3. Update `ARCHITECTURE.md` and `AGENTS.md` tool tables to reference `semantic_query`.
4. Update docstrings in `src/rebalance/mcp/tools/index.py`.

## Definition of Done
- `ruff check .` clean; `pytest tests/test_web.py tests/test_web_badges.py` green; `utils/pdda/pdda.sh governance` passes with 0 errors.
