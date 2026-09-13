---
gh_issue: 215
source: https://github.com/HiQS-Labs/rebalanceOS/issues/215
title: "Guarded jobs that self-report lifecycle events log a second start/terminal pair"
status: "Active — fix in flight on fix/gh215-lifecycle-double-log"
created: 2026-09-12
updated: 2026-09-12
owner: noel
doc_type: bugfix
goal: >
  Restore the GH-211 single-lifecycle-pair contract: a guarded scheduled job records exactly one
  job_started/terminal pair, even when its Python entry point also self-reports lifecycle events.
effort: 2
complexity: 1
risk: 2
phases: 1
ratings_provisional: true
roadmap_exempt: false
---

# GH-215 — Guarded jobs that self-report lifecycle events log a second start/terminal pair

## Status

| What was just completed | What's next |
|---|---|
| Issue captured with live before/after evidence from the Mac Studio runtime; defect confirmed as a gap in PR #212's lifecycle-ownership contract. | Central suppression in `auth_log`, red-control test, full suite, final relay QA, PR. |

## Problem

PR #212 made the outer job guard (`utils/job_guard.py --lifecycle-job`) the single owner of each
scheduled job's lifecycle telemetry, and suppressed the bash wrappers' own emission via
`REBALANCE_SCHEDULER_LIFECYCLE_CHILD=1` (checked only in `scripts/lib/scheduler_common.sh`'s
`rb_job_init`). Two Python entry points never source that shell library and self-report their own
lifecycle events directly:

- `utils/daily_synthesis.py:72-92` (`log_job_started/completed/failed` for `daily-synthesis`)
- `utils/obsidian_daily_rollover.py:41-56` (same for `obsidian-rollover`)

Since the #212 deploy (`8a5df5c`), every `daily-synthesis` fire records **two** pairs. Observed
live in the runtime's `temp/logs/auth_activity.jsonl` at 2026-09-13T01:20 UTC: two `job_started`
events 111 ms apart, two `job_completed` (elapsed 22.76 s / 22.95 s). Pre-deploy runs at the same
fire time show one pair. `obsidian-rollover` had not fired post-deploy at intake; it will
double-log at its next 00:40 run.

## Impact

Duplicate rows in `auth_activity.jsonl`, the `/auth-log` dashboard, and any per-job event counts.
Both pairs agree on outcome, so no liveness/health verdict flips. Contract violation
(SCHEDULER.md: "The guard owns the one lifecycle start/terminal pair"), not a correctness bug in
the jobs themselves.

## Fix direction

The guard sets `REBALANCE_SCHEDULER_LIFECYCLE_CHILD=1` only in the **child** env; its own
`auth_log` calls run in the parent without the variable. Suppressing the lifecycle writers
centrally in `rebalance/ingest/auth_log.py` when that env var is set therefore:

- covers both current self-reporters and any future Python self-reporter (no per-script opt-in),
- leaves guard-side events untouched (parent process, variable absent),
- keeps guard ownership strictly stronger — the guard reports wall-clock timeouts (exit 124),
  ceiling trips, and evictions that a reaped child cannot report for itself.

The bash-side suppression in `scheduler_common.sh` stays (same env var, same contract).

## Acceptance

- [ ] Red control first: a test that fails on today's code (double pair under the guard) and
      passes after the fix.
- [ ] Guarded `daily-synthesis`-shaped run records exactly one pair.
- [ ] Manual (unguarded) invocation still records the self-reported pair.
- [ ] Guard outcomes unchanged: timeout/ceiling/eviction still `job_failed` with the right `reason`.
- [ ] Full `pytest tests/` green; `rebalance doctor` unaffected.

## Rating

`rated 50/40/50/85` — telemetry-pollution defect in the just-shipped incident fix (sev 40: no
wrong verdicts, no data loss); recurrence confirmed nightly since deploy, operator scheduled it
immediately (pri 50); appeal neutral (50); central suppression plus one red-control test
(effort 85). Provisional until post-fix verification.
