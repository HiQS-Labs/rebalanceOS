---
title: "Phase su3 Route Every GitHub API Call Through Shared Client"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su3 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su3 — Route Every GitHub API Call Through Shared Client (#26)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su3 in marathon harness. |

## Objective
Deduplicate legacy URL and pagination helpers in `github_knowledge.py` and `github_watch.py`, routing all calls through `GitHubClient` and adding an auth header contract test.

## Context & Files
- Target files: `src/rebalance/ingest/_http.py`, `src/rebalance/ingest/github_knowledge.py`, `src/rebalance/ingest/github_watch.py`, `tests/test_http_contract.py`
- Issue: #26 — `_build_url` and `_paginate_list` duplicate `GitHubClient` methods; `github_watch.py` has custom pagination loop.

## Tasks
1. Replace `_build_url` and `_paginate_list` in `github_knowledge.py` with `GitHubClient.build_url` and `GitHubClient.paginate`.
2. Migrate `github_watch.py:95-119` to `GitHubClient.paginate`.
3. Add architectural contract test asserting no module outside `_http.py` constructs GitHub `Authorization` headers.

## Definition of Done
- `pytest tests/test_github_knowledge.py tests/test_github_watch.py tests/test_diagnose.py` passes; zero duplicate GitHub HTTP helpers.
