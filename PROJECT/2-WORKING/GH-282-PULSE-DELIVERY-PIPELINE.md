---
gh_issue: 282
source: https://github.com/HiQS-Labs/rebalanceOS/issues/282
title: "GH-282 pulse delivery pipeline: reliable writes, honest liveness, and one owner per path"
status: "Active: implementation and hardening merged/deployed locally; fleet operational qualification remains."
created: 2026-09-26
updated: 2026-10-02
owner: noel
doc_type: architecture
goal: >
  Harden the Git Pulse sync delivery pipeline across fleet Macs: establish an honest exit code
  taxonomy (0=OK, 1=Config, 2=Git Error, 70=Render Error, 75=Busy/Skip), add explicit push/pull timeouts,
  replace silent UTC fallback with host timezone resolution, add bounded jittered retries,
  and transition to disjoint per-device namespaces (`devices/<id>/...`) with reader aggregation.
effort: 4
complexity: 3
risk: 2
phases: 4
ratings_provisional: true
roadmap_exempt: false
---

# GH-282 — Pulse delivery pipeline: reliable writes, honest liveness, and one owner per path

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 #283, implementation #303 and review hardening #304 merged; Studio runtime 0.97.1 verified with native Fable-high approval, CI and actual capture/render/delivery/reconcile/same-note checks. | Qualify other-Mac installation/source inventory, external hook locks, actual offline/rejoin/Sync/archive capacity and seven-day delivery results. |

## Why

Hourly delivery fails on multiple Macs due to push collisions on shared files, lock contention, and uncaught timeouts. At issue intake on September 26, git timeouts and exceptions were swallowed and logged as Exit 1 ("config or render error"), and busy locks exit 2 (counted as failure). Furthermore, `pulse_health.py` reports devices as ALIVE even when pulse delivery has failed for days because it only inspects the collector heartbeat.

## Ratings, with reasons

Rated 2026-09-26 per consensus in AgentChorus #132026.

| Field | Value | Why |
|---|---|---|
| `pri` | 80 | High fleet impact: hourly pulse sync repeatedly fails or collides across 4 Macs. |
| `sev` | 70 | Misleading diagnostic reporting and silent delivery failures. |
| `appeal` | 55 | Operator wants reliable hands-free fleet sync across all devices. |
| `effort` | 65 | Remaining work spans shared producer policy, collector ownership and truthful readers. |

## Phase 1 — merged diagnostics
PR #283 merged the exit taxonomy, configurable deadlines, host timezone fallback and doctor skip handling. Its original implementation plan is superseded by the ordered work below.

## Table of contents
- Phase 0 — grounded recon and prior art
- Phase 1 — already merged diagnostics
- Phase 2 — device-owned output and sole existing pusher
- Phase 3 — truthful delivery readout and deployment qualification

## Phase 0 — Prior Art Review
The current shared publisher already provides exact-path commits, a common advisory lock,
configurable 120-second Git deadlines and pending-error returns. Extend it rather than add a
publisher. The existing collector remains the sole scheduled pusher per Mac; no new timer,
vector store, push loop or XYZ ledger writer. Snapshot readers can select the freshest validated
per-device payload instead of sharing latest.json. Three-Eyes remains deferred.
Source audit: `GH-282-RECON.md`. Baseline at 4349ff5: 2804 passed, 21 skipped,
11 xfailed, 143 subtests; full tests and HiQS tests in a disposable full clone.
QA gate: Claude Fable 5.1 high-effort plan review before implementation.

## Ordered implementation and acceptance
1. Add opt-in fleet configuration with an explicitly validated device ID matching the existing
   collector identity. Device-owned live pulse, daily synthesis and digests go under
   devices/<id>/; all existing Python publishers commit only in this mode, including CLI/MCP.
   Legacy behavior stays available for rollback. Reject missing/unsafe identity before writing.
   -> Existing publication suites prove no Python push and no cross-device output collisions.
2. Calendar/email retain their existing per-device layout. Fleet mode stops writing latest.json;
   read_latest_snapshot derives the latest valid device snapshot with deterministic tie breaking.
   -> Existing snapshot tests cover stale pointers, invalid payloads and deterministic selection.
3. Extend the existing collector's exact owned staging to its namespace and sync payloads.
   Use bounded Git timeouts, at most three delivery attempts with 2–20-second jitter,
   and deterministic per-device delay capped at 240 seconds without changing launchd cadence.
   Preserve pending commits and refuse foreign changes/conflicts. No automatic ours/theirs.
   -> Existing real-Git collector suites plus red controls verify retries and unrelated dirt refusal.
4. Expose a read-only fleet view of device pages. Collector health distinguishes a fresh heartbeat
   with missing/stale live-pulse output from healthy publication. A failed network delivery cannot
   instantly report its failure remotely: readers observe the last delivered evidence and age.
   -> Existing health tests verify ALIVE_NOT_PUBLISHING and legacy metadata compatibility.
5. CLIO's canonical PR #5 remains its separately reviewed prerequisite. Connect only explicitly
   configured helper/database/owner UUID to the collector; validate and stage only that UUID's
   snapshot, reconcile committed blobs and preserve the same Obsidian path/header/300-second
   exporter. Do not infer canonical capture identity from a hostname or echo imported origins.
   -> Existing CLIO gates and a disposable real-Git integration probe establish owner-only transport.
6. Run full tests in a disposable full clone; independent Claude Fable 5.1 high-effort final QA;
   fix concrete findings, commit evidence, publish a development-targeted PR and merge after gates.
   -> Actual reviewed SHA, model/effort, test counts and hosted runs are recorded.
7. Back up runtime/config/collector/private DB/note before local activation; fast-forward the
   stable runtime, update the existing collector copy and opt in only this Mac. Preserve schedules.
   -> Actual local capture, committed export, delivered upstream and same-note rendering verified.
   Other three Macs stay off; rollback restores config/collector/runtime from backups.

## Deployment boundary and remaining qualification
This change is Costly because several producers share the private Git checkout. Rollback disables
fleet mode, restores the backed-up collector/runtime and retains all commits and private backups.
Normal sleep/offline/rejoin requires no designated central Mac or publisher election. Every Mac
keeps a local replica; the shared Obsidian note is a rendered view, never capture/control state.
The issue remains open until the real four-Mac rollout, at least three actual Pulse cycles including
an offline/rejoin interval, source inventory/archive capacity checks and seven-day failure-rate
qualification complete. Synthetic probes do not satisfy these live gates. Historical gaps are
accepted; no additional source recovery is required.

## Lessons Learned (For Future Agents)
PR #283 fixed diagnostics, not the remaining ownership architecture. Runtime can lag merged code.
A locally committed page is queued, not proof of remote delivery. Do not count busy exit 75 as a
failure, require an upstream proof before advancing scan watermarks, and preserve rejected commits.
Python hostname IDs and collector IDs previously differed: use explicit matching configuration.
Run mutation-heavy tests in a separate full clone; a linked worktree shares Git configuration.


## Plan QA dispositions — Fable high, round 1
1. Implemented: fleet results carry `queued=True`, not `pushed=True`; daily synthesis, digest and sync outcome gates explicitly accept queued success. Fleet mode always wins over caller push=True and PULSE_PUSH; fleet-off preserves the existing knob.
2. Implemented: the collector config remains the device identity source of truth. Python reads its literal configured device_id at each publish and compares it to pulse_device_id; missing, unsafe or mismatched values refuse before write. Fleet sync payloads use this matching ID. Collector fleet_sync_subdir must match Python sync_subdir; no hostname inference. Historical latest.json stays retained as legacy evidence, ignored by the derived freshest-snapshot reader and not written in fleet mode. That reader is an existing API, not a new production pipeline.
3. Implemented: deterministic stagger runs before lock acquisition. Existing python3 supplies collector Git deadlines through subprocess process-group termination, no timeout(1) dependency. Every network call is bounded; failure exits Git code 2, busy remains 75. Both early and final pushes use bounded retry/upstream setup. Pending commits remain intact.
4. Implemented: canonical CLIO owner export is exactly devices/<configured-CLIO-UUID>/clio.jsonl. Imported history remains solely in the private SQLite DB outside the Git checkout; the helper never writes imported origins under snapshots/. The legacy snapshots/ transport remains for its existing hook, explicitly outside CLIO's owner export. No broad devices/ staging.
5. Implemented: collector YAML carries fleet_mode=true only for opted-in devices. Legacy/unmarked collector devices keep existing ALIVE classification. The live-pulse producer records an owned status with last attempt, last render success and last exit; fleet health distinguishes render failure/staleness and pending delivery using committed upstream status rather than trusting dirty local output. Failure visibility requires a successful delivery of that status; offline peers can only age the last delivered evidence.
6–10. Implemented/clarified: no new reader daemon; old pointer retained but ignored; existing PULSE_PUSH precedence explicit; old plan superseded; no-upstream/early-network taxonomy covered. Rollback requires a clean private checkout and no unpushed fleet commits; otherwise preserve it and retain the new collector until pending data is reconciled.


## Implementation checkpoint
Fleet mode uses `devices/<id>/status/pulse-sync.json`; the page and attempt status each commit under
the same non-blocking common lock. They are separate transactions; a collector intervening between
them may deliver a page before its matching status. Health conservatively waits for matching upstream
status/page evidence and never labels a merely queued render delivered. Status records preserve the
last good render timestamp/hash after failure. Busy and identity-refused runs cannot write a status;
staleness remains their observable signal. `pulse.fleet_view` extends the existing publish result.

The canonical helper's post-pull owner destination is rechecked for symlinks/escape, and prior owner
snapshot identities cannot disappear. Existing legacy snapshots/PDDA producers are not rewritten in
this repository: their exact common-lock participation still needs per-installation verification (B4).
This is an explicit remaining qualification, not a claim that external hooks were audited exhaustively.

Red control: a normally configured device initially missed the fleet marker because it was inserted
only in the migration metadata block. The forced render-failure probe stayed ALIVE; adding the marker
to the regular metadata block made the same assertion pass. Timeout verification must compare pending
working bytes: a failed git-add can leave newer generated files dirty, and PREPARE correctly commits
those bytes before another push. Freezing the old committed heartbeat/snapshot timestamps is an
incorrect preservation oracle. No source prompt text is included in committed evidence.

## Implementation QA dispositions — Fable high, round 1
1. Implemented: named 10-hour render age bound respects the scheduled overnight gap, DST,
   producer budget and collector delivery grace; explicit failures/queues remain immediate.
2. Implemented: doctor and health-check carry reasons for queued, failed, unavailable and aged
   evidence. A queued local failed attempt exposes its own exit while retaining delivered proof.
3/5/6. Implemented: documented CLIO-only collector halt; corrected retry/state documentation and
   redundant import; status-write errors are classified rather than silently exited 0; final Git proof
   failure exits 2.
4. Retained: text-mode page comparison is a pre-existing limitation with no observed CR-bearing
   page in this scope. No new binary Git API or payload schema is introduced for a speculative case.
Existing pulse-health tests now cover 80/190-minute healthy delivery, the 10-hour boundary, just
past it, and distinct queued/failed reasons. These tests went red against the previous candidate.

## Implementation QA — final approval
Claude Fable 5.1 high-effort round 2 approved the candidate through the native relay (driver exit 0; reviewed head 9719f95). A temporary doctor WARN while a successful render awaits the existing collector is expected; observe this across three actual intervals during rollout before changing alert policy. Remaining text-only nits (generic attempt versus render failure wording and legacy health-check exit-code docstring) do not change delivery correctness and are deferred.

## Studio deployment and post-landing review

CLIO #5 landed at 6a53a38; Rebalance #303 landed at bb84cd0. The stable runtime and copied collector were updated, three preserved origins bootstrapped once, and matching fleet settings activated. Five existing delivery jobs were briefly unloaded and restored with identical plist hashes; capture and the 300-second note exporter remained enabled. Actual render queued without pushing, the existing collector delivered it, and health moved from queued to ALIVE. SQLite integrity, every backed-up record/payload, the personal header and same note path passed. Receipt: `TESTS-RESULTS/2026-10-02+GH-282/deployment.json`.

Late advisory review identified five reproducible configuration-error escapes (missing target, publication mismatch, sync identity, scheduler doctor and fleet doctor). A bounded follow-up centralizes target validation and returns structured errors without writing data; deadline initialization also fails explicitly. These are error-path fixes, not a new delivery system. The initial pre-delivery health check saw legacy ALIVE because the old heartbeat did not yet advertise fleet mode; after the first collector delivered the marker, the queued/delivered transition was verified. Manual immediate runs do not qualify three scheduled intervals or fleet offline/rejoin.

Follow-up Fable round 1 dispositions: F1 restore the changelog template and bracketed release heading; F2 preserve unscoped scheduler liveness on invalid identity; F3 capture the deadline forcing command and both exit codes; F4 exercise real collector configuration rather than injected exceptions; F5 distinct scheduler/fleet failure names; F6 truthful fleet dry-run text; F7 sanitize public log paths with raw hashes retained privately. All addressed without new runtime components.

Final local recheck: Rebalance #304 landed at 8cba6de and runtime 0.97.1 is deployed. All seven tested source hashes match; the copied collector is updated and existing Pulse Server restarted. Final receipt deployment-recheck.json records actual owner-only delivery, ALIVE health, SQLite integrity, all backup records/payloads, natural capture after helper upgrade and the same note/header. All five delivery jobs are loaded with unchanged plists; capture/export schedules are unchanged. Source/runtime implementation is complete locally; the operational gates above remain open.

## Studio follow-through — 2026-10-02

Forge #937 owns cross-repo completion; Rebalance #305 is its pointer. Focused local controls found Unicode JSONL boundary loss, positional Daily citations and missing canonical provenance in consumer metadata. Keep the configured full-history compatibility export and existing consumer IDs; retain canonical origin references additively. Enable existing semantic registry providers through the maintenance facade so selected CLIO backfill actually materializes documents without embedding. Recorded controls and source-bound receipts: `TESTS-RESULTS/2026-10-02+GH-305/`.

Consult: Codex and Agy agreed on additive references, preserved keys and bounded local qualification. Codex identified the missing nonembedding facade path and collision/fallback controls; implemented. They disagreed on compressor tuning; the proposed override was withdrawn. Plists, schedules and memory safeguards remain unchanged. Scheduled heavy/derived work that the guard refuses is deferred, not verified successful. No other device is enabled and no full reembedding or cloud synthesis is claimed.

Rollback: source changes are reversible; consumer schema adds only a references column and preserves old IDs/content. Back up the destination via SQLite backup API before import, retain source and configuration backups privately, and stop destination writers before any restore. Restore loses subsequent consumer updates, so preserve a fresh copy first; source capture history is never rolled back. Local installation locations remain in the private sidecar named by Forge #937.
