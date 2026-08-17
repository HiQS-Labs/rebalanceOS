---
title: "Phase hc1 Close Coverage Gaps"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase hc1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase hc1 — Close Coverage Gaps Across Core Modules (#31)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase hc1 in marathon harness. |

## Objective
Write direct unit and behavioral tests for uncovered core modules: `md_parser.py`, `note_ingester.py`, `slack_users.py`, MCP tools, and the `querier.py` local synthesis path.

## Context & Files
- Target files: `tests/test_md_parser.py`, `tests/test_note_ingester.py`, `tests/test_slack_users.py`, `tests/test_mcp_tools.py`, `tests/test_querier_synthesis.py`
- Issue: #31 — Several core components underpinning search and retrieval lacked direct test files.

## Tasks
1. Create `tests/test_md_parser.py` and `tests/test_note_ingester.py` covering frontmatter, wikilinks, tags, chunk boundaries, and hash delta detection.
2. Create `tests/test_slack_users.py` testing caching and mtime staleness.
3. Create `tests/test_mcp_tools.py` for behavioral invocation of `index.py`, `calendar.py`, `onboarding.py`, `hygiene.py`.
4. Create `tests/test_querier_synthesis.py` for synthesis fallback and mock LLM invocation.

## Definition of Done
- `pytest tests/test_md_parser.py tests/test_note_ingester.py tests/test_slack_users.py tests/test_mcp_tools.py tests/test_querier_synthesis.py` passes with >90% coverage.
