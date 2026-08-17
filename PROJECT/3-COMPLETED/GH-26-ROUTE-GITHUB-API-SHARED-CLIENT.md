---
gh_issue: 26
source: https://github.com/HiQS-Suite/rebalanceOS/issues/26
title: "GH-26 Route every GitHub API call through the shared client"
status: "Completed — shipped in the Build 0.73.0 Subsystem Unification marathon (phase su3) as PR #40 (0.73.0)"
created: 2026-08-16
updated: 2026-08-17
owner: noel
doc_type: code-quality
goal: >
  Finish the GitHub HTTP client consolidation by deleting legacy helper duplicates in
  github_knowledge.py, migrating github_watch pagination, and enforcing a single-client contract test.
effort: 2
complexity: 2
risk: 1
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-26 — Route Every GitHub API Call Through Shared Client

## Status

| What was just completed | What's next |
|---|---|
| Correctness fixes landed: diagnose live probes + `pulse.fetch_assigned_issues` routed through `GitHubClient`, backed by 13 tests in `tests/test_diagnose.py`. | Phase 0 review of legacy copies in `github_knowledge.py` and hand-rolled pagination in `github_watch.py`. |

## Why

`src/rebalance/ingest/_http.py::GitHubClient` provides retry with backoff, header-based rate-limit detection, and request attribution.

Remaining tasks:
1. `_build_url` (`github_knowledge.py:111`) and `_paginate_list` (`github_knowledge.py:118`) are byte-for-byte duplicates of `GitHubClient` methods (retained temporarily as legacy seams).
2. `github_watch.py:95-119` uses hand-rolled commit pagination rather than `GitHubClient.paginate`.
3. Missing contract test ensuring no module outside `_http.py` constructs a GitHub `Authorization` header directly.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Deduplication and pagination migration](#phase-1--deduplication-and-pagination-migration)
- [Phase 2 — Architectural contract test](#phase-2--architectural-contract-test)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/ingest/_http.py`: `GitHubClient` class (get, get_json, paginate, build_url).
- `src/rebalance/ingest/github_knowledge.py:111,118`: legacy `_build_url` and `_paginate_list`.
- `src/rebalance/ingest/github_watch.py:95-119`: custom pagination loop.
- `tests/test_github_client.py` & `tests/test_diagnose.py`: test suites pinning `GitHubClient`.

**Research / Inventory:**
1. Check call sites of `_paginate_list` and `_build_url` in `github_knowledge.py`.
2. Inspect tests in `tests/test_github_knowledge.py` to ensure mock fixtures support `GitHubClient` dependency injection.

**Acceptance criteria for Phase 0:**
- Verification that all GitHub API call sites can cleanly use `GitHubClient`.

## Phase 1 — Deduplication and pagination migration

- [ ] Replace `_build_url` and `_paginate_list` in `github_knowledge.py` with `GitHubClient.build_url` / `GitHubClient.paginate`.
- [ ] Migrate `github_watch.py` commit pagination to `GitHubClient.paginate`.
- [ ] Update any tests mocking the legacy functions to mock `GitHubClient` instead.

**QA gate:**
- `pytest tests/test_github_knowledge.py tests/test_github_watch.py tests/test_github_client.py` all green.

## Phase 2 — Architectural contract test

- [ ] Add contract test in `tests/test_http_contract.py` asserting no module outside `_http.py` constructs `Authorization: Bearer` or `Authorization: token` for GitHub API.
- [ ] Verify rate limiting and 429 backoff paths work across all collectors.

**QA gate:**
- Contract test passes; zero duplicate GitHub HTTP logic in `src/`.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
