---
gh_issue: 23
source: https://github.com/HiQS-Suite/rebalanceOS/issues/23
title: "GH-23 Consolidate the pulse/fleet collector stack — one collector, one scheduler story"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: feature
goal: >
  Unify the fragmented pulse and fleet collection architecture into a single Python-based
  pipeline, eliminating the bash collect.sh duplication and collapsing 5+ launchd jobs into a clean,
  resilient 3-job topology (collector, publisher, watchdog).
effort: 4
complexity: 4
risk: 3
phases: 4
ratings_provisional: true
roadmap_exempt: true
---

# GH-23 — Consolidate Pulse/Fleet Collector Stack

## Status

| What was just completed | What's next |
|---|---|
| Issue migrated from retiring repo ticket #280 and widened per operator direction to ruthlessly consolidate duplicate subsystems. | Phase 0 comprehensive read/write inventory of all 5 launchd jobs and the bash collector. |

## Why

Five launchd jobs + one external job currently orbit the same "collect state, publish it, watch it" loop:
1. `com.user.git-pulse` (bash `experimental/git-pulse/collect.sh` via `~/bin/git-pulse`)
2. `com.rebalance-os.pulse-sync` (Python `src/rebalance/ingest/pulse*`)
3. `com.rebalance-os.pulse-web-sync` (Python `scripts/pulse_web.py`)
4. `com.rebalance-os.pulse-server` (Python `scripts/pulse_server.py`)
5. `com.rebalance-os.pulse-warning-watch` (Python `scripts/pulse_warning_watch.py`)

Duplicate logic pairs:
- `experimental/git-pulse/health-check.py` vs `src/rebalance/ingest/pulse_health.py`
- `experimental/git-pulse/collect.sh` vs `src/rebalance/ingest/pulse.py`
- `scripts/pulse_common.py` vs `src/rebalance/lib/*`

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Ingest unification: port bash collect.sh to Python](#phase-1--ingest-unification-port-bash-collectsh-to-python)
- [Phase 2 — Unified scheduler topology (3 jobs)](#phase-2--unified-scheduler-topology-3-jobs)
- [Phase 3 — Shared read & health reporting consolidation](#phase-3--shared-read--health-reporting-consolidation)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `experimental/git-pulse/collect.sh`: bash script scanning repos, pulling/pushing sync state via git.
- `src/rebalance/ingest/pulse.py`: Python markdown & summary renderer for pulse.
- `scripts/pulse_server.py` & `scripts/pulse_web.py`: web daemon and static dashboard generator.
- `src/rebalance/ingest/pulse_health.py`: device heartbeat & freshness evaluation.

**Research / Inventory:**
1. Document full matrix of inputs, outputs, and trigger frequencies for each of the 5 jobs.
2. Identify dependencies between the sync mirror repo and SQLite DB.
3. Map out migration plan for `com.user.git-pulse` bash runner to pure Python `rebalance ingest pulse` or `pulse_sync.py`.

**Acceptance criteria for Phase 0:**
- Complete dataflow diagram from host scanning to web dashboard.
- Identified shared modules to replace `pulse_common.py` and `collect.sh`.

## Phase 1 — Ingest unification: port bash collect.sh to Python

- [ ] Port repo discovery, commit extraction, and heartbeat JSON emission from `collect.sh` into `src/rebalance/ingest/pulse_collector.py`.
- [ ] Replace git-conflict-prone `git pull --rebase` sync with direct API / SQLite / atomic file writes.
- [ ] Add unit tests for pulse collector in `tests/test_pulse_collector.py`.

**QA gate:**
- Python pulse collector produces byte-compatible sync payloads with zero bash dependency.

## Phase 2 — Unified scheduler topology (3 jobs)

- [ ] Consolidate launchd jobs into a clean 3-job topology:
  1. `com.rebalance-os.pulse-collector` (hourly collection & local sync)
  2. `com.rebalance-os.pulse-server` (unified server hosting API + web dashboard)
  3. `com.rebalance-os.pulse-watchdog` (consolidated health check & triage)
- [ ] Deprecate standalone `pulse-sync`, `pulse-web-sync`, and `git-pulse` launchd plists.
- [ ] Update `scripts/install_scheduler.sh` and `doctor.py` scheduler inventory.

**QA gate:**
- `rebalance doctor` verifies the 3-job topology with zero orphan jobs.

## Phase 3 — Shared read & health reporting consolidation

- [ ] Merge `health-check.py` and `pulse_health.py` into canonical `src/rebalance/ingest/pulse_health.py`.
- [ ] Re-key legacy `pulse collector:*` auto-filed issue titles (addressing parked P-007).
- [ ] Coordinate with GH-29 on shared SQL read layer.

**QA gate:**
- All pulse tests pass; `pytest tests/test_pulse_*.py -v` green.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
