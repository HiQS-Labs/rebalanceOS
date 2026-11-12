---
gh_issue: 377
source: https://github.com/HiQS-Labs/rebalanceOS/issues/377
title: "ci: development red — GH-178 quarantine expired and auto-promote/project-inference fixtures aged out"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-11-11
doc_type: bugfix
---

# GH-377 — GH-178 quarantine expiry and fixture aging

## Asks

- `root-noembed` is red on `development` (`88a8972`): 9 `test_auto_promote` tests and 1 `test_project_inference` test.
- Cause: the GH-178 xfail quarantine expired on 2026-11-01T00:00Z (GH-312 P13), so the tests now run unmarked. Their fixed dates sit outside the rolling windows
  (`_activity_repos` uses a 14-day SQLite `date('now')` window; `_load_calendar_events` uses 90 days from `now_utc()`).
- Fix the tests' time dependence and leave production windows unchanged. Empty `KNOWN_FAILING_GH178`.

## Acceptance

See the issue's Acceptance checklist (red control, decay falsification, suite parity, green `root-noembed`).
