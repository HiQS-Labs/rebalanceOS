---
gh_issue: 211
source: https://github.com/HiQS-Labs/rebalanceOS/issues/211
title: Mac Studio bounded runtime recovery
status: In progress
owner: Mac Studio runtime recovery arm
created: 2026-09-12
updated: 2026-09-12
goal: Restore bounded, fresh scheduled operation before beginning GH-210.
doc_type: bugfix
effort: 4
complexity: 4
risk: 3
phases: 4
reversibility: Costly — runtime and database recovery touch shared operational state; code remains revertible.
---

# GH-211 — Mac Studio bounded runtime recovery

| Most recently completed phase | What's next |
| --- | --- |
| Phase 0: incident reproduction and Recon Map | Phase 1: executable timeout and health contracts |

## Table of contents

- [Phase 1: Executable timeout and health contracts](#phase-1-executable-timeout-and-health-contracts)
- [Phase 2: Bounded scheduler implementation](#phase-2-bounded-scheduler-implementation)
- [Phase 3: Recover persisted state](#phase-3-recover-persisted-state)
- [Phase 4: QA, PR, and deployment](#phase-4-qa-pr-and-deployment)

The grounded trace is [recon-bounded-runtime.md](GH-211-MAC-STUDIO-RUNTIME-RECOVERY/recon-bounded-runtime.md).
Execution uses the debug-mantra protocol. Ratings are `rated 95/90/50/30`.

## Bet, scope, and safety

The bet is that overlapping, unbounded scheduled jobs—not one corrupt lockfile—created the runaway
runtime. The lean fix extends the existing stdlib guard and policy seams; it adds no daemon, queue,
dependency, heartbeat stream, or 3-Eyes ownership. Whole-job bounds, stale-output health, targeted
semantic repair, and truthful Git publication are in scope. Collector optimization is deferred.

Code changes are Easy to revert. Stopping jobs and repairing projections is Costly: the shield is a
fleet stop plus verified DB/Git backups; the tripwire is any live DB holder, failed exclusive
transaction, unpreserved Git change, failed test, or stale post-deploy artifact. A tripwire stops
the phase before later mutation.

## Phase 1: Executable timeout and health contracts

**Goal:** Red tests demonstrate that overlong jobs and stale pulse artifacts cannot remain green.

- [ ] Derive conservative per-job maximum runtimes from non-empty lifecycle history and record the
  values in `SCHEDULER.md`; finite jobs have positive ceilings and the server has none.
- [ ] Add a red-control test proving `run_guarded` fails to terminate a child tree at its deadline.
- [ ] Add hermetic red controls proving stack/doctor label an over-age live job healthy and pulse
  health accepts an expired artifact.
- [ ] Add red controls for matching dirty Git content that is not committed and targeted semantic
  orphan repair dry-run/apply behavior.

### Phase 1 — QA checklist

- [ ] Every test was witnessed red against the unmodified production path.
- [ ] Fixtures are non-empty and launchctl/Git/SQLite effects remain hermetic.
- [ ] Each retry and process-reap loop has a finite attempt or time bound.
- [ ] Status table and `updated:` date refreshed.

## Phase 2: Bounded scheduler implementation

**Goal:** Every finite scheduled batch has one existing-guard deadline and truthful terminal health.

- [ ] Extend `utils/job_guard.py` with an optional positive wall-clock limit using its current child
  process group and TERM/KILL path; emit a distinct timeout reason and preserve existing exit codes.
- [ ] Add one shared scheduler helper and wire finite managed wrappers through the guard. Keep
  3-Eyes untouched.
- [ ] Extend the policy parser and tests with maximum runtime; make stack and doctor report an
  over-age live PID as unhealthy rather than RUNNING/OK.
- [ ] Make pulse health non-healthy/503 when the generated artifact exceeds its documented age.
- [ ] Make shared-Git publication verify tracked/staged/HEAD state before returning unchanged and
  serialize in-repo publishers with an advisory lock without changing schemas.
- [ ] Add a supported semantic-orphan command with read-only default, explicit apply, transaction,
  counts, and audit output.

### Phase 2 — QA checklist

- [ ] Focused tests run and pass; each assertion has Phase 1 red-control evidence.
- [ ] Timeout logs name job, limit, child PID/group, and reason without polling heartbeats.
- [ ] No new dependency, supervisor, database writer, or published schema exists.
- [ ] Version is bumped PATCH in both owners and a dated changelog entry names #211.
- [ ] Status table and `updated:` date refreshed.

## Phase 3: Recover persisted state

**Goal:** No over-age holders remain, the database is exclusively writable, and shared Git work is
preserved and publishable.

- [ ] Re-run process, child-tree, progress, DB/WAL, Git-process, and index-lock ownership probes;
  capture non-empty evidence under `TESTS-RESULTS/2026-09-12+GH-211/`.
- [ ] Stop the managed stack through `stack.sh down`, verify descendants exited, and ignore inert
  job-guard lockfile contents as ownership evidence.
- [ ] Create and verify a DB backup, checkpoint WAL, prove an exclusive transaction, sample orphan
  IDs, run supported repair dry-run then apply, and prove zero orphans without unexpected backlog.
- [ ] Preserve tracked, staged, untracked, ref, and lock evidence from the shared Git checkout. Move
  the proven-ownerless lock aside, reconcile without reset/tree-wide stash, then verify remote data.

### Phase 3 — QA checklist

- [ ] Every material mutation names its backup and restoration command in the campaign report.
- [ ] DB integrity, checkpoint, exclusive transaction, orphan count, and Git remote checks ran.
- [ ] No unique runtime or shared-checkout work was discarded.
- [ ] Any tripwire stopped the phase before later mutation.
- [ ] Status table and `updated:` date refreshed.

## Phase 4: QA, PR, and deployment

**Goal:** CI-equivalent proof, independent relay approval, merged code, and a fresh stable runtime.

- [ ] Run format/lint/type gates, `pytest tests/`, doctor, PDDA, and relevant shell tests; publish
  non-empty outputs in the GH-211 campaign directory.
- [ ] Run Codex relay final QA with an empty reviewer allowlist; cap at four productive rounds and
  stop if two consecutive rounds add no qualifying improvement.
- [ ] Push, open the PR with evidence/rollback, wait for checks, merge to `development`, and verify
  the remote merge commit.
- [ ] Fast-forward the declared runtime, refresh its editable install, reinstall bounded plists,
  start only safe jobs initially, then bring up the fleet after DB/Git tripwires stay green.
- [ ] Prove current drift, fresh pulse health, no GH-211 doctor errors, and bounded job outcomes over
  two observations.
- [ ] Comment #211 with evidence, then create the fresh GH-210 branch from updated development and
  begin its Phase 0 spike.

### Phase 4 — QA checklist

- [ ] Artifacts are non-empty, commit-stamped, and distinguish observed from predicted.
- [ ] Independent QA approves and required GitHub checks are green.
- [ ] Deployment is a runtime fast-forward; rollback is a revert PR plus forward deployment.
- [ ] Pulse freshness and doctor/stack status close the user/operator loop.
- [ ] Status table and `updated:` date refreshed before #211 is shipped.

