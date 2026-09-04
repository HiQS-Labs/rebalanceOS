---
name: activity-synthesis
description: >
  15-minute multi-source activity synthesis engine. Monitors the operator's multi-agent
  prompt log (`0. Claude Prompts.md` / CLIO) and fuses it with Rebalance's live work signal
  (ranked next actions, calendar events, Sleuth reminders, GitHub activity) and device-wide
  git state (`collect.sh`). Maintains a rolling 2-hour window in `temp/activity-rolling-window.md`
  and overlays previous summaries for narrative cohesion. Trigger on "synthesize activity",
  "what am I working on", "monitor prompts", "activity synthesis".
---

# Activity Synthesis — Prompts Log + Live Work Signal + Git Activity

Continuously synthesizes: **"What is the operator actually working on right now across all agents, repos, and systems?"**

Combines two independent primary sources with historical continuity:
1. **Multi-Agent Prompt Log** — `/Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md` (and `~/.claude/prompt-log.jsonl` / `clio_prompts` table in SQLite), capturing real-time human intent, instructions to Claude/Agy/Codex/ZCode, and agent turn handoffs.
2. **Rebalance Work Activity Signal & Git State** — Ranked next actions (`get_next_actions`), upcoming calendar events, Sleuth reminders, and device-wide git activity (`.claude/skills/rebalance/collect.sh`).
3. **Historical Continuity Overlay** — Reads the 2 preceding summaries from `temp/activity-rolling-window.md` to ensure a smooth, cohesive narrative rather than disjointed snapshots.

---

## Guardrails & Principles

- **Reuse Existing Subsystems**: Do not create parallel pipelines or bespoke ad-hoc trackers. Query the resolved SQLite database (`src/rebalance/paths.py:resolve_db()`), `get_next_actions()`, `clio_prompts`, and `.claude/skills/rebalance/collect.sh`.
- **Read-Only**: Synthesis inspects files and SQLite tables; it never mutates git state, resets branches, or alters worktrees.
- **Rolling Window Storage**: Write and maintain the rolling 2-hour window in `temp/activity-rolling-window.md` (gitignored in repo root).

---

## Procedure (Every 15 Minutes)

### Step 1 — Read Recent Multi-Agent Prompts (Intent Signal)
Inspect the top of `/Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md` (or query `clio_prompts` table in `rebalance.db`).
- Extract prompts within the current 2-hour window.
- Identify the active repositories, tools/agents (Claude, Agy, Codex, ZCode), and explicit directives (e.g. PR reviews, feature builds, hotfixes, refactors).

### Step 2 — Read Rebalance Live Work Signal (Operational Signal)
- Call `get_next_actions()` / load ranked next actions from `rebalance.db`.
- Query upcoming calendar events for today.
- Query active Sleuth reminders.

### Step 3 — Scan Device-Wide Git Activity (Code Signal)
- Execute `bash .claude/skills/rebalance/collect.sh` (or inspect recent commits from `github_commits` / `github_activity`).
- Identify repos with `ACTIVE` or `WARM` worktrees, recent commit timestamps, unmerged branches, and dirty working trees.

### Step 4 — Overlay Previous 2 Summaries (Narrative Cohesion)
- Read `temp/activity-rolling-window.md` if it exists.
- Extract the 2 most recent synthesis snapshots.
- Trace transitions: what finished, what is currently in-flight, and what emerged newly.

### Step 5 — Synthesize and Report
Structure the output clearly:
1. **Current Focus & In-Flight Efforts (Last 15–30 min)**: What is actively being built or orchestrated right now.
2. **Multi-Agent & Tool Interactions**: Which agents (Agy, Codex, Claude, ZCode) are executing which tasks across repos.
3. **Reconciled Operational Context**: How live coding matches against calendar commitments and ranked priorities.
4. **Narrative Arc (Past 2 Hours)**: Progression from earlier tasks to current state.

### Step 6 — Update Rolling Window
Append or rotate the entry in `temp/activity-rolling-window.md` keeping the last 2 hours of timestamped snapshots.
