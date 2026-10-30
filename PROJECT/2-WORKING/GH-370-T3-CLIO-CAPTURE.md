---
title: T3 Code prompt capture in CLIO
status: planning
created: 2026-10-30
updated: 2026-10-30
owner: Codex
goal: Capture human T3 submissions across providers using CLIO's canonical writer.
gh_issue: https://github.com/HiQS-Labs/rebalanceOS/issues/370
effort: 2
complexity: 3
risk: 2
phases: 1
---

## Status

| What was just completed | What's next |
|---|---|
| Issue and isolated full clone created; canonical capture owner located. | Complete recon and obtain independent plan approval. |

## Quad Concepts
- Missing T3 coverage → read durable human submissions across providers.
- Lost provenance → preserve IDE, provider, UTC time, thread and project metadata.
- Duplicate retries → stable source identities through the existing CLIO writer.

## Phase 0 - Prior Art Review

Base: `f0819314c078f58e9d51b6ccd698c76b700ec1cc`. CLIO's canonical source is
`utils/clio-capture/`; its standalone store already owns normalization, identity,
durable pending receipts, config and scheduled exports. Native Codex/Agy tailers
and Claude hooks do not provide provider-independent T3 provenance. Extend this
standalone subsystem; the Rebalance index registry consumes its compatibility
export and is not the capture owner. No new collector, daemon, script or plist.

T3 source inspection: `orchestration_events` contains `message.updated` payloads
with `createdBy`, `creationSource`, `id`, `threadId`, `role`, `text`, `createdAt`.
`run.created` binds user message to provider/model; thread/project projections
contain workspace and branch. Dedicated `orchestration_v2_events` exists in some
versions; support only inspected layouts and refuse unknown schemas visibly.
Live source inspection was read-only and did not export prompt content.
The current layout uses unified `orchestration_events` plus V2 projections;
scope support to that layout, not the unused dedicated V2 event table. Accept
only `createdBy=user` with `creationSource=web|mobile`; desktop wraps web.
T3 contracts distinguish these from `server|provider|mcp` automation.

GitHub open PRs in both current and predecessor repos contain no CLIO/T3 work;
T3+CLIO issue searches found no existing implementation. Local prior-art script
is absent; manual searches used. Active CLIO #368 concerns native Codex capture,
not this source. Recurrence windows 2026-10-17–30 and 2026-10-03–16: no distinct
T3 capture incidents found in targeted searches; trend unknown, not zero.

## Solution fit and implementation

Outcome: all human text prompts entered into the configured local T3 environment
reach the activated CLIO SQLite history with existing fields plus `extras.ide`,
provider instance/model and T3 message identity. Include one-word prompts.

Smallest viable bet: add opt-in `configure-t3 SOURCE` and `capture-t3` commands to
`clio-store.py`; invoke configured capture from its existing `scheduled-export`
path. Register source and initial high-water mark explicitly, then scan bounded
event batches, maintaining a private sidecar cursor under the CLIO DB directory.
Use SQLite `mode=ro` for T3. Never open T3 via CLIO's writable database gateway.
Use existing `capture()` and stable T3 message source IDs; advance only after the
writer durably accepts rows. Serialize cursor operations with existing lock().
Source identity is explicit configuration; refuse replaced/regressed sources.
Capture original message text, not provider transcript transformations; exclude
import-prefixed threads/messages, non-user creators, subagent lineage, and
scheduled/task creation sources based on inspected T3 contracts. Resolve provider
from the corresponding run rather than the thread's mutable default.

Existing alternative: provider hooks alone miss providers and IDE attribution.
T3 app-specific hooks would require an application rebuild and separate write
integration, while existing durable events already carry the required input.

Non-goals: T3 code changes, remote-machine discovery, automatic historical import,
attachment contents, CLIO schema migration, changes to existing native capture,
fleet rollout, installing the unmerged branch, merge, or synthetic frameworks.
Independent native transcript observations may coexist; this feature guarantees
once per T3 submission on retry, not global cross-harness reconciliation.

## Acceptance and verification

1. Inspect source variants and immutable metadata; finalize exact supported layouts.
2. Extend existing `test/clio-store.py` using small synthetic T3 SQLite fixtures:
   human short/multiline text, multiple providers, automated/import exclusions,
   duplicate updates/rerun, queued capture/retry and source-regression refusal.
3. Implement reviewed helper, opt-in config and scheduled integration; preserve
   existing config and inactive default. Content-free failures must be visible.
4. Run existing CLIO store/runtime/capture/exporter suites and inventory/gateway
   ratchets. Run repository-required pytest and doctor, recording environmental
   limitations separately. No new test runner or gate.
5. Smoke CLI configure/capture and rerun on disposable fixture data, retain raw
   evidence under `TESTS-RESULTS/2026-10-30+GH-370/`, then independent final QA.

Red control: new fixture assertions must fail before implementation. Preserve
nonempty fixture prompts and verify exact metadata/text, not only counts.
Rollback is Easy: remove T3 config registration to stop scans; preserve captured
history and sidecar cursor. No writes to source; existing SQLite pending spool
handles destination contention. New config must not reset an existing cursor.

## Rating rationale

2026-10-30: pri/sev/appeal/effort = 65/40/50/60. Missing cross-provider prompt
history affects recall and provenance; no demonstrated source data corruption.
User explicitly requested this work now. Neutral appeal; moderate delivery ease
from reusing store/exports, with source-version uncertainty. No user override.

## QA

Plan: pending. Final: pending. No implementation before plan approval.
