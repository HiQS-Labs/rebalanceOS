---
gh_issue: 4
source: https://github.com/HiQS-Suite/rebalanceOS/issues/4
title: "GH-4 git-pulse collector for Fleet device Mac Studio dead since 2026-08-11"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: bugfix
goal: >
  Resolve git-pulse merge conflicts on Fleet device Mac Studio mirror repo and reload
  its launchd hourly collector job with monitoring supervision.
effort: 1
complexity: 1
risk: 2
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-4 — Git-Pulse Collector for Fleet Device Mac Studio Dead

## Status

| What was just completed | What's next |
|---|---|
| Issue intake and root-cause analysis on the host machine (`noels-mac-studio`). Log error identified at `~/.config/git-pulse/logs/git-pulse.err` due to `git pull --rebase` conflict in `sync_repo_dir`. | Phase 0 verification on the local mirror clone, followed by rebase resolution and launchd bootstrap. |

## Why

The dashboard displays "pulse collector:noel's Mac Studio ALERT — last scan 2026-08-11 7:08 PM", which is beyond the 24h `ALERT_HOURS` threshold in `src/rebalance/ingest/pulse_health.py:35`.

Root causes:
1. `~/Library/LaunchAgents/com.user.git-pulse.plist` is installed on disk but not loaded in `launchctl`.
2. The error log `~/.config/git-pulse/logs/git-pulse.err` reveals a `git pull --rebase` merge conflict in `sync/calendar/latest.json` and `sync/email/latest.json` inside `experimental/git-pulse/collect.sh:479-480`.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Operational resolution & launchd bootstrap](#phase-1--operational-resolution--launchd-bootstrap)
- [Phase 2 — Verification & supervision integration](#phase-2--verification--supervision-integration)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `experimental/git-pulse/collect.sh:479-480`: executes `git pull --rebase` in `sync_repo_dir` without auto-aborting on unresolvable JSON conflicts.
- `src/rebalance/ingest/pulse_health.py:35`: defines `ALERT_HOURS = 24`.
- `scripts/pulse_server.py:310-364`: `/api/refresh` handles Reminders/static HTML but does not invoke pulse collectors.

**Spike/Research questions:**
1. Check the local `sync_repo_dir` git status at `~/.config/git-pulse/sync/` (or configured location in `~/.config/git-pulse/config.sh`).
2. Verify whether conflict resolution requires `git rebase --abort` and re-syncing from canonical state.
3. Confirm `launchctl list | grep git-pulse` output on host.

**Acceptance criteria for Phase 0:**
- Exact conflict state in the local sync mirror is documented.
- Remediation steps for `collect.sh` to fail safely (or abort rebase automatically) are validated.

## Phase 1 — Operational resolution & launchd bootstrap

- [ ] Abort or resolve in-flight merge conflicts in `sync_repo_dir` (`sync/calendar/latest.json`, `sync/email/latest.json`).
- [ ] Run a manual test pass: `/Users/noelsaw/bin/git-pulse` or `bash experimental/git-pulse/collect.sh`.
- [ ] Bootstrap launchd job: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.git-pulse.plist`.
- [ ] Verify job status in `launchctl list com.user.git-pulse`.

**QA gate:**
- Manual run exits 0 without git conflicts.
- `launchctl list` confirms `com.user.git-pulse` registered and running.

## Phase 2 — Verification & supervision integration

- [ ] Wait for next scheduled scan cycle or trigger manual scan.
- [ ] Check `rebalance doctor` and `src/rebalance/ingest/pulse_health.py` output; confirm alert clears.
- [ ] Coordinate with GH-23 (pulse/fleet collector consolidation) and 3-eyes job supervisor.

**QA gate:**
- Dashboard shows device heartbeat fresh (<1h ago).
- Health alert on Mac Studio collector is resolved.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
