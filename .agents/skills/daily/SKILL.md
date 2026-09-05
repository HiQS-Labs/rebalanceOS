---
name: daily
description: >
  15-minute multi-source daily work synthesizer. Monitors the operator's multi-agent
  prompt log (`0. Claude Prompts.md` / CLIO) and fuses it with Rebalance's live work signal
  (ranked next actions, calendar events, Sleuth reminders, Apple Reminders, GitHub activity)
  and device-wide git state (`collect.sh`). Appends 15-minute syntheses into deterministic daily logs at
  `temp/daily-log/YYYY-MM-DD.log`, evaluating trajectory, velocity, and adaptive coaching over the rolling
  2-hour window. Trigger on "/daily", "daily", "what am I working on", "synthesize activity",
  "daily log", "monitor prompts".
---

# Daily — Live Prompts Log + Work Signal + Git Telemetry

Continuously answers: **"What is the operator actually working on right now across all agents, repos, and systems, what is the trajectory/velocity of their work, and what actionable coaching maintains forward momentum?"**

Combines multi-source operational telemetry with temporal trajectory analysis, deterministic cadence gates, and data-grounded adaptive coaching:
1. **Multi-Agent Prompt Log** — `/Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md` (and `~/.claude/prompt-log.jsonl` / `clio_prompts` table in SQLite), capturing real-time human intent, instructions to Claude/Agy/Codex/ZCode, and agent turn handoffs.
2. **Rebalance Work Activity Signal & Git State** — Ranked next actions (`get_next_actions`), upcoming calendar events (`calendar_events`), Sleuth task reminders (`sleuth_reminders`), macOS Apple Reminders read-only snapshots (`src/rebalance/ingest/apple_reminders.py`), and device-wide git activity (`.claude/skills/rebalance/collect.sh`).
3. **Daily Log & Trajectory Analysis** — Maintains deterministic daily logs in `temp/daily-log/YYYY-MM-DD.log`. Inspects the preceding **2-hour window** to derive **velocity** (rate of completions/commits) and **trajectory** (shifts in focus, momentum, bottlenecks).
4. **Adaptive Coaching & Guidance** — Generates falsifiable, signal-grounded coaching nudges citing specific triggering metrics (flow reinforcement, context-switching alerts, pacing/break reminders, and friction escape hatches).
5. **Cadenced Horizons (Exactly-Once Morning Retro & Monday Outlook)** — Produces a 2–3 sentence retrospective on yesterday's achievements on the day's first synthesis entry, and a 5-day horizon forecast on Monday's first synthesis entry.

---

## Guardrails & Principles

- **Reuse Existing Subsystems**: Do not create parallel pipelines or bespoke ad-hoc trackers. Query the resolved SQLite database (`src/rebalance/paths.py:resolve_db()`), `get_next_actions()`, `clio_prompts`, `calendar_events`, `sleuth_reminders`, Apple Reminders snapshots, and `.claude/skills/rebalance/collect.sh`.
- **Read-Only Against Repositories & External Stores**: Synthesis inspects files and SQLite tables; it never mutates git state, resets branches, alters worktrees, or writes to external stores. Apple Reminders access uses the read-only Core Data snapshot extractor with graceful degradation.
- **Deterministic Daily Logging**: Output records append to `temp/daily-log/YYYY-MM-DD.log` (gitignored under `temp/`) matching the fixed log-entry schema.

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
- **macOS Apple Reminders Snapshot**:
  - Invoke the read-only snapshot extractor (`src/rebalance/ingest/apple_reminders.py:extract_apple_reminders`).
  - Filter to incomplete items (`is_completed == False`).
  - Graceful degradation: If running on non-macOS or if TCC/permissions are unavailable, log a warning and proceed without failing the cycle.

### Step 3 — Scan Device-Wide Git Activity (Code Signal)
- Execute `bash .claude/skills/rebalance/collect.sh` (or inspect recent commits from `github_commits` / `github_activity`).
- Identify repos with `ACTIVE` or `WARM` worktrees, recent commit timestamps, unmerged branches, and dirty working trees.

### Step 4 — Evaluate 2-Hour Trajectory, Velocity & Cadenced Horizons

1. **2-Hour Rolling Window Analysis**:
   - Read `temp/daily-log/YYYY-MM-DD.log`.
   - **Trajectory**: Direction of focus across repos, projects, and domains.
   - **Velocity**: Rate of task completions, commit cadence, multi-agent handoff speed, resolution of blockers.
   - **Momentum**: Accelerating vs decelerating workstreams, impending context switches (calendar events, deadlines).

2. **Time-Gated Horizons (Exactly-Once Semantics)**:
   - **Local Timezone**: Evaluate against the operator's configured local timezone (e.g. `America/Los_Angeles` / PDT/PST).
   - **🌅 Morning Retrospective (Yesterday's Arc)**:
     - *Predicate*: Generated on the **first synthesis cycle written to `temp/daily-log/YYYY-MM-DD.log` for the day** (check if `🌅 Yesterday's Arc` is already present in today's log; if absent, generate it).
     - *Action*: Inspect `temp/daily-log/YYYY-MM-[yesterday].log` and summarize yesterday's landed commits, PRs, and finished arcs in 2–3 crisp sentences.
   - **📅 Monday Weekly Horizon**:
     - *Predicate*: Generated on the **first synthesis cycle written on Mondays** (`local_time.weekday() == 0`, check if `📅 Weekly Operational Horizon` is already present in today's log; if absent, generate it).
     - *Action*: Evaluate upcoming 5-day calendar (`calendar_events` Monday–Friday) and top-ranked next actions to outline key weekly milestones, meeting load distribution, and deep work runways.

3. **Adaptive Coaching & Focus Guidance (Falsifiable Predicates)**:
   Evaluate the rolling window against these four trigger rules. Every emitted coaching nudge **must explicitly cite the trigger** (e.g., `[Trigger: ...]`) to remain falsifiable:
   - **Flow State & Momentum Reinforcement**:
     - *Trigger*: $\ge 2$ consecutive 15m cycles with prompts/commits concentrated on a single repository without context-switching.
     - *Nudge*: Reinforce flow state; advise protecting the deep-work block until the current unit of work/PR is landed.
     - *Citation*: `[Trigger: N cycles focused on <repo>]`
   - **Context-Switching & Fragmentation Alert**:
     - *Trigger*: $\ge 3$ distinct repositories touched within the last 45 minutes ($T-3$ cycles).
     - *Nudge*: Warn of attention fragmentation; recommend parking secondary tasks and landing active WIP on the primary repository first.
     - *Citation*: `[Trigger: 3 repos touched in 45m: <repo1>, <repo2>, <repo3>]`
   - **Pacing & Recovery Reminders**:
     - *Trigger*: $\ge 8$ consecutive active cycles ($\ge 120\text{m}$) without an idle cycle, OR an external calendar meeting is $T-15\text{m}$ away.
     - *Nudge*: Encourage a 5-minute hydration/movement break or transition buffer before the next calendar milestone.
     - *Citation*: `[Trigger: 120m continuous execution | Meeting T-15m: <event_title>]`
   - **Friction & Blocker Escape Hatch**:
     - *Trigger*: $\ge 2$ consecutive cycles reporting test failure, error traces, or unmerged blocked state on the same task.
     - *Nudge*: Recommend dropping down to Rung 1 (`/debug-mantra`) to re-verify ground truth or invoking a quick `/consult` before further churn.
     - *Citation*: `[Trigger: Stalled task <task_id> for N cycles]`

---

### Step 5 — Synthesize and Report (Deterministic Schema)

Format the synthesis matching this exact Markdown template:

```markdown
## [YYYY-MM-DD HH:MM TZ] — Synthesis (Cycle N)
[If First Cycle of Day]
- **🌅 Yesterday's Arc**: <2-3 sentences summarizing yesterday's achievements from previous log>

[If First Cycle of Monday]
- **📅 Weekly Operational Horizon**: <5-day outlook: key milestones, meeting load, and deep work runway>

- **Focus**: <1-2 sentences on what is actively being built or orchestrated right now across agents>
- **Trajectory (2-Hour Window: HH:MM – HH:MM TZ)**:
  - <Bullet 1: momentum, completed arcs, and direction of focus across repos>
  - <Bullet 2: swarm state across tools/agents (Claude, Agy, Codex, ZCode)>
- **Velocity**: <Nominal / High / Very High — with brief quantitative basis (e.g. commits/PRs/phases completed)>
- **Operational Horizon**: <Reconciled next 1–2 hours: upcoming calendar commitments + ranked Sleuth & Apple Reminders priorities>
- **Coaching Nudge**: <1-2 sentences of actionable guidance> `[Trigger: <telemetry_metric>]`
```

---

### Step 6 — Append to Daily Log

Append the formatted synthesis entry into `temp/daily-log/YYYY-MM-DD.log` (create file with `# Daily Activity Log — YYYY-MM-DD` header if starting a new day).
