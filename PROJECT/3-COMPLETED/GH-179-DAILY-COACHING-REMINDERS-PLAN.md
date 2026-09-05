---
gh_issue: 179
source: https://github.com/HiQS-Labs/rebalanceOS/issues/179
title: "GH-179 Daily Skill: Adaptive Coaching, Morning Retrospectives, Weekly Outlook, and Apple Reminders Integration"
status: Complete
created: 2026-09-04
updated: 2026-09-05
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
| Implemented enhanced specification, completed 2-round `/relay-xyz` QA review with Codex (Approved), verified pytest suite, synchronized global skill locations, and opened PR [#180](https://github.com/HiQS-Labs/rebalanceOS/pull/180). | Merge PR [#180](https://github.com/HiQS-Labs/rebalanceOS/pull/180) into `development`. |

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
   - Synchronized `SKILL.md` into:
     - `~/.claude/skills/daily/`
     - `~/.codex/skills/daily/`
     - `~/.gemini/config/skills/daily/`
     - `~/.gemini/antigravity/skills/daily/`
     - `~/.agents/skills/daily/`

## Verification & QA Evidence

- **Pytest**: Passed clean (0 errors/failures).
- **Relay Review**: Approved by Codex in Round 2 (`relay-system/2026-09-04/gh179-daily-coaching-qa.md`).
- **Pull Request**: Opened [#180](https://github.com/HiQS-Labs/rebalanceOS/pull/180).

## Lessons Learned (For Future Agents)

Distilled at reconcile time from the plan above, PR #180, and the two-round relay record
(`relay-system/2026-09-04/gh179-daily-coaching-qa.md`); the implementing session did not write
this section, and the reconciler refuses to retire a doc without it.

- **A coaching nudge without a cited trigger is an opinion.** Every nudge names the rule that
  fired and the numbers behind it (`[Trigger: 3 repos touched in 45m: …]`). That is what makes
  "you seem fragmented" falsifiable instead of vibes — the same bar as `GUIDING-PRINCIPLES.md`
  "ATTESTED".
- **Time-gated sections need exactly-once semantics, not clock checks.** The morning
  retrospective and Monday horizon key off "first synthesis cycle written to today's log", not
  "is it before 09:00". A clock check re-fires on every cycle in the window; a first-write check
  fires once even if the machine slept through the morning.
- **Degrade, don't fail, on optional sources.** Apple Reminders is a macOS Core Data read that
  can be denied by TCC or absent entirely. It warns and continues; a missing optional input must
  never take down the synthesis it feeds.
- **Five copies of `SKILL.md` is a maintenance cost, not a feature.** The skill is synced into
  `~/.claude`, `~/.codex`, two `~/.gemini` trees and `~/.agents`. Any future edit has to fan out
  to all five or the agents silently disagree. Worth a sync check before that bites.
