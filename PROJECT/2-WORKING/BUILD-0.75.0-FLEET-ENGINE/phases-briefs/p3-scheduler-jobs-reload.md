---
title: "Phase fe3 Reconcile and Load Scheduler Jobs"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase fe3 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase fe3 — Reconcile & Load Watchdog Scheduler Jobs (#22)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase fe3 in marathon harness. |

## Objective
Reconcile and bootstrap the three unloaded watchdog launchd jobs (`health-check`, `health-check-triage`, `pulse-warning-watch`) onto the host machine.

## Context & Files
- Target files: `scripts/install_health_check_scheduler.sh`, `scripts/install_health_check_triage_scheduler.sh`, `scripts/install_pulse_warning_watch_scheduler.sh`, `src/rebalance/doctor.py`
- Issue: #22 — Scheduler watchdog plists were installed but unloaded in `launchctl`.

## Tasks
1. Bootstrap consolidated/reconciled launchd jobs in `gui/$(id -u)`.
2. Verify `doctor.py` scheduler checks report `OK` for all registered jobs.
3. Confirm heartbeat log files in `temp/logs/` update periodically.

## Definition of Done
- `rebalance doctor` reports zero scheduler FAIL / UNLOADED warnings.
