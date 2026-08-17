---
title: "Phase fe2 Consolidate Pulse Collector Stack"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase fe2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase fe2 — Consolidate Pulse/Fleet Collector Stack (#23)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase fe2 in marathon harness. |

## Objective
Unify the pulse and fleet collection architecture into a single Python pipeline, porting bash `collect.sh` to Python and consolidating launchd jobs into a clean 3-job topology.

## Context & Files
- Target files: `src/rebalance/ingest/pulse_collector.py`, `src/rebalance/ingest/pulse_health.py`, `scripts/install_scheduler.sh`, `scripts/lib/scheduler_common.sh`, `src/rebalance/doctor.py`
- Issue: #23 — Five launchd jobs + bash/python fragmentation caused multiple fleet collection failures.

## Tasks
1. Port repo discovery, commit scanning, and heartbeat payload generation from `experimental/git-pulse/collect.sh` to `src/rebalance/ingest/pulse_collector.py`.
2. Define a clean 3-job launchd topology: `pulse-collector` (hourly collection), `pulse-server` (web daemon), and `pulse-watchdog` (health check & triage).
3. Update `doctor.py` and 3-eyes job supervisor catalog to recognize the consolidated topology.

## Definition of Done
- `pytest tests/test_pulse_*.py tests/test_scheduler_policy.py` passes; zero bash dependencies in pulse collection.
