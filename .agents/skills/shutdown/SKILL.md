---
name: shutdown
description: >-
  End-of-day repository triage, two-pass liveness detection, and next-session
  continuity handoff alongside daily. Produces a compact handoff under
  temp/daily-log/shutdown/YYYY-MM-DD/<run-id>.md and optionally delegates
  user-approved merges and cleanup to merge-cleanup.
---

# Shutdown — End-of-Day Triage & Next-Session Continuity

Own the transition from today's multi-agent development sessions to tomorrow's cold start.
Produce a trustworthy, reviewable brief of what advanced, what remains in flight, and
which concrete actions should kick off tomorrow morning.

## Core Principles & Safety Boundaries

1. **Report & Triage First**: Default is strictly report-only. No automatic commits,
   no background merges, no deletions, and no application quitting.
2. **Two-Pass Liveness Exclusion**: Compares two snapshots taken at least 30 seconds
   apart. Any repository with detected edits, ref movements, lock files, or active
   processes is flagged as **ongoing activity** and excluded from action candidates.
3. **Canonical Writer Separation**: The scanner generates evidence and sidecar JSON;
   the invoking agent synthesizes the review and handoff narrative.
4. **Durable & Atomic Persistence**: Outputs are saved under:
   `temp/daily-log/shutdown/YYYY-MM-DD/<run-id>.md`
   `temp/daily-log/shutdown/YYYY-MM-DD/<run-id>.json`
   A relative pointer `latest.md` is updated only after both files are complete.
5. **Delegated Execution Only**: If the operator chooses to execute an approved action
   (e.g. merge an open PR or clean a finished worktree), delegate strictly to
   `/merge-cleanup` by name. Never improvise a custom merge or delete script.

---

## Conversational Execution Workflow

### Step 1 — Run Two-Pass Scanner
Execute the canonical scanner in shutdown mode:
```bash
python3 .agents/skills/daily/scripts/scan_unclosed_loops.py --mode shutdown
```
- Discovers git repositories across configured roots (`temp/rbos.config` or standard dev folders).
- Performs Snapshot A, waits $\ge 30\text{s}$, performs Snapshot B.
- Gathers staged/unstaged/untracked files, local branch tips, unpushed commits, and open PRs.
- Emits structured JSON to stdout.

### Step 2 — Synthesize Context & Read Continuity History
1. **Read Previous Handoff**: Inspect `temp/daily-log/shutdown/latest.md` (if present)
   to carry forward any previously recorded deliberate deferrals or open blockers.
2. **Inspect Today's Log**: Read `temp/daily-log/YYYY-MM-DD.log` to incorporate recent
   trajectory and completed phases.
3. **Optional Rebalance DB Enrichment**: If `rebalance.db` is present, read-only
   queries can enrich author-scoped commits and project registry metadata without
   altering the database. If absent or locked, proceed in basic mode without degradation.

### Step 3 — Present End-of-Day Triage (First Screen)
Format the output for the operator using this structure:

```markdown
# 🌙 End-of-Day Shutdown Brief — [YYYY-MM-DD HH:MM TZ]

## 🚀 What Advanced Today
- **[Project / Repo]**: Summary of completed commits, PRs opened/merged, and milestones advanced.

## 🧭 Project Arcs & Remaining Phases
- **[Project A]**: Phase N in progress (PR #X open: [Title]). Next: Phase N+1.
- **[Project B]**: All PRs merged. Remaining arc: [Documentation / QA].

## ⏳ Pending Pull Requests & Proposed Merge Order
1. `repo#123` — [Title] (Checks passing, ready for review/merge)
2. `repo#124` — [Title] (Depends on #123)

## ⏸️ Deliberate Deferrals & Held PRs
- `repo#99`: Held for morning dogfooding (`[Reason: ...]`).

## 🛑 Ongoing Activity Exclusions (Excluded from actions)
- `repo-active`: Excluded (`[Reason: Active edits in pass B / lock detected]`).

## 🌅 Tomorrow Morning Nudges (Top 1–3 Focus Items)
1. **[Top Priority]**: [Exact command or prompt to start next session]
2. **[Secondary]**: [Follow-up verification or review step]
```

### Step 4 — Persist Handoff Artifact
1. Generate unique run ID: `HHMMSS` (e.g. `201500`).
2. Write markdown brief to `temp/daily-log/shutdown/YYYY-MM-DD/<run-id>.md`.
3. Write scanner JSON payload to `temp/daily-log/shutdown/YYYY-MM-DD/<run-id>.json`.
4. Update `temp/daily-log/shutdown/latest.md` pointing to `<run-id>.md`.

### Step 5 — Optional Scoped Execution (Explicit Consent Only)
Ask the operator if they wish to perform any specific, approved actions:
- If operator asks to merge an open, passing PR or tear down a clean clone:
  Invoke `/merge-cleanup` with the targeted repos/PRs.
- If operator does not request execution, conclude report-only.
