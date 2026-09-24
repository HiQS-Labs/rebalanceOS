---
gh_issue: 23
source: https://github.com/HiQS-Labs/rebalanceOS/issues/23
title: "GH-23 — Durable fleet publication"
status: In progress
created: 2026-08-16
updated: 2026-09-24
owner: Codex
doc_type: bugfix
goal: Preserve fleet output and prevent shared Git writers from wedging or discarding work.
effort: 3
complexity: 3
risk: 3
phases: 3
ratings_provisional: true
reversibility: Costly — preserve outstanding output before changing deployed writers
---

# GH-23 — Durable fleet publication

| What was just completed | What's next |
|---|---|
| Read-only incident recon and operator-approved issue additions | Fable low plan QA, then regression controls and implementation |

## Table of contents
- [Scope and recon](#scope-and-recon)
- [Phase 0 — Confirm the contract](#phase-0--confirm-the-contract)
- [Phase 1 — Repair publication](#phase-1--repair-publication)
- [Phase 2 — Verify and deliver](#phase-2--verify-and-deliver)
- [Risks and rollback](#risks-and-rollback)
- [Lessons learned](#lessons-learned)

## Scope and recon

This supersedes the original speculative transport replacement / three-job topology in the
GH-23 intake. Operator request: additions to #23, relay with Claude Code Fable low/light, then
execute the smallest durable and safe repair. Keep Git, current scheduler and standalone fleet
collector. No new daemon, store, service, supervisor, LaunchAgent, or full scanner rewrite.
3-Eyes stays deferred. Skill content remains peer-editable; authored conflicts never auto-resolve.

Evidence: #206, #211 / PR #212, #225, #207, and private sync incident #1. September 12 and 16
recoveries did not close ownership gaps. Source review is not a runtime health claim. Graph
2026-09-02 was stale; all material seams were read directly. This plan uses debug-mantra for
execution-time failures and ponytail for scope adjudication.

### Recon map and ownership

| Entry / seam | Current behavior | Violation / target |
|---|---|---|
| `sleuth_reminders._refresh_file_source` | fetch + checkout remote file into worktree/index | reader must fetch/read blob without staging; explicit last-good fallback |
| `index_ops._refresh_sync` → `sync_snapshot.commit_and_push_sync` | lock, render device files and pointers, stage all sync/, commit entire index, push | exact owned paths; no imported reminder commits |
| `pulse_sync.sh` → `reconcile_pulse_mirror` → `publish_pulse` | reconcile outside lock, continue after failure, then lock publish | one transaction boundary, no self-started replay backlog |
| `pulse._commit_and_push_if_changed` | common publisher for page/digest/synthesis | preserve existing interfaces and exact remote verification; reject foreign staged work |
| `daily_synthesis._publish_clio_log` | read-modify-write begins before publisher lock | move entire RMW under common lock without nested flock deadlock |
| standalone `collect.sh` | config mkdir lock, pull before staging externally produced snapshots, independent git writer | same OS lock protocol as Python; preserve owned pending changes; no blanket commit/reset |
| `pulse._push_repair_actions.abort_rebase` / `git_pull_rebase_safe` | unscoped rebase abort | remove repair action; only abort transaction-owned rebase |
| `self_heal_sync_repo` | aborts existing rebase, replaces branch, hard reset | stop without modifying abnormal state; abort only self-started failed rebase |
| `sync/*/latest.json` | every device writes same pointer | preserve schema; resolve only generated pointer conflicts from validated device snapshots |
| installed collector | copied/symlinked by existing install.sh | verify installed source and preserve supported local collection configuration |

The shared transaction owns checkout/index/HEAD. External reminder source owns its export.
Each device owns its snapshot and heartbeat files. Per-slot digests/append-only history are
retained; generated page output is replaceable. User-authored skills never receive a generated
file conflict policy. Local flock cannot serialize peers; bounded push-race reconciliation and
explicit shared-pointer semantics remain necessary.

Current-state radius: Pulse page, fleet check-in, calendar/email relay, reminder ingest, dated
digests, CLIO daily log, deployed skill collection and their existing consumers.
Unknowns: external `latest.json` consumers, which independent snapshot/skill producers honor a
transaction, and package availability on other devices. Confirm before changing their protocol.

## Phase 0 — Confirm the contract

Timebox 1–2 hours. Reuse existing temporary-repository test helpers; no custom test runner.
- [ ] Inventory callers/producers and latest-pointer readers; retain the file schema.
- [ ] Inspect standalone installation/runtime compatibility. A full Rebalance install must not
  become a new collector prerequisite; reuse stdlib Python (already used by the collector).
- [ ] Reuse the already implemented Python common lock protocol: actual git-dir/rebalance-publish.lock, OS flock,
  nonblocking defer; the collector may use a small stdlib entry shim around its existing shell
  transaction, covered by a real interoperability test. No parallel lock registry.
- [ ] Fable low review approves this plan and explicit questions below; findings dispositioned.

QA: unresolved ownership or compatibility assumptions stop dependent edits, not all independent
work. Remote/DB access is already demonstrated by the incident reads; no live refresh needed.

## Phase 1 — Repair publication

Ordered implementation, extending existing modules:
- [ ] Write focused red regression controls for reminder read side effects, foreign staged
  content, dirty owned output, conflict preservation, peer races, identical retry, and Python/shell lock exclusion spanning reconcile through push.
- [ ] Reminder refresh returns parsed upstream content using fetch + show; fallback reads the
  unchanged local last-good file with refresh failure exposed. Validate data before ingest.
- [ ] Extend `lib/git_ops.py` with the smallest shared publication preconditions/retry mechanism
  after checking existing helpers. No rebase/detached operation may discard work. All callers
  use the same OS lock from reconciliation through write/stage/commit/push; RMW reads included.
- [ ] Preserve owned stranded output by committing its exact paths before reconciliation when
  necessary. Refuse foreign staged or tracked dirty paths without modifying them. Check Git
  states before writing and before retry; no automatic stash, reset, branch replacement.
- [ ] Snapshot publication stages only this device's calendar/email payloads and the two known
  pointers. Never stage the whole sync directory. Authored/unrelated files remain untouched.
- [ ] Keep pointer schema; narrow deterministic recovery to calendar/email latest.json conflicts:
  recompute from valid device snapshots by parsed UTC generated_at (tie by device ID). Missing/malformed candidate timestamps stop automatic resolution. Do not
  generalize to sync/**/*.json or skills. Unrelated conflicts stop and preserve original work.
- [ ] Retry existing delivery before minting more routine commits. On unresolved conflict, keep
  local commit/payload and report blocked. Preserve unique digest/history outputs on delivery
  failure (never just skip their generation silently). Coalesce replaceable pending pages only
  within explicit owned output; do not rewrite arbitrary local history.
- [ ] Remove model escalation from these deterministic Git failures; one peer-race retry, then
  actionable error with blocked paths/pending state. Keep rendering success separate from delivery.
- [ ] Collector shares lock with Python; moves handling of its known pending snapshot/projection
  paths before pull, rejects other dirt, never stages the whole skills collection implicitly,
  removes destructive self-heal, retries boundedly and advances cursor only after verified delivery.
  Preserve scanner/dedup behavior; stop on pre-existing rebase rather than touching another task.

QA: real temporary repositories with nonempty content; deterministic negative controls must fail
before fixes, same controls pass after. No speculative fuzzer or external live writes in tests.

## Phase 2 — Verify and deliver

- [ ] Focused suites: pulse reconcile/self-repair, sync snapshots, reminder file source, collector
  CLI, daily synthesis and orchestrator outcomes. Cover actual Python/shell lock interoperability.
- [ ] Run root suite and HiQS suite in isolation, never deferred 3-Eyes. Lint/types, PDDA, script
  inventory, relevant shell syntax. Preserve red/green results in TESTS-RESULTS per SOP.
- [ ] Fable low final relay QA on committed diff and evidence; resolve boundedly (three rounds).
- [ ] Version/changelog and deployment runbook; ready PR targeting development with exact checks.
- [ ] Runtime recovery/deployment: preserve unique commits, files, staged/untracked state and refs;
  pause only relevant existing writers, reconcile preserved content, update actual invoked
  executables and restart existing jobs. No force push/reset or deletion of original evidence.
  Verify remote content and scheduled outcome before calling the runtime recovered.

Done requires consumer-visible remote payload, not local commit/exit alone. PR-ready and deployed
are separate states. No claim of all devices updated without evidence from those devices.

## Risks and rollback

Risk 3 (costly): publication contract spans independent deployed actors. Shield: real fixtures,
reviewed narrow diff, then single-device pilot. Tripwire: lost content, foreign staging, unresolved
conflict, false delivery/cursor acknowledgment, or old deployed writer bypassing lock => stop pilot
and preserve evidence. Roll back code by revert/forward deploy; keep backups/local refs for content.
No destructive rollback. Existing blocked checkout is recovered separately from tests.

## Review questions

1. Does the bounded lock bridge preserve standalone collector installation without introducing a
   second publisher framework? Prefer a smaller existing primitive where available.
2. Are pre-existing staged/dirty/rebase states preserved, including interrupted pending writes?
3. Is pointer-only deterministic conflict recovery safe with unchanged consumer schemas and old
   peers? Does any proposed step accidentally make authored files last-writer-wins?
4. Does delivery failure preserve unique digests and history without endless snapshot commits?
5. Are retry/cursor semantics and tests sufficient and commensurate? Identify concrete failure
   input, affected scope, falsifier; reject speculative enterprise machinery.

## Lessons learned

A scoped git add does not scope a later git commit. A reader that checks out a remote file is a
writer to the shared index. A lock is useful only if every mutator shares its transaction boundary.

## Plan QA dispositions (2026-09-24)

Fable 5.1 low round 1: PASS text, driver exit 4 close-mismatch (reviewer released rather than
completed the token); not counted as a completed relay. Round 2 verifies these dispositions and
closes through the real harness.

- Implemented: reuse existing Python flock; shell bridge holds an inherited descriptor for the
  entire transaction. Do not introduce per-step locking or another lock registry.
- Implemented: inventory and remove the Python unscoped abort action as well as shell self-heal;
  pre-existing rebase/detached states remain unchanged.
- Modified: claimed zero lock tests is incorrect (`test_pulse_self_repair.py:69` already holds
  `git_publish_lock`). Existing test covers two Python callers, not shell/Python interop; add
  that exact missing red control before code.
- Implemented: the standalone reconcile entry also locks and guards rebase ownership.
- Implemented: malformed/missing candidate timestamps stop pointer auto-resolution.
- Retained: retry only on nonzero push status and rejection signature; no string-only success path.
