---
gh_issue: 148
source: https://github.com/HiQS-Labs/rebalanceOS/issues/148
title: "GH-148 slice 1 — incremental per-item github-sync: skip the PR/issue fan-out when updated_at is unchanged"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). Slice 1 of the issue's five fix directions; the rest stay on #148."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: bugfix
rating: "pri/sev/appeal/effort 90/90/85/30 · calc 295"
effort: 3
complexity: 3
risk: 2
phases: 1
ratings_provisional: false
goal: >
  Stop re-fetching every PR/issue's comments, reviews, commits and check-runs on every hourly run.
  Compare each listed item's `updated_at` against the value already stored and skip the fan-out when
  it has not moved. This one change is ~90% of the measured call volume.
non_goals:
  - Fix directions 2–5 in the issue (repo-level pushed_at gating, tiered cadence, 403 hygiene, ETag/GraphQL). They stay on #148 as later slices.
  - Changing the 30-day window or the collector registry.
---

# GH-148 slice 1 — incremental per-item github-sync

## Status

| What was just completed | What's next |
|---|---|
| Capture written for the 2026-09-05 marathon, scoped to fix direction #1 only. | Builder lane: implement the `updated_at` short-circuit in `sync_github_repo`, with a red control proving the fan-out was previously unconditional. |

## Why

The hourly job makes 5–7k API calls against a 5,000/hr budget. Measured endpoint mix on the 09-02 12:45 run (5,534 attempts): ~90% is the per-item fan-out — `/issues/{n}/comments` 2,223, `/pulls/{n}` 562, `/pulls/{n}/comments` 563, `/pulls/{n}/commits` 575, `/pulls/{n}/reviews` 562, `/commits/{sha}/check-runs` 560 — re-fetched in full for every item in the 30-day window regardless of whether anything changed.

## Where

`sync_github_repo` in [src/rebalance/ingest/github_knowledge.py:423](../../src/rebalance/ingest/github_knowledge.py#L423). The list responses already carry `updated_at` (stored at `:241`); the fan-out begins at `:476` and is unconditional.

## Acceptance

Verbatim from #148, restricted to what slice 1 can deliver:

- A normal hourly run stays well under the 5,000/hr budget (target: < 1,000 attempts) with equal freshness for repos that actually changed.
- Zero rate-limit 403s on a normal day; run duration < 60 min (ideally < 15).
- A rate-limited or truncated run is named in `index_status` signal health, never read as a quiet day.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_github_knowledge.py tests/test_github_scan.py -q",
  "fix_probes": [
    { "type": "grep_absent", "path": "src/rebalance/ingest/github_knowledge.py", "pattern": "stored_updated_at" }
  ],
  "artifacts": [
    "src/rebalance/ingest/github_knowledge.py",
    "tests/test_github_knowledge.py"
  ],
  "remediation": {
    "source": "issue#148",
    "criteria": "sync_github_repo skips the per-item fan-out when the listed updated_at equals the stored value; a red control shows the fan-out was unconditional before."
  },
  "lanes": { "agy_safe": ["src/rebalance/ingest/github_knowledge.py", "tests/test_github_knowledge.py"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1 — implement + red control

- [ ] Red control first: a test that asserts the fan-out endpoints are called for an item whose `updated_at` is unchanged — it must FAIL on the current tree, and is then inverted.
- [ ] Read the stored `updated_at` for each listed item before fanning out; skip when equal. Missing stored value → fetch (first sight).
- [ ] Count attempts in the test via the existing client seam; assert the skip path makes zero fan-out calls.

### QA checklist — Phase 1
- [ ] The red control was witnessed red before the fix landed.
- [ ] No change to what is stored for items that DID change.
- [ ] Full `tests/test_github_knowledge.py` + `tests/test_github_scan.py` green.
