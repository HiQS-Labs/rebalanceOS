---
gh_issue: 179
source: https://github.com/HiQS-Labs/rebalanceOS/issues/179
title: "GH-179 Daily Skill: Adaptive Coaching, Morning Retrospectives, Weekly Outlook, and Apple Reminders Integration"
status: "Working"
created: 2026-09-04
updated: 2026-09-04
owner: noel
doc_type: feature
goal: >
  Enhance the `/daily` skill specification and supporting signal telemetry to incorporate data-grounded adaptive coaching/encouragement, morning retrospective analysis from previous day logs, Monday weekly horizon forecasting, and direct awareness of macOS Apple Reminders snapshots.
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: true
---

# GH-179 — Daily Skill: Adaptive Coaching, Morning Retrospectives, Weekly Outlook & Apple Reminders

## Status

| What was just completed | What's next |
|---|---|
| Refined `.agents/skills/daily/SKILL.md` addressing Codex review (deterministic thresholds, exactly-once time-gated horizons, Apple Reminders graceful degradation, fixed schema). | Run second Codex QA review turn via `/relay-xyz` to obtain approval, sync global skill paths, and open PR. |

## Context & Motivation

The `/daily` skill operates on a 15-minute cadence to synthesize operator focus across all agent prompt logs (CLIO), active git working trees, calendar schedules, and task priorities.

To elevate `/daily` into a proactive executive co-pilot while maintaining rigor:
1. **Adaptive Coaching & Guidance (Falsifiable & Signal-Grounded)**:
   - Evaluated against 4 strict trigger rules (Flow State >= 2 cycles, Fragmentation >= 3 repos in 45m, Pacing >= 120m or meeting T-15m, Blocker >= 2 cycles).
   - Every emitted nudge cites its triggering telemetry (e.g. `[Trigger: ...]`).
2. **Time-Gated Horizons (Exactly-Once Semantics)**:
   - **Morning Retrospective (Yesterday's Arc)**: Generated on the first synthesis cycle written to `temp/daily-log/YYYY-MM-DD.log` for the day.
   - **Monday Weekly Horizon**: Generated on the first synthesis cycle written on Mondays (`weekday == 0`), evaluating the 5-day calendar.
3. **Apple Reminders Integration**:
   - Read-only macOS Core Data snapshot extraction (`src/rebalance/ingest/apple_reminders.py:extract_apple_reminders`).
   - Filter to incomplete items with graceful non-macOS/permissions degradation.
4. **Deterministic Log-Entry Contract**:
   - Fixed schema with explicit headers, section ordering, and quantitative velocity bases.

## Proposed Changes

1. **`.agents/skills/daily/SKILL.md`**:
   - Core specification update across Steps 1–6.
2. **Global Skill Parity**:
   - Synchronize `SKILL.md` into `~/.claude/skills/daily/`, `~/.codex/skills/daily/`, `~/.gemini/config/skills/daily/`, `~/.gemini/antigravity/skills/daily/`, `~/.agents/skills/daily/`.

## Verification Plan

- Run `pytest` on `rebalanceOS` test suite.
- Re-run `/relay-xyz` with Codex to confirm approval.
- Open PR on `origin/development`.
