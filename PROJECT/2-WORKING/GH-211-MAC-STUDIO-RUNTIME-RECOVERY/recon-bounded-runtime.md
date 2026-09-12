---
title: GH-211 bounded runtime recovery — Recon Map
status: Complete
owner: Mac Studio runtime recovery arm
created: 2026-09-12
updated: 2026-09-12
goal: Map the scheduler, process, database, Git, health, and rollback seams before GH-211 changes.
roadmap_exempt: true
---

# GH-211 bounded runtime recovery — Recon Map

## Scope and evidence

Verified against commit `3801fa5` in a fresh clone. The code graph generation was dated
2026-09-02 and excluded operational scripts, so it was used only to locate Python seams; every
material path below was read from the task clone. Live observations came from the declared Mac
Studio runtime and are evidence, not a claim about other devices.

## Current-state trace

1. `SCHEDULER.md:14-24` is the fleet policy source. `scripts/stack.sh:54-84,282-314` parses it and
   installs plist templates through `scripts/lib/install_common.sh:45-116` into the runtime root
   declared at `~/.config/rebalance/runtime-root`.
2. The daily, GitHub, vault-embedding, pulse-web, and HiQS wrappers enter Python synchronously.
   None has a job-wide wall-clock deadline.
3. Embedding leaves use `utils/job_guard.py:496-641,907-1051` for flock, child process groups, and a
   memory ceiling. `run_guarded()` waits forever after launch; incumbent wrappers do not call it.
   Persisted guard lockfile contents are advisory; kernel `flock` ownership is truth.
4. SQLite writers use WAL and a 30-second busy timeout (`db/connection.py:20-50`). Only vault,
   GitHub, and semantic stages retry lock failures, three attempts with 5/10-second backoff
   (`index_ops.py:1891-1945`). Overlapping jobs can still retain readers/writers indefinitely.
5. `scheduler_common.sh:26-68` appends `job_started` and terminal lifecycle events. A stuck job has
   no terminal event. `doctor.py:998-1122` and `stack.sh:417-485` nevertheless mark every live PID
   healthy without consulting elapsed runtime.
6. `pulse_web.py:3335-3370` atomically replaces HTML, but `pulse_server.py:294-304` reports
   `ok: true` whenever the artifact exists, even when its reported age is far beyond cadence.
7. Semantic vectors have no foreign key (`db/schema.py:107-185`). Canonical deletion removes the
   vector before its document (`db/semantic.py:144-156`), but no supported command targets existing
   orphans. `semantic-embed --force` is the only current supported rebuild path.
8. Pulse, digest, synthesis, snapshot, and the external fleet collector share a Git checkout with
   no cross-writer lock. Publishing writes content before `git add`; after an index-lock failure a
   retry can call identical dirty content "unchanged" without proving commit or push
   (`pulse.py:797-874`).

## Observed failure path

- Multiple launchd jobs remained live for 2–26 hours. Samples placed GitHub sync in SQLite
  commit/checkpoint work, embeddings and health checks in large SQLite scans, and daily sync in
  subprocess waits. Lifecycle history also records jobs lasting 9–27 hours, so the blind spot is
  recurrent rather than a one-off label error.
- The database was about 4.93 GiB with a large WAL; doctor hit `database is locked`, reported 1,735
  orphan vectors and 4,472 pending embeddings, while launchd PIDs still appeared healthy.
- The pulse HTTP endpoint returned healthy while its generated artifact was over a day old.
- The shared sync checkout had a zero-byte `.git/index.lock` with no `lsof` owner, was 112 commits
  behind, and contained tracked and untracked local work. All work must survive recovery.

## Contracts and blast radius

- Scheduler policy is consumed by shell and Python parsers and pinned by
  `tests/test_scheduler_policy.py`; a new policy field must update both readers and tests.
- Guard exit codes 3/75 are deferred, 4 is a mid-run resource failure, and 143 is eviction.
  Timeout needs a distinct terminal reason while preserving child exit codes.
- Doctor checks flow through `compute_health_status()` into CLI JSON and the issue reporter. New
  detection must reuse that contract.
- Deploy affects the declared runtime, editable install, launchd plists, and pulse server. 3-Eyes
  is inert and explicitly out of scope.
- Shared-checkout recovery affects pulse, digest, synthesis, fleet check-in, and Sleuth consumers;
  schemas and paths stay unchanged.

## Unknowns retained as gates

- Derive legitimate ceilings from recorded completed-run durations and cadence; do not guess from
  cadence alone.
- Before signals, recheck PID ancestry, elapsed time, logs, and DB/WAL ownership. After stopping,
  prove a checkpoint and exclusive transaction succeed.
- Before moving the Git lock, recheck ownership and Git processes, inventory status/stage/refs, and
  preserve local evidence. Explicitly reconcile and verify remote content; "unchanged" is not proof.
- Sample semantic orphan IDs before repair. Historical attribution may remain unknown; repair must
  use a supported, backed-up, auditable command rather than raw SQL.

## Rollback today

Stack down preserves plists and runtime data. Code rollback is a revert PR followed by a
fast-forward deployment; database recovery requires a verified backup before mutation. The shared
Git checkout is not reset or stashed: preserved local work is the rollback artifact.
