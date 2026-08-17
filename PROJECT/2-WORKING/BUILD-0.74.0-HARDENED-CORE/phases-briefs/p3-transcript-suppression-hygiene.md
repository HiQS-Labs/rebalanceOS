---
title: "Phase hc3 Transcript Suppression and Repo Hygiene"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase hc3 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase hc3 — Transcript Suppression & Repo Hygiene (#33)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase hc3 in marathon harness. |

## Objective
Enforce strict .gitignore rules for agent transcripts and SQLite blobs, add an automated repo hygiene contract test, and verify upstream repository archival checklist.

## Context & Files
- Target files: `.gitignore`, `tests/test_repo_hygiene.py`, `PROJECT/1-INBOX/GH-33-STOP-COMMITTING-TRANSCRIPTS.md`
- Issue: #33 — History bloat from committed transcripts and sqlite files in previous repo; ensure clean-room invariants hold.

## Tasks
1. Audit `.gitignore` patterns for `relay-system/`, `marathon-system/`, `.tick/`, and `.sqlite`.
2. Add `tests/test_repo_hygiene.py` asserting no ignored file types or agent transcripts are tracked in git.
3. Validate upstream repository migration/archival checklist.

## Definition of Done
- `pytest tests/test_repo_hygiene.py` passes; zero tracked transcripts or sqlite files.
