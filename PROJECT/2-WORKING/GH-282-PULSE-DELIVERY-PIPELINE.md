---
gh_issue: 282
source: https://github.com/HiQS-Labs/rebalanceOS/issues/282
title: "GH-282 pulse delivery pipeline: reliable writes, honest liveness, and one owner per path"
status: "Active: Phase 1 merged; fleet delivery implementation and local deployment next."
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
phases: 3
ratings_provisional: true
roadmap_exempt: false
---

# GH-282 — Pulse delivery pipeline: reliable writes, honest liveness, and one owner per path

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 implemented in PR #283: honest exit taxonomy (0/1/2/70/75), bounded 120s git timeouts, timezone fallback defaulting to local host timezone, rebase cleanup, and launchd exit 75 skip logging. | PR #283 is merged. Complete fleet-mode namespaces, sole collector delivery, independent Claude Fable high-effort QA, and Studio deployment; qualify the other Macs separately. |

## Why

Hourly delivery fails on multiple Macs due to push collisions on shared files, lock contention, and uncaught timeouts. Currently, git timeouts and exceptions are swallowed and logged as Exit 1 ("config or render error"), and busy locks exit 2 (counted as failure). Furthermore, `pulse_health.py` reports devices as ALIVE even when pulse delivery has failed for days because it only inspects the collector heartbeat.

## Ratings, with reasons

Rated 2026-09-26 per consensus in AgentChorus #132026.

| Field | Value | Why |
|---|---|---|
| `pri` | 80 | High fleet impact: hourly pulse sync repeatedly fails or collides across 4 Macs. |
| `sev` | 70 | Misleading diagnostic reporting and silent delivery failures. |
| `appeal` | 55 | Operator wants reliable hands-free fleet sync across all devices. |
| `effort` | 65 | Phase 1 is clean, localized, and highly testable (~50 lines across 3 files). |

## Implementation Plan

### Phase 1: Diagnostic Honesty & Resilience (Current Scope)
1. **Exit Code Taxonomy**:
   - Update `scripts/pulse_sync.sh` to classify exits cleanly: Exit 0 (OK/no-change), Exit 1 (Config error only), Exit 2 (Git error after retries/timeout), Exit 70 (Render/Python exception), Exit 75 (Busy lock / skip).
2. **Git Timeout & Error Handling**:
   - Update `src/rebalance/lib/git_ops.py` to catch `subprocess.TimeoutExpired` / `OSError` in `publish_git_paths` and return `git_error` + `pending=True`.
   - Add configurable timeout (default 120s, env `REBALANCE_GIT_TIMEOUT`) for `publish_git_paths` and `git_pull_rebase_safe`.
3. **Timezone Fallback**:
   - In `src/rebalance/ingest/pulse.py:965`, remove `or "UTC"` so `_resolve_timezone` correctly falls back to `local_tz()` (America/Los_Angeles).
4. **Doctor Exit 75 Handling**:
   - In `src/rebalance/doctor.py:1269`, treat status `75` as a non-failing skip state (`idle, skipped (75)`).

### Phase 2: Jitter & Namespace Partitioning (Future PR)
- Bounded jittered retry (≤ 3 attempts, 2–20s) and per-device deterministic stagger delay.
- Disjoint namespaces (`devices/<id>/live-pulse.md`).
- Reader aggregation `fleet_view()` and deprecation of committing `latest.json`.

### Phase 3: Multi-Dimensional Liveness (Future PR)
- `devices/<id>/status/<job>.yaml` and collector mirroring.
- `pulse_health.py` `ALIVE_NOT_PUBLISHING` state.


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
