---
title: "Phase si4 Wire Slack Resolver Into Whats Next"
status: "Draft"
created: 2026-08-25
updated: 2026-08-25
owner: noel
goal: "Phase si4 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase si4 — Wire resolve_slack_user Into sleuth_candidates (#123)

## Status

| What was just completed | What's next |
|---|---|
| Phases si1-si3 restored the ingest path and its reporting. | Execute phase si4 in marathon harness. |

## Objective
Make "What's Next" show human names for Sleuth reminder items by calling the live resolver that
already exists, instead of the static map that cannot resolve an unmapped ID.

## Context & Files
- Target files: `src/rebalance/ingest/next_actions.py`, `tests/test_next_actions.py`
- Issue #123: `resolve_slack_user()` (`src/rebalance/ingest/slack_users.py`) — the live `users.info`
  resolver with write-through cache, built in #114 and merged 2026-08-21 in PR #118 — is real and
  working, but `sleuth_candidates()` (`src/rebalance/ingest/next_actions.py:516-535`) still calls
  `load_user_map()` and reads only the static gitignored `temp/slack_users.json`.
- The dashboard has therefore shown raw IDs like `@U032TCHJ8` in production for days on a machine
  running current `development`. The feature shipped; nothing called it. That is the same failure
  shape as the dead layout toggle and the blank date pill — work that reports success while
  changing nothing a user can see.

## Tasks
1. Call `resolve_slack_user()` from `sleuth_candidates()` for sender attribution, keeping the
   static map as the fast path where it already has an answer.
2. Keep the write-through cache doing its job — one uncached ID should not mean one API call on
   every subsequent render.
3. Fall back to the raw ID when the API cannot resolve a user, and make that fallback visible in
   whatever the function reports rather than silently indistinguishable from a real name.
4. Respect si1's budget: resolution is a nice-to-have, so it must not be what spends the last of
   the hourly quota.

## Definition of Done
- A Sleuth candidate whose sender is absent from `temp/slack_users.json` resolves to a display
  name through the live resolver, asserted by test.
- A resolver failure degrades to the raw ID without raising, asserted by test.
- Repeated renders of the same sender do not repeat the API call, asserted by test.
- `tests/test_next_actions.py` and the parity, precompute and privacy suites still pass.
