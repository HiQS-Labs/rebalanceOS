---
title: "Phase hc2 Secret Redaction and Chunk Purge"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase hc2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase hc2 — Secret Redaction Regression Suite & Chunk Purge (#32)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase hc2 in marathon harness. |

## Objective
Establish a regression test suite pinning pre-embed secret redaction in vault ingest, implement a purge/re-index command for existing databases, and support frontmatter `index: false`.

## Context & Files
- Target files: `src/rebalance/ingest/note_ingester.py`, `src/rebalance/ingest/semantic_index.py`, `tests/test_secret_redaction.py`
- Issue: #32 — Known gap #5: live credentials indexed in vault notes returnable via `semantic_query()`. Unchanged notes skip redaction without a purge/re-index mechanism.

## Tasks
1. Create `tests/test_secret_redaction.py` testing synthetic key patterns (ghp_, sk-, AKIA, AIza, xoxb, Bearer, long hex) ensuring zero verbatim leaks reach chunks or query output.
2. Add `--force-rechunk` / `--reindex-secrets` to `note_ingester.py` to sanitize existing database rows.
3. Support frontmatter `index: false` to skip indexing sensitive notes entirely.

## Definition of Done
- `pytest tests/test_secret_redaction.py -v` green; re-index command sanitizes existing databases.
