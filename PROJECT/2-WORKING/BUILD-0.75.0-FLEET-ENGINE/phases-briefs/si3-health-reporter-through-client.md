---
title: "Phase si3 Health Reporter Through GitHubClient"
status: "Draft"
created: 2026-08-25
updated: 2026-08-25
owner: noel
goal: "Phase si3 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase si3 — Route health_issue_reporter.py Through GitHubClient (#75)

## Status

| What was just completed | What's next |
|---|---|
| Phase si1 landed budget-aware, retrying HTTP in one place. | Execute phase si3 in marathon harness. |

## Objective
Delete the hand-rolled `urllib` layer in `scripts/health_issue_reporter.py` and route its GitHub
calls through `GitHubClient`, so the health reporter inherits the rate-limit handling si1 built
instead of crashing on the 403 that #54's quota exhaustion guarantees.

## Context & Files
- Target files: `scripts/health_issue_reporter.py`, `tests/test_health_issue_reporter.py`
- Issue #75: `_request()` is a private `urllib.request` implementation that bypasses
  `src/rebalance/ingest/_http.py::GitHubClient`. On a 403 it raises an unhandled `RuntimeError` and
  exits 1 — the architectural root cause of the failing `launchd:health-check-triage` job.
- This is the second-order failure of #54: the reporter whose job is to tell you the fleet is
  unhealthy is itself taken out by the same exhausted quota, so the fleet goes quiet exactly when
  it has the most to report.
- `_request()` was edited on 2026-08-25 (GH-124) to follow 307/308 redirects. That change stays —
  verify `GitHubClient` handles redirects equivalently before removing the local implementation,
  and if it does not, that gap belongs in `GitHubClient`, not in a second copy here.

## Tasks
1. Replace `_request()`'s call sites with `GitHubClient`, preserving current behaviour for the
   paths the script actually uses.
2. Confirm redirect handling and auth-header behaviour survive the move; close any gap in
   `GitHubClient` rather than keeping a private fallback.
3. Make a rate-limited response a reported, non-crashing outcome — the script should say it could
   not file and exit in a way the scheduler can distinguish from a hard fault.
4. Remove the dead `urllib` code once nothing calls it. Leaving it behind invites the next caller
   to reach for it.

## Definition of Done
- No `urllib.request` usage remains in `scripts/health_issue_reporter.py`.
- A simulated 403 rate-limit response produces a reported failure, not an unhandled `RuntimeError`,
  asserted by test.
- Redirect following is still exercised by a test after the move.
- `tests/test_health_issue_reporter.py` passes.
