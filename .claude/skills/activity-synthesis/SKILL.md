---
name: activity-synthesis
description: >
  15-minute multi-source activity synthesis engine. Monitors the operator's multi-agent
  prompt log (`0. Claude Prompts.md` / CLIO) and fuses it with Rebalance's live work signal
  (ranked next actions, calendar events, Sleuth reminders, GitHub activity) and device-wide
  git state (`collect.sh`). Appends 15-minute syntheses into deterministic daily logs at
  `temp/daily-log/YYYY-MM-DD.log`, evaluating trajectory and velocity over the rolling
  2-hour window. Trigger on "synthesize activity", "what am I working on", "monitor prompts",
  "activity synthesis".
---

# Activity Synthesis — Prompts Log + Live Work Signal + Git Telemetry

Continuously answers: **"What is the operator actually working on right now across all agents, repos, and systems, and what is the trajectory/velocity of their work?"**

Combines two independent primary sources with temporal trajectory analysis:
1. **Multi-Agent Prompt Log** — `/Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md` (and `~/.claude/prompt-log.jsonl` / `clio_prompts` table in SQLite), capturing real-time human intent, instructions to Claude/Agy/Codex/ZCode, and agent turn handoffs.
2. **Rebalance Work Activity Signal & Git State** — Ranked next actions (`get_next_actions`), upcoming calendar events (`calendar_events`), Sleuth reminders, and device-wide git activity (`.claude/skills/rebalance/collect.sh`).
3. **Daily Log & Trajectory Analysis** — Maintains deterministic daily logs in `temp/daily-log/YYYY-MM-DD.log`. Inspects the preceding **2-hour window** to derive **velocity** (rate of completions/commits) and **trajectory** (shifts in focus, momentum, bottlenecks) to shape each 15-minute synthesis.

---

## Guardrails & Principles

- **Reuse Existing Subsystems**: Do not create parallel pipelines or bespoke ad-hoc trackers. Query the resolved SQLite database (`src/rebalance/paths.py:resolve_db()`), `get_next_actions()`, `clio_prompts`, and `.claude/skills/rebalance/collect.sh`.
- **Read-Only Against Repositories**: Synthesis inspects files and SQLite tables; it never mutates git state, resets branches, or alters worktrees.
- **Deterministic Daily Logging**: Output records append to `temp/daily-log/YYYY-MM-DD.log` (gitignored under `temp/`).

---

## Procedure (Every 15 Minutes)

### Step 1 — Read Recent Multi-Agent Prompts (Intent Signal)
Inspect the top of `/Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md` (or query `clio_prompts` table in `rebalance.db`).
- Extract prompts within the current 2-hour window.
- Identify active repositories, tools/agents (Claude, Agy, Codex, ZCode), and explicit directives (e.g. PR reviews, feature builds, hotfixes, refactors).

### Step 2 — Read Rebalance Live Work Signal (Operational Signal)
- Call `get_next_actions()` / load ranked next actions from `rebalance.db`.
- Query upcoming calendar events for today from `calendar_events` (or trigger `rebalance calendar-sync` if needed).
- Query active Sleuth reminders.

### Step 3 — Scan Device-Wide Git Activity (Code Signal)
- Execute `bash .claude/skills/rebalance/collect.sh` (or inspect recent commits from `github_commits` / `github_activity`).
- Identify repos with `ACTIVE` or `WARM` worktrees, recent commit timestamps, unmerged branches, and dirty working trees.

### Step 4 — Evaluate 2-Hour Trajectory & Velocity
- Read `temp/daily-log/YYYY-MM-DD.log` (and yesterday's log if at start of day).
- Inspect the last 2 hours of snapshots to evaluate:
  - **Trajectory**: Direction of focus across repos, projects, and domains (e.g., pivot from incident fix to skill tooling, shift to PR review).
  - **Velocity**: Rate of task completions, commit cadence, multi-agent handoff speed, resolution of blockers.
  - **Momentum**: Accelerating vs decelerating workstreams, impending context switches (calendar events, deadlines).

### Step 5 — Synthesize and Report
Structure the output clearly:
1. **Current Focus & Active Swarm State (Last 15–30 min)**: What is actively being built or orchestrated right now.
2. **Trajectory & Velocity (Past 2 Hours)**: Momentum, completed arcs, and rate of progress across repos.
3. **Reconciled Operational Horizon**: How live coding matches against calendar commitments and ranked priorities for the next 1–2 hours.

### Step 6 — Append to Daily Log
Append the timestamped synthesis entry into `temp/daily-log/YYYY-MM-DD.log`.
