---
gh_issue: 236
source: https://github.com/HiQS-Labs/rebalanceOS/issues/236
title: "Diagnose a broken runtime virtualenv across the scheduler fleet"
status: "Implementation complete — final Codex QA pending"
created: 2026-09-21
updated: 2026-09-21
owner: Codex
doc_type: bugfix
goal: >
  Make doctor and stack status identify a missing or dangling runtime virtualenv
  interpreter as the shared cause of fleet-wide launchd EX_CONFIG failures.
effort: 2
complexity: 2
risk: 2
phases: 1
---

# GH-236 — runtime virtualenv diagnostics

## Status

| What was just completed | What's next |
|---|---|
| Plan approved by Codex relay; implementation and focused verification complete. | Commit the candidate, run final Codex QA, then execute the final repo gates and open the PR. |

## Bug

A Homebrew Python patch upgrade can leave the declared runtime checkout's
`.venv/bin/python` symlink chain pointing at a removed Cellar interpreter. launchd
then exits every interpreter-backed scheduler job with status 78 before the job
wrapper can write a current log. `stack.sh verify` identifies the missing executable,
but `stack.sh status` and `rebalance doctor` currently present only opaque per-job
failures and a kickstart remedy that cannot repair the interpreter.

## Acceptance

- `rebalance doctor` emits one fleet-level failure when installed Rebalance plists
  reference the declared runtime interpreter and it is missing, non-executable, or a
  dangling symlink; the finding names the affected-job count and explicit repair flow.
- Per-job nonzero-exit hints direct operators through `stack.sh verify` before logs or
  kickstart, so status 78 no longer implies kickstart alone is sufficient.
- `stack.sh status` prints the same root-cause warning and points to `stack.sh verify`.
- Hermetic tests cover a healthy executable, an absent path, and a dangling symlink.
- Diagnosis stays read-only; the product does not delete or recreate a virtualenv.

## Assessment

Rated 90/90/50/80 (priority/severity/neutral appeal/cheapness). The confirmed incident
disabled 12 of 13 managed jobs and left indexed sources five days stale, while the
repair is localized to existing doctor and stack diagnostics. One incident is proven;
there is not enough same-root-cause history to claim an increasing recurrence trend.

## Recon map

The declared runtime root comes from `~/.config/rebalance/runtime-root` through
`_expected_runtime_root()`. Scheduler installers render that checkout's
`.venv/bin/python` into installed `com.rebalance-os.*.plist` files. `run_doctor()`
already takes one launchctl snapshot, reports per-job exits in `_check_launchd()`, and
checks those same installed plists for checkout drift in
`_check_scheduled_stack_checkout()`. The latter is the nearest existing fleet-level
configuration seam. `scripts/stack.sh` resolves the same runtime root through
`scripts/lib/install_common.sh`; `validate_environment()` already owns the exact
interpreter preflight and repair command, while `stack_status()` omits it.

Failure path: launchd resolves `ProgramArguments[0]` before `job_guard.py` or a wrapper
starts. A dangling interpreter therefore produces EX_CONFIG 78 with no current job
log. Re-running or kickstarting cannot cross that boundary. Interactive `doctor` can
still diagnose the declared runtime from another healthy checkout; `stack.sh status`
runs under bash and remains available in the broken checkout.

Prior art is extended, not duplicated: the public fix reuses `_expected_runtime_root`,
the installed plist inventory, `validate_environment`, and existing stack tests. GH-132
checks a PATH console-script shebang and cannot see launchd's separately rendered
runtime interpreter. 3-Eyes is deferred and is not reactivated for this repair.

Graph note: the available index generation predates current `development`, and
`scripts/` is excluded. Direct source reads cover the material Python and shell seams.

## Phase 1 — surgical diagnosis

1. Add a read-only doctor check beside the existing scheduler-checkout check. Parse
   installed Rebalance plists, count only jobs that reference the declared runtime's
   `.venv/bin/python`, and validate that executable's path, resolved target, regular-file
   type, and execute bit. Use standard-library structured plist parsing; an unreadable or
   malformed installed Rebalance plist emits an explicit unknown/WARN and is excluded from
   the affected count, never converted into a healthy claim. Emit one fleet-level error
   with the count and an explicit `cd <declared-runtime-root>` (safely quoted) before the
   rebuild → `bash scripts/stack.sh verify` → reload flow, so doctor invoked from a dev
   checkout cannot repair the wrong venv. Healthy matching jobs produce one quiet OK; no
   installed interpreter-backed jobs produce no health claim.
2. Change the generic nonzero launchd hint to run `bash scripts/stack.sh verify` first,
   then inspect logs and kickstart only after preflight succeeds. Preserve exit grading,
   daily-sync's richer result, crash-loop state, and every launchctl predicate.
3. Add one read-only `stack_status()` preamble using the same `-x` predicate already
   owned by `validate_environment()`. On failure, name the interpreter and direct the
   operator to `bash scripts/stack.sh verify`; leave status exit behavior unchanged.
4. Add hermetic tests for a healthy executable, absent interpreter, dangling symlink,
   non-executable regular file, executable directory, malformed installed plist, exact
   affected-job count when one plist repeats the interpreter argument, zero matching jobs,
   unrelated/foreign plist exclusion, distinct current/declared roots in remediation, the
   revised exit hint, and stack-status output. Witness red by running the new regression
   cases against the baseline before implementation.
5. Run focused doctor/stack tests during implementation. After final relay approval,
   run the repo-required `rebalance doctor`, `pytest tests/`, and deterministic PDDA
   checks once against the final commit; disclose unrelated baseline failures.

## Boundaries and rollback

Easy / risk 2: the change is additive diagnosis plus remediation wording. Rollback is
one commit revert; it neither mutates installed plists nor changes scheduler state.

Non-goals: automatic virtualenv deletion/recreation, Python pinning, Homebrew lifecycle
management, scheduler installation, 3-Eyes activation, runtime deployment, suppression
of truthful per-job failures, or changes to launchd status semantics.

## Verification

- Witnessed red: the new doctor test module failed collection because the fleet-level
  interpreter check did not exist on baseline; no implementation tests could pass vacuously.
- Focused after final-review remediation: 63 doctor/launchd/stack/scheduler/version tests passed.
- Relevant suite: 179 doctor, scheduler-policy, and stack tests plus 19 subtests passed.
- Ruff passed on every changed Python file.
- Pre-implementation Codex relay approved the revised plan in round 2. Final implementation
  review found and drove two corrections: count validated unique launchd labels rather than plist
  filenames, and control interpreter health explicitly in stack-status tests. Re-review and
  repo-wide gates remain pending.
