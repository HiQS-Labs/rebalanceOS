---
title: "Phase si1 Rate-Limit Budget and Conditional Requests"
status: "Draft"
created: 2026-08-25
updated: 2026-08-25
owner: noel
goal: "Phase si1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase si1 — Rate-Limit Budget and ETag Conditional Requests in GitHubClient (#54, #62)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase si1 in marathon harness. |

## Objective
Give `GitHubClient` a rate-limit budget it enforces and an ETag cache it honours, so a caller
cannot consume the token's entire hourly allowance and every unchanged resource costs zero quota.

## Context & Files
- Target files: `src/rebalance/ingest/_http.py`, `tests/test_http_client.py`
- Issue #54: `com.rebalance-os.github-sync` exits 1 on every run. `_get_login`
  (`src/rebalance/ingest/github_scan.py:175`) logs `remaining=0 used=5129` against a 5000/hr core
  limit, four hours running. The token is exhausted, not throttled — this is a budget problem,
  not a retry problem, and no amount of backoff fixes it.
- Issue #62: names the two mechanisms — conditional requests (`If-None-Match` / `If-Modified-Since`,
  which return 304 and do NOT count against the core limit) and a pre-call guardrail that stops
  work while `remaining` is still above a floor.

## Tasks
1. Persist ETag and `Last-Modified` per request URL, and send `If-None-Match` /
   `If-Modified-Since` on repeat GETs. Treat 304 as a cache hit and return the stored payload.
   Store the cache somewhere a launchd job can reach across runs, not in process memory.
2. Track `X-RateLimit-Remaining` / `X-RateLimit-Reset` from every response on the client itself,
   so the budget is a property of the client rather than of any one caller.
3. Add a reserve floor: below it, the client refuses further non-essential calls and reports why,
   rather than spending down to zero and failing the run that discovers it.
4. Make exhaustion legible — a caller must be able to ask "how much is left and when does it
   reset" without making another request.

## Definition of Done
- A repeat scan over unchanged resources issues conditional requests and spends materially less
  quota than the first, proven by a test asserting request headers and 304 handling.
- The reserve floor is enforced and covered by a test that drives `remaining` to the floor and
  asserts the client refuses rather than continuing.
- `remaining` and `reset` are readable from the client without an extra API call.
- Existing `tests/test_http_client.py`, `tests/test_http_contract.py` and
  `tests/test_http_latency_attribution.py` still pass.
