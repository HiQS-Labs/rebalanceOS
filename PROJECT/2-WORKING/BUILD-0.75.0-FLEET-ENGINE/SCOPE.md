---
title: "Build 0.75.0 Fleet Engine Marathon Scope"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Autonomous marathon execution plan for Release 0.75.0 Fleet Engine"
effort: 4
complexity: 4
risk: 3
phases: 5
ratings_provisional: false
roadmap_exempt: false
---

# Build 0.75.0 — Fleet Engine Scope

## Status

| What was just completed | What's next |
|---|---|
| Phase briefs and MARATHON.yaml generated following Relay XYZ consult with Codex. | Preflight and dry run validation of marathon plan. |

## Overview

Build 0.75.0 consolidates the pulse/fleet collection and scheduler ecosystem, establishes a shared presentation query layer, recovers host device collector jobs, and delivers multi-signal auto-promotion:
- Phase `fe1` (#29): Extract the 6 duplicate SQL query families into `src/rebalance/ingest/db/queries.py` and unify web app mounting in `scripts/pulse_server.py`.
- Phase `fe2` (#23): Consolidate pulse/fleet collector stack into a Python pipeline and streamline launchd topology into 3 supervised jobs.
- Phase `fe3` (#22): Reconcile and load Mac Studio watchdog scheduler jobs.
- Phase `fe4` (#4): Resolve Mac Studio git-pulse merge conflicts and verify live host heartbeat.
- Phase `fe5` (#1): Implement 5-signal sustained-activity project auto-promotion with 20h wall-clock burst guard.

## Execution

```bash
.xyz/relay-automation/marathon.sh \
  --plan PROJECT/2-WORKING/BUILD-0.75.0-FLEET-ENGINE/MARATHON.yaml \
  --pre-advance-cmd "pytest tests/ -q" \
  --dry-run
```
