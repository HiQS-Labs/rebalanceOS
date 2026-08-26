---
title: "Phase si2 Two-Tier Ingest Cadence"
status: "Draft"
created: 2026-08-25
updated: 2026-08-25
owner: noel
goal: "Phase si2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase si2 — Two-Tier Ingest Cadence: Hourly Delta, Daily Deep Scan (#62)

## Status

| What was just completed | What's next |
|---|---|
| Phase si1 landed the budget and conditional-request machinery. | Execute phase si2 in marathon harness. |

## Objective
Stop the hourly sync from walking all 60+ registered repos. The hourly pass covers only repos with
recent activity; the exhaustive scan moves to once a day.

## Context & Files
- Target files: `src/rebalance/ingest/github_scan.py`, `tests/test_github_scan.py`
- Issue #62: the hourly job iterates 60+ repos pulling commits, issues and PR comments, exhausts
  the limit in under 15 minutes, then runs 40-50 minutes before dying on 403s.
- Depends on si1: the budget and ETag cache must exist before the cadence can lean on them.

## Tasks
1. Split the scan into an hourly delta pass, scoped to actively-changing repos, and a daily deep
   pass that still covers everything. Derive "active" from signal the repo already has rather than
   a new hand-maintained list.
2. Route both passes through si1's conditional requests so an unchanged repo is nearly free.
3. Have the hourly pass consult si1's budget before starting and degrade deliberately when the
   budget is short — fewer repos, reported plainly — instead of failing partway through.
4. Make a partial pass distinguishable from a complete one in whatever the job reports, so a
   degraded run cannot be mistaken for a clean one.

## Definition of Done
- An hourly pass over a fixture repo set touches only the active subset, asserted by test.
- A full daily pass still covers every registered repo, asserted by test.
- A budget-constrained hourly pass degrades and says so rather than raising, asserted by test.
- `tests/test_github_scan.py` passes, including the existing cases.

## Explicitly out of scope
Changing launchd schedules or installer scripts. This phase changes what the scan does when it
runs; wiring the daily cadence into the scheduler is separate work against #59/#60.
