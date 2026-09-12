# RELAY · GH-211 bounded runtime recovery plan QA
<!-- Single source of truth. Read the entire file before acting. -->

NEXT: Closed
STATUS: Open
ROUND: 4 / 4

## ▶ TAKE YOUR TURN — read this first

1. Read this whole file and act only when `NEXT` names your role.
2. Reviewer: grade findings `[Blocker]`, `[Should]`, `[Nit]`, or `[Pass]`, cite file:line, propose a
   concrete fix, declare `swept file: yes|no`, and set `VERDICT: Approved|Changes requested|Blocked`.
   Do not edit product or plan files.
3. Producer: disposition every finding, apply accepted fixes, and append one response block.
4. Append one block at the bottom; never rewrite earlier turns. Flip `NEXT`, update `STATUS`, and
   increment `ROUND` only when the Producer opens another cycle.
5. Commit only this relay file and explicitly name the next role. Reviewer alone may close Approved.

## Setup

- Artifact: `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md`
- Recon: `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY/recon-bounded-runtime.md`
- Reviewer: codex · Producer: claude-a
- Definition of Done: the plan is grounded, minimal, diagnosable, blast-priced, and independently
  executable without risking existing runtime/database/Git work or activating 3-Eyes.

Read the artifact and Recon Map in full, then inspect `SCHEDULER.md`, `SOP.md`, `AGENTS.md`, and cited
code/tests as needed.

Questions:

1. Does every proposed change follow a verified current call/write path, with unsupported claims  [Unverified — no citation]
   exposed as gates rather than assumptions?
2. Is extending the existing job guard and scheduler policy the smallest coherent fix, without
   duplicating supervision or reactivating 3-Eyes?
3. Are timeout semantics, exit codes, process-tree reaping, lifecycle evidence, and per-job ceilings
   implementable and testable without guessing?
4. Do stack, doctor, pulse health, Git publication, and semantic repair close the actual false-green
   paths without expanding public schemas or destructive authority?
5. Are database and dirty-Git recovery shields, tripwires, backups, and rollback sufficient to
   preserve unique local work?
6. Does every phase have falsifiable proof: red controls, non-empty artifacts, full gates,
   independent final QA, safe deployment, and handoff to GH-210?
7. Flag missing scope, overreach, unsafe ordering, contradiction, or weak acceptance. Cite file:line
   and give the cheapest correction.

## Ground rules

1. This thread is the single source of truth; agents share no memory.
2. One turn is one appended block. Findings are bullets, not essays.
3. Reviewer changes only this relay file; no push.
4. The relay ends only on Reviewer Approved or escalates at round four.

## Log

### Round 1 — Reviewer (codex)

- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:69-70` requires a distinct
  timeout reason while preserving existing exit codes, but never assigns timeout an exit code or
  defines how that code reaches the lifecycle event, launchd, stack, and doctor. This leaves the
  central terminal contract to implementation guesswork. Specify one unused timeout exit code,
  distinguish it from resource exit `4`, eviction `143`, and child exits, and add assertions for the
  wrapper result plus `job_failed`/stack/doctor classification.
- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:50-54,69-75` promises coverage
  for every finite scheduled batch but only says to wire “managed wrappers”; the policy includes
  finite Python-direct jobs as well as a ceiling-free daemon. Add a per-job matrix naming the
  measured ceiling, unit/sentinel, enforcement entry point (wrapper or plist/adapter), health age
  source, and explicit daemon exemption. Pin parser rejection of missing, zero, negative, duplicate,
  and malformed values so no finite job silently escapes the contract.
- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:98-99` says “backup, checkpoint”
  without naming a WAL-safe backup mechanism or ordering it after exclusive access is proven. A
  file copy can omit committed WAL state. Require stack-down and no-holder/exclusive proof first,
  then either a successful checkpoint followed by the DB copy or SQLite's backup API; verify the
  restored copy with integrity checks before orphan apply, and state the exact restore command.
- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:78-79,98-100` gives semantic
  orphan deletion an `apply` switch but omits the repository's mandatory destructive confirmation
  and >1,000-row escalation contract. Route the command through the semantic-stage owner, require an
  explicit confirmation flag in addition to apply, stop before mutation above 1,000 unless the
  additional confirmation is present, and test audit output and transaction rollback on failure.
- [Should] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:76-77` leaves “shared-Git
  publication” and the advisory-lock contract ambiguous even though the Recon Map names several
  writers. Enumerate every in-scope publisher, reuse one shared Git helper/lock identity, define lock
  acquisition boundaries and conflict behavior, and test the unchanged-but-dirty, staged, divergent
  HEAD, concurrent publisher, push-failure, and remote-content cases. Gate any external fleet
  check-in change separately if it is not owned by this repository.
- [Should] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:75,121-124` does not define the
  artifact-age threshold, the two observation times, or which jobs are safe for staged startup;
  `stack.sh up` is fleet-wide. State the freshness threshold and boundary behavior, name the exact
  initial job subset and supported start commands, and require observations separated by at least
  the relevant cadence/ceiling rather than two immediate samples.
- [Should] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:115-116` names `pytest tests/`
  and “relevant” shell tests, which is weaker than the repository's full-suite requirement including
  CI-skipped surfaces. Name the canonical full gate and explicit non-3-Eyes exclusions, plus the
  focused guard, scheduler-policy, stack/doctor, pulse-health, Git-publication, and semantic-repair
  tests whose non-empty outputs must be published.

swept file: yes

Verdict: Changes requested

### Round 1 — Producer (claude-a)

- Implemented all four Blockers: the plan now assigns conventional timeout exit 124 and its full
  lifecycle/status contract; adds a twelve-job enforcement/health matrix with the daemon exemption
  and parser rejection rules; orders no-holder/exclusive proof before SQLite `.backup` plus integrity
  and explicit restore; and adds `--confirm` plus a greater-than-1,000-row `--confirm-large` gate,
  transaction rollback, and audit assertions.
- Implemented the Git-publication Should: the plan enumerates the four in-repo publishers, one lock
  boundary, conflict behavior, six required cases, and keeps the externally owned collector recovery
  only.
- Implemented the freshness/startup Should: the plan defines the schedule-aware 90-minute boundary,
  exact staged jobs and kickstart command, and cadence-or-limit-separated observations.
- Implemented the gate Should: the plan names every CI-equivalent command family, Python lanes,
  embedding seam, HiQS suite, focused outputs, and the sole 3-Eyes exclusion.

Handing off to Reviewer for round 2 — verify the revised artifact and close only if every central
contract is independently executable.

### Round 2 — Reviewer (codex)

- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:49-53,70-73,98-103`
  places `job_guard.py` outside the current wrapper/Python command but says the wrapper EXIT trap
  records `job_failed(exit_code=124)`. The current trap can observe only its own child-side exit
  (`scripts/lib/scheduler_common.sh:47-54`), while the outer guard owns the eventual timeout result;
  moreover the three Python-direct jobs have no wrapper trap at all (`SCHEDULER.md:20-22,106-109`).
  Thus the required lifecycle evidence is impossible as specified and implementations must guess
  between 124, TERM/KILL status, or no terminal event. Make the outer guard the single lifecycle
  writer for every guarded finite job (and prevent duplicate inner events), or introduce one shared
  adapter inside the lifecycle boundary; then pin wrapper and Python-direct timeout cases proving
  exactly one `job_started` and one `job_failed` with `exit_code=124` and
  `reason=wall_clock_timeout`.
- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:104-106` defines 06:00–23:59
  as the active 90-minute window while also allowing the prior final artifact until 06:53 as an
  off-hours rule. The intervals overlap from 06:00 through 06:53 and yield opposite health outcomes
  for an overnight artifact, so the endpoint and boundary tests cannot implement one answer. State
  the precedence explicitly—cheapest is an overnight grace through exactly 06:53, followed by the
  90-minute rule—and add boundary cases immediately before, at, and after 06:53.

swept file: yes

VERDICT: Changes requested

### Round 2 — Producer (claude-a)

- Implemented the lifecycle Blocker: the plan now makes scheduled-mode job guard the single event
  writer for wrapper and Python-direct jobs, suppresses only inner child traps, and requires exactly
  one start plus one terminal event in both timeout cases.
- Implemented the freshness Blocker: overnight grace now has explicit precedence through exactly
  06:53, followed by the active 90-minute rule, with before/at/after boundary tests.

Handing off to Reviewer for round 3 — verify these two corrected contracts and approve only if the
plan is executable without event duplication or time-window ambiguity.

### Round 3 — Reviewer (codex)

- [Blocker] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:167-170` says to reinstall
  bounded plists before the staged `pulse-server` → warning watcher → pulse-web startup, but the
  existing supported installers always unload, render, and load their jobs
  (`SCHEDULER.md:102-105`), and `daily-sync`, `pulse-server`, and `pulse-warning-watch` include
  `RunAtLoad` (`SCHEDULER.md:14,19-20`). A fleet-wide reinstall can therefore start finite DB work
  before the stated DB tripwires and makes “First kickstart only `pulse-server`” false. Replace this
  with an explicit per-job install/load sequence: keep the fleet down; install/load only
  `pulse-server`, observe it; then install/load the watcher; run the DB tripwires; install/load and
  deliberately trigger `pulse-web-sync`; only after those checks install/load the remaining finite
  jobs. If the current installers cannot preserve that ordering, add a gated render-without-load
  mode and test that no non-selected label is bootstrapped.
- [Should] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:139-142,148-149` requires a
  checkpoint in the Phase 3 QA checklist, but the executable recovery step goes from exclusive proof
  directly to SQLite `.backup` and never names the checkpoint command or its ordering. Either remove
  checkpoint from the acceptance criteria because `.backup` is the chosen WAL-safe mechanism, or
  explicitly run and record `PRAGMA wal_checkpoint(...)` after the no-holder proof and before the
  backup; keep failure as a phase-stopping tripwire.

swept file: yes

VERDICT: Changes requested

### Round 3 — Producer (claude-a)

- Implemented the startup-order Blocker: deployment now keeps the fleet down and installs/loads only
  pulse-server, then the watcher, then pulse-web after DB proof, followed by each finite job with
  RunAtLoad daily-sync last. Fleet-wide up is forbidden until all are observed; a tested
  render-without-load mode is required if current installers cannot preserve the order.
- Implemented the checkpoint Should: the executable recovery step now runs
  `PRAGMA wal_checkpoint(TRUNCATE)` after no-holder/exclusive proof and before `.backup`, with failure
  stopping the phase.

Handing off to Reviewer for final round 4 — approve only if the revised plan is safe and directly
executable; otherwise escalate with the remaining blocker.

### Round 4 — Reviewer (codex)

- [Pass] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:168-175` now keeps the fleet down,
  installs and observes only the selected labels in dependency order, delays finite jobs until the DB
  tripwires pass, and requires a tested render-without-load path if current installers cannot preserve
  containment. This resolves the RunAtLoad contradiction without activating 3-Eyes.
- [Pass] `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:139-143` now places
  `PRAGMA wal_checkpoint(TRUNCATE)` after no-holder/exclusive proof and before SQLite `.backup`, makes
  failure phase-stopping, verifies backup integrity, and records the restore command.
- [Pass] Full-plan sweep: the timeout/lifecycle contract, per-job policy, freshness precedence,
  single Git publication path, confirmed semantic repair, recovery shields, full gates, staged deploy,
  and GH-210 handoff are independently executable and preserve the stated scope
  (`PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md:46-187`).

swept file: yes

VERDICT: Approved

<!-- ↓↓↓ NEXT TURN goes here; marker stays last ↓↓↓ -->

### System · relay-drive — 2026-09-12T16:33:50Z
terminal STATUS Approved written by FAILED reviewer turn (codex; shim returned non-zero) — reverted
