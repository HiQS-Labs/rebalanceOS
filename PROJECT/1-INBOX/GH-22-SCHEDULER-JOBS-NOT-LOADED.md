---
gh_issue: 22
source: https://github.com/HiQS-Suite/rebalanceOS/issues/22
title: "GH-22 Three scheduler jobs not loaded on the Mac Studio"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: bugfix
goal: >
  Reconcile, configure, and bootstrap the three unloaded watchdog launchd jobs
  (health-check, health-check-triage, pulse-warning-watch) on the host machine.
effort: 2
complexity: 2
risk: 2
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-22 — Three Scheduler Jobs Not Loaded on Mac Studio

## Status

| What was just completed | What's next |
|---|---|
| Issue migrated from retiring repo tickets #204/#205; surfaced via `rebalance doctor` on 0.69.8. | Phase 0 audit of launchd plists on disk vs. active registration in `launchctl`. |

## Why

`rebalance doctor` reports three watchdog scheduler jobs not loaded on Mac Studio:
- `scheduler:health-check` — runs `scripts/health_issue_reporter.py`
- `scheduler:health-check-triage` — runs `scripts/health_issue_reporter.py` triage mode
- `scheduler:pulse-warning-watch` — runs `scripts/pulse_warning_watch.py`

Plists exist in `~/Library/LaunchAgents/` but are not registered in `launchctl`, preventing background health issue auto-reporting.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Installation and bootstrap reconciliation](#phase-1--installation-and-bootstrap-reconciliation)
- [Phase 2 — Verification via doctor and triage tests](#phase-2--verification-via-doctor-and-triage-tests)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `scripts/install_health_check_scheduler.sh`: installer for `com.rebalance-os.health-check`.
- `scripts/install_health_check_triage_scheduler.sh`: installer for `com.rebalance-os.health-check-triage`.
- `scripts/install_pulse_warning_watch_scheduler.sh`: installer for `com.rebalance-os.pulse-warning-watch`.
- `scripts/health_issue_reporter.py`: auto-reports `doctor` failures as GitHub issues.
- `scripts/pulse_warning_watch.py`: scans pulse dashboard for warnings.
- `src/rebalance/doctor.py`: checks `_check_scheduler_jobs()` against required launchd labels.

**Spike / Research questions:**
1. Check `~/Library/LaunchAgents/com.rebalance-os.*.plist` file contents and permissions.
2. Determine why jobs were unloaded (post-reboot state, permissions, or manual unload).
3. Evaluate consolidation with GH-23 (collector/watchdog stack unification).

**Acceptance criteria for Phase 0:**
- Plist integrity and virtual environment paths in the templates verified.
- Confirmation of target launchd domain (`gui/$(id -u)`).

## Phase 1 — Installation and bootstrap reconciliation

- [ ] Execute `bash scripts/install_health_check_scheduler.sh`.
- [ ] Execute `bash scripts/install_health_check_triage_scheduler.sh`.
- [ ] Execute `bash scripts/install_pulse_warning_watch_scheduler.sh`.
- [ ] Verify `launchctl list | grep rebalance-os` shows all three jobs active with exit code 0 or scheduled intervals.

**QA gate:**
- All three plists loaded in user launchd session.

## Phase 2 — Verification via doctor and triage tests

- [ ] Run `rebalance doctor` (or `python -m rebalance.doctor`).
- [ ] Confirm all scheduler job checks in `doctor` report `OK` with 0 `FAIL`.
- [ ] Verify log files in `temp/logs/` or `~/Library/Logs/` receive heartbeat ticks.

**QA gate:**
- `rebalance doctor` reports clean scheduler status.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
