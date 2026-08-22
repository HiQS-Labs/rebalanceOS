---
title: "Phase ro1 Live Slack User Resolver and Write-Through Cache Origin"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase ro1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase ro1 — Live Slack User Resolver & Cache Origin (#114)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase ro1 in marathon harness. |

## Objective
Implement live Slack user name resolution in `src/rebalance/ingest/slack_users.py` backed by optional Slack API token or publisher-embedded names, caching resolved user maps write-through to `temp/slack_users.json`, and add comprehensive test coverage in `tests/test_slack_users.py`.

## Context & Files
- Target files: `src/rebalance/ingest/slack_users.py`, `src/rebalance/ingest/config.py`, `tests/test_slack_users.py`
- Issue: #114 — Durable resolver so new machines/installs do not degrade to raw Slack UIDs.

## Tasks
1. Support reading embedded display names from export payload or querying Slack Web API `users.info` when `slack_bot_token` is present in config.
2. Maintain `temp/slack_users.json` as a write-through cache rather than an unbacked manual file.
3. Create `tests/test_slack_users.py` covering cache hits, cache misses, token resolution, and fallback behavior.
4. Verify tests pass with `.venv/bin/pytest tests/test_slack_users.py -q`.

## Definition of Done
- `pytest tests/test_slack_users.py` passes with >90% coverage.
