# Recon Map — GH-210 Daily work synthesis canary

Commit: `f3b91df` · Mode: graph+read (graph lead from the older `rebalanceOS` checkout, confirmed in this branch) · Lanes: A–D serially

## Subject and change class

Add an opt-in, every-15-minute Terra Low canary around the established `/daily`
contract. This is a cross-module operational change: it adds one constrained model
boundary and one scheduled job, while preserving the existing collectors and the
separate 18:20 vault publisher.

## The seams — where a change here escapes this file

| Seam | Location | Crosses | Breaks if |
|---|---|---|---|
| Daily output contract | `.agents/skills/daily/SKILL.md` | Agent skill → daily log | Required sections, cadence gates, or single-writer append semantics drift |
| Scheduler manifest | `SCHEDULER.md` | Docs → `stack.sh`, doctor, policy tests | A malformed table row silently removes a managed job |
| Runtime installer | `scripts/lib/install_common.sh` | Source checkout → rendered launchd plist | The job binds to the wrong checkout or TCC-safe wrapper path |
| Ranked work signal | `src/rebalance/ingest/next_actions.py:1596` | SQLite cache → synthesis packet | The canary recomputes/reranks instead of reading the persisted verdict |
| Calendar/reminders | `src/rebalance/ingest/calendar.py:448`, `src/rebalance/ingest/sleuth_grouping.py:322`, `src/rebalance/ingest/apple_reminders.py:907` | Existing read APIs → synthesis packet | New direct SQL or a second collector becomes authoritative |
| Device work state | `.agents/skills/daily/scripts/scan_unclosed_loops.py` | Repository fleet → compact counts | The canary mutates repos or trusts an empty scan |
| Model boundary | `codex exec` | Minimized private packet → OpenAI | Tools, repository access, malformed output, missing usage, or budget overrun fail open |

## Call paths in

`launchd StartInterval` → `utils/job_guard.py` →
`scripts/daily_work_synthesis.sh` → `utils/daily_work_synthesis.py` → existing
read APIs/scanners → isolated `codex exec` → local validator → deterministic renderer
→ `temp/daily-log/YYYY-MM-DD.log`.

Manual canary uses the same wrapper, bypassing only launchd.

## State

- Authoritative inputs remain the existing Rebalance database, CLIO prompt rows,
  repository scanner, and CPU scanner.
- The single user-facing writer is the new runner's locked append to the established
  gitignored daily log.
- Mutable canary-only state is gitignored: config, sanitized usage receipts, and the
  CPU scanner snapshot. No model output is written before validation.

## Contracts

- `Daily Markdown v1` — user/skill consumer — breaking if established sections or
  exactly-once cycle numbering disappear — `.agents/skills/daily/SKILL.md`.
- `Scheduler policy table` — stack/doctor/tests — breaking if cadence, wrapper, label,
  installer, or runtime limit disagree — `SCHEDULER.md`.
- `Terra structured result v1` — validator/renderer — breaking if required fields or
  evidence IDs cannot be validated — owned by the canary runner/schema.
- `Canary config v1` — local operator/runtime — default-off; contains model, effort,
  timeout, call/token/cost ceilings, and kill switch.

## Build, failure and rollback today

The task worktree has no independent virtualenv, so the system interpreter could not
collect the suite (42 missing-dependency errors). Re-running from this worktree with the
neighboring development checkout's complete virtualenv passed the full repository
suite. Model/auth/schema capability is recorded under
`TESTS-RESULTS/2026-09-12+GH-210/`.

Failures must append a receipt but not a Daily entry. Three consecutive failures,
missing usage, a token ceiling breach, or the daily call/cost ceiling stops subsequent
calls. Rollback is setting `enabled=false` in the local config or unloading the one
launchd label; the incumbent 18:20 publisher is untouched.

## Unknowns

| Unknown | Why it matters | What would settle it |
|---|---|---|
| Real-world usefulness versus the deterministic/direct controls | Synthetic capability is not product evidence | Frozen blinded historical evaluation plus operator ratings |
| Actual billed cost under Codex entitlement | CLI exposes tokens, not invoice cost | Provider billing export; until then report dated list-price estimates |
| Sleep/wake catch-up behavior across several missed intervals | May create an unwanted burst | Observe a real wake transition during the bounded canary |

## Current-state radius, one line

One Mac Studio launchd job, one minimized private outbound packet per accepted cycle,
the gitignored Daily log/receipts, and the operator reading its coaching; no repository,
database, vault, Slack, or GitHub write path changes.
