---
gh_issue: 202
source: https://github.com/HiQS-Labs/rebalanceOS/issues/202
title: "GH-202 — Claude session identity and status producer snapshot"
status: Proposed — plan written; compatibility spike and implementation not started
created: 2026-09-09
updated: 2026-09-09
owner: Codex
doc_type: architecture
goal: Publish existing session identity and status once through Rebalance for passive consumers without a parallel collector.
effort: 3
complexity: 3
risk: 3
phases: 3
reversibility: Costly — additive cross-repository contract; opt-in export and independent rollback
related:
  - https://github.com/HiQS-Labs/XYZ-forge/issues/494
  - https://github.com/HiQS-Labs/rebalanceOS/issues/150
  - https://github.com/Hypercart-Dev-Tools/rebalance-OS/issues/128
---

# GH-202 — Claude session identity and status producer snapshot

## Status

| What was just completed | What's next |
|---|---|
| Source ownership and existing reader/registry seams rechecked; producer scope separated from Flightdeck presentation. | Independent protocol review, then Phase 0 compatibility spike. No source refresh, schedule, hook or deployment has been activated. |

## Table of contents

- [Ownership and scope](#ownership-and-scope)
- [Recon Map](#recon-map)
- [Phase 0 - Prior Art Review and compatibility spike](#phase-0---prior-art-review-and-compatibility-spike)
- [Phase 1 — Publish a bounded snapshot](#phase-1--publish-a-bounded-snapshot)
- [Phase 2 — Identity enrichment and consumer handoff](#phase-2--identity-enrichment-and-consumer-handoff)
- [Rollback and completion](#rollback-and-completion)

## Ownership and scope

**Rebalance owns the existing Claude status reader and the new optional export. Flightdeck owns its adapter, aggregation and UI.** This document is canonical for the producer work previously outlined in XYZ-forge's `GH-494-SESSION-CONTEXT-PLAN.md`; that document remains the consumer plan. Neither is blocked on GH-201's GitHub efficiency work. GH-199/PR-200 owns the separate first-prompt capture defect; this work must not reimplement it.

This is a narrow continuation of the [archived predecessor plan](../4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/GH-128-CC-CLOUD-JOBS-INGEST.md), not a replacement collector. Its deferred raw-table/ranking promotion stays deferred. A regenerable versioned file serves the present passive-consumer need without a new database or ranking influence. The current repository's issue 128 is unrelated; use the fully qualified predecessor link above.

The bet is that the existing authenticated session endpoint continues to expose the observed Remote Control session facts. That endpoint is a compatibility risk, not a promised public API. Missing support disables/degrades this optional export; it does not stop other Rebalance sources or justify an alternate collector.

Scope: session title, source-qualified identity, optional exact local/remote mapping, repo/branch, connection, worker/status fields, observation time and coverage. Initial intent/latest prompt preservation and issue-card rendering remain Flightdeck responsibilities using existing CLIO data. Do not infer completed progress from a running worker, connected client, prompt, or timestamp.

Non-goals: new transcript crawler, hooks, remote session control, LLM summarizer, vector embedding, PR/GitHub enrichment fetches, cross-device sync service, generic plugin framework, new scheduler/supervisor, UI or Swift work. 3-Eyes remains stood down under AGENTS.md; do not reactivate or build a replacement. No experimental harness CI/CD wiring.

## Recon Map

Source reviewed at Rebalance HEAD `0bffc4dab79da4a2a13ecd605af9798181a76bc9`; re-anchor before execution. Graph generation `2026-09-02T03:54:57Z` is older than some working-copy files, so direct source reads supply material claims. Earlier status research and its sanitized receipt are recorded under [XYZ-forge #494](https://github.com/HiQS-Labs/XYZ-forge/issues/494#issuecomment-5594212850); this planning task did not repeat live collection.

| Existing seam | Read/write contract and gap |
|---|---|
| `src/rebalance/ingest/claude_cloud.py:47` `_get_token` | Existing keychain then credential-file read; retain auth ownership, never publish credentials. Keychain call has its own timeout that must count toward a whole-cycle deadline. |
| `claude_cloud.py:77` `_fetch_raw` | Existing paginated HTTP read returns a list, capped by record count. It does not expose termination/coverage metadata; repeated cursors or empty pages need a page/deadline bound independent of row count. Extend this fetch implementation rather than copying it. |
| `claude_cloud.py:101` `normalize` | Emits ID/title/status/worker/repo/event facts, but drops raw connection_status. Project an allowlisted snapshot; do not export the whole normalized object including summaries by default. |
| `claude_cloud.py:197` `sessions_for_day` | Selects creation date; returns empty on auth/fetch failure. Keep legacy grade/report behavior compatible, but do not use this wrapper to produce a completeness claim. |
| `src/rebalance/ingest/index_ops.py:2130,2240` | Existing `claude_cloud` registered derived scan, excluded from all, currently returns grade without persisting rows. Extend this adapter for opt-in export, leaving dispatch and default behavior intact. |
| `src/rebalance/ingest/config.py:1362` | Existing ranking flag is default-off. Export enablement must be independent; writing a snapshot must not enable ranking or change source inclusion in all. |
| `src/rebalance/ingest/clio.py:99` | Consumes timestamp/session_id/prompt from CLIO's prompt log. It is not a native Claude transcript reader. Adding bridge parsing here cannot recover records absent from that input. |
| Native Claude metadata (prior research) | Explicit bridge-session records map local UUID to remote session ID; exact matches were reported for two sessions, another remained unmatched. This is evidence the metadata exists, not evidence an existing producer exports it. |
| `utils/claude_cloud_daily_grade.py`; `scripts/cc_cloud_jobs.py` | Daily note exporter and older POC exist. GH-150 already tracks duplication. Do not add a third fetch implementation or migrate the POC wholesale. |

Current flow: Claude session service → canonical reader → normalization → daily grade/optional ranking. Proposed additive flow: same reader → source-owned export via existing collector adapter → local snapshot → passive consumer. CLIO remains an independent prompt source; exact IDs can connect records only when supported by producer evidence.

Unresolved seams: configured scheduler/runtime checkout, existing atomic-write/lock helper, producer-owned metadata parser, endpoint offline/resume semantics. Phase 0 must read and name these exact paths before their integration. No whole-machine compatibility claim is made.

## Phase 0 - Prior Art Review and compatibility spike

**Goal:** Prove the affected read contracts and identify safe existing integration points before writing runtime behavior. Timebox: 1–2 hours after protocol review; stop and record blockers at the limit.

1. Check current and predecessor PRs, GH-150, CLIO capture work, and existing reader/collector consumers for overlap. Re-read the helper call paths, including failure and write paths. Review the existing configured scheduling mechanism read-only; identify one opt-in invocation through the collector registry and the runtime checkout it uses. Read-only metadata discovery must establish whether an existing producer already parses title/bridge events. Record exact seams or explicit absence/unknown here. Extend existing layers; do not create alternate collection or scheduling machinery.
2. Use the current reader's auth path for a bounded, explicitly invoked read-only probe after protocol review. No PR enrichment, token refresh/login, hooks, source DB writes or scheduler activation. Bound auth + DNS + requests + decoding to a 25-second whole-cycle deadline (including at most 10 seconds auth and three requests of at most five seconds, reduced by remaining budget). Use a cancellable existing execution boundary if socket timeouts do not bound DNS; no lingering child process. Capture only a sanitized schema/status receipt; do not commit session titles, real IDs, personal repo names, tokens or prompt bodies. Offline/auth failure means unverified, not empty.
3. Build fixtures in a proven temporary root for versioned export and consumer compatibility: old active session, recent idle/disconnected session, unknown enums, malformed data, empty complete response, capped/repeated-cursor/empty-page traversal, page failure, and same-repo distinct sessions. Read live configuration without calling migration/writer-bearing helpers; use copied/synthetic config for headless scenarios. No production database is needed for this feature. If any DB compatibility check is necessary, use the canonical read gateway without schema initialization or a synthetic disposable store.

### Phase 0 QA

- [ ] Write findings back into the Recon Map: exact scheduler, locking, metadata reuse paths and their read/write contracts; unresolved capabilities are marked unavailable.
- [ ] Retain a nonempty sanitized fixture set and protocol/receipt in `TESTS-RESULTS/2026-09-09+GH-202/`; no measured benefit or compatibility claim without retained evidence.
- [ ] Whole-cycle timeout and nonmutation checks run; a deliberately misdirected write is rejected against a sacrificial fixture, never against production.
- [ ] Prior-art/DRY/SOLID check confirms this extends the existing collector. No parallel fetcher, database, supervisor or 3-Eyes integration.
- [ ] A blocker stops the dependent phase. Missing identity export can defer identity enrichment without hiding otherwise available remote sessions; absent safe scheduling leaves manual-only export explicit.

## Phase 1 — Publish a bounded snapshot

**Goal:** An optional versioned snapshot contains existing session facts, explicit incomplete/error states, and safe per-row freshness.

4. Extend the canonical fetch implementation to return internal page/coverage details while preserving existing list-returning callers through a compatibility wrapper. Explicit page count, row limit, repeated-cursor detection, response byte limit and the Phase 0 whole-cycle deadline must bound the actual fetch. No immediate retry loop; next attempt belongs to the existing scheduler. Preserve legacy daily grading and candidate enablement defaults. Snapshot selection includes active sessions regardless of creation date and other sessions with events in the last two hours; selection happens after bounded retrieval, and a capped upstream result remains partial.
5. Project one `schema_version: 1` envelope with source instance/scope identity, attempted_at, last_complete_success_at, coverage (complete/partial/unavailable), coverage_reason (exhausted/cap/fetch_error/auth_unavailable/invalid), pages_read, records_read and sessions. All timestamps UTC. Each row has remote ID, optional repo/branch, title, raw status/status_bucket/worker_status/connection_status, observed_at, created_at and last_event_at. Preserve unknown raw enums but map their display interpretation to unknown. Observation time means a successful row read; event time means last reported activity. Do not interchange them. Missing repo stays unassigned, not guessed from title. Exclude summaries, message bodies, credentials and raw API payloads. Configured paths and account/source-instance scope stay local, not machine-hardcoded in the contract.
6. One export writer, invoked through the existing `claude_cloud` collector adapter when explicitly enabled, atomically replaces the configured file (private directory, user-only file, temporary sibling + flush/replace). Lock the read/merge/publish transaction using the verified existing helper or a minimal standard-library lock; bounded lock contention yields an explicit skipped attempt. Complete success replaces the selected set and advances last_complete_success_at. Partial success updates observed IDs and retains unseen historical rows without refreshing observed_at. Total failure retains previous rows and records error; failed file replacement leaves the previous complete file, whose age exposes the failure. Account/source-instance mismatch never merges histories. Bound retained output to 300 rows and 4 MiB; deterministic oldest historical eviction reports omitted-count/partial coverage, never fabricated session closure. An unknown number of upstream omissions remains unknown, not zero.
7. Extend existing configuration/health reporting with export enablement and path plus attempted/success times, coverage and sanitized error code. Dry-run performs neither network nor export writes. Keep export off by default, independently of ranking, and retain included_in_all=False. Integrate a 120-second start-to-start cadence only through the Phase 0 verified facility; do not create another scheduler or bypass the registry with a request-side leaf call. If that cadence is unavailable, manual invocation remains useful but the near-real-time target is unfulfilled.

### Phase 1 QA

- [ ] Run focused fixtures for existing grade/ranking compatibility, selection, complete-empty versus error, partial retention, auth/account change, byte/row/page caps, concurrent/crashed publication and missing source.
- [ ] Mutate export to call the date-filtered wrapper: old-active presence assertions must fail. Mutate error-to-empty and retained-row timestamp refresh: coverage/freshness assertions must fail.
- [ ] One writer/one fetch implementation; no secret/raw payload logging. Disable flag proves zero new source calls/writes and preserves old behavior.
- [ ] Observability names last attempt, last complete success and per-row observation separately; an empty response is not accepted after a parse/auth failure.
- [ ] Run required Rebalance focused/full tests and doctor in an isolated full clone before runtime completion; record pre-existing failures separately. No new CI/CD wiring for this experimental harness.

## Phase 2 — Identity enrichment and consumer handoff

**Goal:** Export exact identity where existing producer evidence supports it and give passive consumers a tested, replaceable contract.

8. If Phase 0 identifies an existing metadata producer seam, extend it narrowly to project native bridge records into optional mappings: local session ID + device/source namespace, remote ID, producer source and mapping observation/provenance. Retain alias history only as bounded evidence; ambiguous resumes/conflicts never become unique mappings. CLIO is canonical here, with XYZ-CLIO a downstream copy only if actual CLIO code changes; in that case follow the existing sync path and compatibility tests rather than independently editing both implementations. If no existing seam is available, ship remote identities with identity_coverage=partial and capture the missing producer extension as a follow-up requiring justification. No consumer transcript scanner, title matching, repo-only merging or guessed UUIDs.
9. Publish synthetic contract fixtures and consumer rules: source-qualified IDs, exact joins only, unmatched sessions remain visible, unknown schemas fail gracefully, no network call from reading the file, and no guarantee that one record equals one unique local agent without a mapping. After 180 seconds from observed_at, a consumer must display status as historical/unknown even from a last-good browser cache. Connected, working, idle, issue linkage and attested progress are distinct facts. Consumers own title/initial intent/latest prompt presentation; the producer does not summarize prompts or invent issue associations. Flightdeck changes stay under XYZ-forge #494.
10. Run the existing manually invokable experimental harness against synthetic producer files and a downstream passive adapter fixture; use temporary fixture storage, not production database writes. Then conduct a three-cycle opt-in pilot after protocol review and configuration is prepared. Target 120-second production + at most 25-second cycle + 30-second client polling + 5-second local overhead = predicted <=180 seconds on an awake machine/visible client. Measure source-state-change-to-display where an actual transition is observable; otherwise mark that measurement unverified. Test offline expiry/resume, auth failure, partial traversal and unmatched session visibility. Stop after three cycles; a failed freshness/identity target disables the pilot and yields a concrete follow-up, not indefinite retries.

### Phase 2 QA

- [ ] Exact mappings coalesce only the right fixture records; unmatched/ambiguous records survive and count coverage is partial. Repo-only join mutation must fail.
- [ ] Snapshot reads work without Rebalance installed or network access in the consumer. Adapter absence/failure does not suppress other sources.
- [ ] A frozen running badge must fail a fake-clock stale test; timestamps cannot become fresh merely because the file was rewritten.
- [ ] Document whether optional local identity enrichment shipped or remained unavailable. Do not claim complete identity coverage or all-device visibility from a bounded sample.
- [ ] Retain sanitized pilot/provenance and actual outcomes, obtain independent runtime review, and update this plan/issue before marking complete. Plan approval alone is not runtime proof.

## Rollback and completion

Cross-repository contract changes are Costly. Shield: independent export flag, no DB migration, unchanged ranking defaults, optional consumer adapter. Tripwires: false identity merge, stale state presented live, leaked payload/credentials, old grading regression, concurrent file corruption or missed measured deadline. Disable the export invocation/consumer adapter at the first tripwire; preserve source logs, credential storage and previous evidence. The snapshot is regenerable; no destructive source cleanup or remote deployment is required.

Use debug-mantra for failures: reproduce, trace the failing path, falsify the hypothesis, cross-reference every breadcrumb. Stop conditions: 1–2h spike, 25s producer deadline, three pages/300 fetched records, bounded bytes, no nested retry, three-cycle pilot. If any bound cannot be enforced with the existing execution primitives, record the missing capability before expanding scope.

Done means the producer contract and its limitations are verified and documented, and a passive fixture consumer demonstrates integration. Full Flightdeck UI acceptance remains in its own repo. This plan does not claim tests, collection, scheduling, deployment or independent review have already passed.
