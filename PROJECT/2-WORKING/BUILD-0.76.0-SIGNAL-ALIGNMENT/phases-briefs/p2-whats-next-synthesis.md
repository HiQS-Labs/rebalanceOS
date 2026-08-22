---
title: "Phase sa2 What's Next Candidate Ranking and Attribution Fallback"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase sa2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase sa2 — What's Next Candidate Ranking and Attribution Fallback (#113)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase sa2 in marathon harness. |

## Objective
Enforce and test the candidate ranking and author fallback semantics in `src/rebalance/ingest/next_actions.py` to ensure unmapped Slack sender IDs fall back to raw traceable receipts (`@U12345678`) rather than crashing or degrading to anonymous labels.

## Context & Files
- Target files: `src/rebalance/ingest/next_actions.py`, `tests/test_next_actions.py`
- Issue: #113 (Point 1) — What's next display and ranking resilience.

## Tasks
1. Verify `sleuth_candidates()` in `src/rebalance/ingest/next_actions.py` properly applies `users.get(sender_id, sender_id)`.
2. Add `test_sleuth_candidates_unmapped_sender_id` to `tests/test_next_actions.py` validating that missing user mappings preserve traceable raw IDs across candidate generation and rank sorting.
3. Verify test suite passes cleanly with `.venv/bin/pytest tests/test_next_actions.py -q`.

## Definition of Done
- `pytest tests/test_next_actions.py` passes.
