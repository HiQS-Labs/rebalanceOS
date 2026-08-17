---
title: "Phase fe4 Mac Studio Collector Recovery"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase fe4 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase fe4 — Mac Studio Pulse Collector Conflict Recovery (#4)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase fe4 in marathon harness. |

## Objective
Resolve merge conflicts in the local sync mirror repo on Mac Studio, reload the collector launchd job, and verify live device heartbeat freshness.

## Context & Files
- Target files: `~/.config/git-pulse/sync/`, `src/rebalance/ingest/pulse_health.py`
- Issue: #4 — Mac Studio git-pulse collector dead since 2026-08-11 due to JSON merge conflict in `sync_repo_dir`.

## Tasks
1. Abort/resolve in-flight merge conflicts in `sync_repo_dir` (`sync/calendar/latest.json`, `sync/email/latest.json`).
2. Run manual collector test cycle and ensure clean JSON emission.
3. Verify `pulse_health.py` reports Mac Studio heartbeat fresh (<1h) and clears dashboard alert.

## Definition of Done
- `pulse_health.py` verifies device heartbeat fresh (<1h); dashboard alert cleared.
