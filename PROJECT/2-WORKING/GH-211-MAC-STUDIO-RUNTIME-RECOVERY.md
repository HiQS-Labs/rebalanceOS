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

### Runtime policy matrix

Limits are conservative first-release ceilings derived from non-empty completed-run history through
2026-09-12, not performance targets. Enforcement for every finite job is the existing
`utils/job_guard.py` CLI placed at the outer plist `ProgramArguments` boundary, before the current
wrapper or Python command. Live-process health age comes from the launchd PID's OS start time; the
lifecycle log records the terminal result. `none` is the only sentinel and is valid only for the
daemon. Tests reject missing, duplicate, zero, negative, non-integer, or other sentinel values.

| Job | Max runtime | Evidence / policy reason |
| --- | ---: | --- |
| daily-sync | 10,800 s | completed runs reached 6,737 s; incident runs reached 57,278 s |
| obsidian-vault-embeddings | 7,200 s | completed runs reached 2,871 s before multi-hour incidents |
| github-sync | 7,200 s | completed runs reached 5,869 s before 9-hour incidents |
| pulse-sync | 1,800 s | ordinary runs are minutes; multi-hour failures are not useful work |
| pulse-web-sync | 7,200 s | completed pressure runs reached 4,010 s; day-long runs are stale |
| pulse-server | none | intentional KeepAlive daemon; artifact freshness is its health contract |
| pulse-warning-watch | 300 s | one bounded loopback probe |
| health-check | 900 s | deterministic doctor/report pass; doctor subprocesses are bounded |
| health-check-triage | 1,800 s | bounded doctor plus at most five model triages |
| obsidian-rollover | 300 s | recorded completions are sub-second |
| hiqs-digest | 14,400 s | a completed pressure run reached 9,167 s; incident ran about 7 hours |
| daily-synthesis | 900 s | recorded completions are under 23 s |

Timeout is exit `124`, distinct from conflict `3`, resource ceiling `4`, preflight defer `75`,
eviction `143`, and child exits. In scheduled mode the outer guard is the single lifecycle writer:
it records one `job_started`, suppresses the inner wrapper trap through a child-only environment
flag, and records one terminal event. This gives Python-direct and wrapper jobs the same contract.
Timeout produces `job_failed` with `exit_code=124` and `reason=wall_clock_timeout`; stack and doctor
classify terminal 124 or a live PID older than policy as unhealthy. Tests pin exactly one start and
one terminal event for both wrapper and Python-direct timeout cases, plus both presentations.

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
  process group and TERM/KILL path; emit a distinct timeout reason, preserve existing exit codes,
  and add scheduled-mode lifecycle ownership while `scheduler_common.sh` honors the child-only
  suppression flag.
- [ ] Route every finite managed plist through the existing job-guard CLI using the matrix above;
  keep the current wrapper/Python commands behind it and keep 3-Eyes untouched.
- [ ] Extend the policy parser and tests with maximum runtime; make stack and doctor report an
  over-age live PID as unhealthy rather than RUNNING/OK.
- [ ] Make pulse health non-healthy/503 using this precedence: overnight grace accepts the final
  scheduled artifact through exactly 06:53 local; after 06:53 and through 23:59, an artifact is
  healthy through exactly 90 minutes old; otherwise it is stale. Test immediately before, at, and
  after 06:53 plus the 90-minute boundary.
- [ ] Route pulse, snapshot, HiQS digest, and daily-synthesis publication through one shared Git
  helper and advisory lock spanning content write through verified push. Conflict defers without
  writing. Verify dirty-identical, staged, divergent HEAD, concurrent writer, push failure, and
  remote-content cases. The external `com.user.git-pulse` collector remains separately owned and
  receives recovery-only handling, not a code change in this issue.
- [ ] Add semantic-orphan maintenance through the semantic CLI/stage owner with read-only default,
  `--apply --confirm`, transaction, counts, and audit output. Above 1,000 rows it refuses unless an
  additional `--confirm-large` is present; tests cover audit content and transaction rollback.

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
- [ ] After stack-down, prove no DB/WAL holders and `BEGIN EXCLUSIVE; COMMIT`, run
  `PRAGMA wal_checkpoint(TRUNCATE)` as a phase-stopping tripwire, then create a WAL-safe backup with
  SQLite `.backup`, verify the backup's `PRAGMA integrity_check`, and record the exact restore
  command (`sqlite3 <live-db> ".restore '<backup-db>'"`). Sample orphan IDs, run dry-run, then
  `--apply --confirm --confirm-large`, and prove zero orphans without unexpected backlog.
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

- [ ] Run `ruff check .`, `ruff format --check .`, `mypy src/`, banned-import/doc/frontdoor/PDDA
  checks, the root suite under Python 3.12 and 3.13 excluding only the two CI-declared embedding
  seam files, those two seam tests with embeddings installed, and `HiQS/tests/`. Keep the explicitly
  stood-down `utils/3-eyes/tests` excluded. Separately capture non-empty focused guard,
  scheduler-policy, stack/doctor, pulse-health, Git-publication, and semantic-repair outputs.
- [ ] Run Codex relay final QA with an empty reviewer allowlist; cap at four productive rounds and
  stop if two consecutive rounds add no qualifying improvement.
- [ ] Push, open the PR with evidence/rollback, wait for checks, merge to `development`, and verify
  the remote merge commit.
- [ ] Keep the fleet down while fast-forwarding the declared runtime and refreshing its editable
  install. Install/load only `pulse-server` and observe loopback semantics; next install/load only
  `pulse-warning-watch`; after DB tripwires pass, install/load `pulse-web-sync` and deliberately
  trigger it with `launchctl kickstart -k gui/$UID/com.rebalance-os.pulse-web-sync`. Only after those
  checks install/load the remaining finite jobs one at a time, with `daily-sync` last because its
  installer fires RunAtLoad. Do not use fleet-wide `stack.sh up` until every bounded plist is loaded
  and observed. If existing installers cannot preserve this order, implement and test a
  render-without-load mode that never bootstraps an unselected label.
- [ ] Prove current drift, fresh pulse health, no GH-211 doctor errors, and bounded job outcomes in
  observations separated by at least the relevant cadence or maximum runtime (whichever is longer).
- [ ] Comment #211 with evidence, then create the fresh GH-210 branch from updated development and
  begin its Phase 0 spike.

### Phase 4 — QA checklist

- [ ] Artifacts are non-empty, commit-stamped, and distinguish observed from predicted.
- [ ] Independent QA approves and required GitHub checks are green.
- [ ] Deployment is a runtime fast-forward; rollback is a revert PR plus forward deployment.
- [ ] Pulse freshness and doctor/stack status close the user/operator loop.
- [ ] Status table and `updated:` date refreshed before #211 is shipped.
