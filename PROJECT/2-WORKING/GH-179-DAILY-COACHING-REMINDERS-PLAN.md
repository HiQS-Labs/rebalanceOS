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
| Initial proposal evaluated & approved; filed GH-179; created PDDA plan of record. | Update `.agents/skills/daily/SKILL.md`, execute `/relay-xyz` QA review with Codex, synchronize global skills, and open PR. |

## Context & Motivation

The `/daily` skill operates on a 15-minute cadence to synthesize operator focus across all agent prompt logs (CLIO), active git working trees, calendar schedules, and task priorities.

To elevate `/daily` into a more proactive executive co-pilot, four key capabilities are integrated:
1. **Adaptive Coaching & Encouragement**: Context-aware guidance derived directly from the rolling 2-hour velocity & trajectory metrics (flow reinforcement, context-switch warnings, pacing/break nudges, friction escape hatches).
2. **Morning Retrospectives (Yesterday's Arc)**: Crisp 2–3 sentence morning recap evaluating previous day's landed achievements and PRs from `temp/daily-log/YYYY-MM-[yesterday].log`.
3. **Monday Weekly Outlook**: 5-day horizon forecasting on Monday mornings fusing upcoming calendar events and top-ranked next actions.
4. **Apple Reminders Integration**: Leveraging Rebalance's non-locking read-only macOS Core Data snapshot engine (`src/rebalance/ingest/apple_reminders.py`) alongside calendar and Sleuth task signals.

## Proposed Changes

1. **`.agents/skills/daily/SKILL.md`**:
   - Update Step 1–Step 5 procedure to include:
     - Inspection of Apple Reminders snapshot data (`src/rebalance/ingest/apple_reminders.py`).
     - Morning Yesterday Retrospective generation on early-morning cycles (reading yesterday's log).
     - Monday Weekly Horizon generation on Monday cycles (evaluating 5-day calendar and ranked priorities).
     - Adaptive Coaching & Focus Guidance block in the synthesis output.
2. **Global Skill Parity**:
   - Synchronize the updated `SKILL.md` into:
     - `~/.claude/skills/daily/`
     - `~/.codex/skills/daily/`
     - `~/.gemini/config/skills/daily/`
     - `~/.gemini/antigravity/skills/daily/`
     - `~/.agents/skills/daily/`

## Verification Plan

- Run `pytest` on existing test suite to ensure no regressions.
- Conduct a `/relay-xyz` QA review with Codex against the updated skill specification and plan doc.
- Verify that the updated skill is syntactically valid YAML frontmatter and well-structured Markdown.
