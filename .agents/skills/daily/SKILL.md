---
name: daily
description: >
  15-minute multi-source daily work synthesizer. Monitors the operator's multi-agent
  prompt log (`0. Claude Prompts.md` / CLIO) and fuses it with Rebalance's live work signal
  (ranked next actions, calendar events, Sleuth reminders, Apple Reminders, GitHub activity)
  and device-wide git state (`collect.sh`). Appends 15-minute syntheses into deterministic daily logs at
  `temp/daily-log/YYYY-MM-DD.log`, evaluating trajectory and velocity over the rolling
  2-hour window. Trigger on "/daily", "daily", "what am I working on", "synthesize activity",
  "daily log", "monitor prompts".
---

# Daily — Live Prompts Log + Work Signal + Git Telemetry

Continuously answers: **"What is the operator actually working on right now across all agents, repos, and systems, what is the trajectory/velocity of their work, and what guidance helps maintain momentum?"**

Combines multi-source operational telemetry with temporal trajectory analysis and adaptive coaching:
1. **Multi-Agent Prompt Log** — `/Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md` (and `~/.claude/prompt-log.jsonl` / `clio_prompts` table in SQLite), capturing real-time human intent, instructions to Claude/Agy/Codex/ZCode, and agent turn handoffs.
2. **Rebalance Work Activity Signal & Git State** — Ranked next actions (`get_next_actions`), upcoming calendar events (`calendar_events`), Sleuth task reminders (`sleuth_reminders`), macOS Apple Reminders snapshots (`src/rebalance/ingest/apple_reminders.py`), and device-wide git activity (`.claude/skills/rebalance/collect.sh`).
3. **Daily Log & Trajectory Analysis** — Maintains deterministic daily logs in `temp/daily-log/YYYY-MM-DD.log`. Inspects the preceding **2-hour window** to derive **velocity** (rate of completions/commits) and **trajectory** (shifts in focus, momentum, bottlenecks).
4. **Adaptive Coaching & Guidance** — Generates context-aware, data-grounded nudges (flow reinforcement, context-switching warnings, pacing/break alerts, and blocker escape hatches).
5. **Cadenced Horizons (Morning Retro & Monday Outlook)** — Produces a 2–3 sentence retrospective on yesterday's achievements every morning and a 5-day horizon forecast every Monday.

---

## Guardrails & Principles

- **Reuse Existing Subsystems**: Do not create parallel pipelines or bespoke ad-hoc trackers. Query the resolved SQLite database (`src/rebalance/paths.py:resolve_db()`), `get_next_actions()`, `clio_prompts`, `calendar_events`, `sleuth_reminders`, Apple Reminders snapshots, and `.claude/skills/rebalance/collect.sh`.
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
- Query active Sleuth reminders (`sleuth_reminders`).
- Check local macOS Apple Reminders snapshot (`src/rebalance/ingest/apple_reminders.py`).

### Step 3 — Scan Device-Wide Git Activity (Code Signal)
- Execute `bash .claude/skills/rebalance/collect.sh` (or inspect recent commits from `github_commits` / `github_activity`).
- Identify repos with `ACTIVE` or `WARM` worktrees, recent commit timestamps, unmerged branches, and dirty working trees.

### Step 4 — Evaluate 2-Hour Trajectory, Velocity & Cadence

1. **2-Hour Window Analysis**:
   - Read `temp/daily-log/YYYY-MM-DD.log`.
   - **Trajectory**: Direction of focus across repos, projects, and domains (e.g., pivot from incident fix to skill tooling, shift to PR review).
   - **Velocity**: Rate of task completions, commit cadence, multi-agent handoff speed, resolution of blockers.
   - **Momentum**: Accelerating vs decelerating workstreams, impending context switches (calendar events, deadlines).

2. **Special Cadence Checks**:
   - **🌅 Morning Retrospective (Yesterday's Arc)**: On early morning cycles / first cycle of the day (~8:00 AM / Cycle 0), inspect `temp/daily-log/YYYY-MM-[yesterday].log` and summarize yesterday's landed commits, PRs, and finished arcs in 2–3 crisp sentences.
   - **📅 Monday Weekly Horizon**: On Monday morning cycles (~8:00 AM – 9:00 AM), evaluate the upcoming 5-day calendar (`calendar_events` Monday–Friday) and top-ranked next actions to outline key weekly milestones, meeting load distribution, and deep work runways.

3. **Adaptive Coaching Evaluation**:
   - **Flow State & Momentum Reinforcement**: When sustained single-trunk progress is high across $\ge 2$ cycles.
   - **Context-Switching & Fragmentation Alert**: When prompts show rapid bouncing across $\ge 3$ unrelated repos within 45 minutes; nudge to land or park active WIP first.
   - **Pacing & Break Reminders**: When continuous high-intensity execution runs past 90–120 minutes or when an external calendar event is $T-15\text{m}$ away.
   - **Friction & Blocker Coaching**: When an issue or test suite stalls repeatedly, nudge to drop down to Rung 1 (`/debug-mantra`) or a quick `/consult`.

### Step 5 — Synthesize and Report
Structure the output clearly:
1. **[If Morning] 🌅 Yesterday's Arc (2–3 sentences)**: Context from the previous day's landed work.
2. **[If Monday Morning] 📅 Weekly Operational Horizon**: Key milestones, meeting load distribution, and deep work blocks for the week.
3. **🎯 Current Focus & Active Swarm State (Last 15–30 min)**: What is actively being built or orchestrated right now.
4. **📈 Trajectory & Velocity (Past 2 Hours)**: Momentum, completed arcs, and rate of progress across repos.
5. **⏱️ Reconciled Operational Horizon**: How live coding matches against calendar commitments, Reminders (Sleuth + Apple Reminders), and ranked priorities for the next 1–2 hours.
6. **🧭 Adaptive Coaching & Focus Nudge**: 1–2 data-grounded guidance sentences.

### Step 6 — Append to Daily Log
Append the timestamped synthesis entry into `temp/daily-log/YYYY-MM-DD.log`.
