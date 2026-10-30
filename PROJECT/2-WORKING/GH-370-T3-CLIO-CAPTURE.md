---
title: T3 Code prompt capture in CLIO
status: in-progress
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
| Plan QA round 2 Approved; capture and focused synthetic cases implemented. | Run required verification, smoke and independent final QA. |

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
Capture original message text, not provider transcript transformations. Accept
only user-created web/mobile message events; server/provider/MCP historical,
scheduled and delegated input is excluded. Do not exclude a whole imported or
subagent thread: fresh direct human submissions in either remain eligible.

### Frozen source and identity contract

Supported source: unified `orchestration_events` with `application_event_version=2`
for thread events and object message payloads matching the inspected T3 contract.
Version 1 thread history is ignored; unknown (>2) thread versions stop scanning
without cursor advance. Required event columns and V2 thread/run/project
projection columns must exist. Unknown layouts refuse registration/capture.
Rows are bounded to 1000 events per invocation; additional pages wait for the
next scheduled run. Attribution queries see the same committed read transaction,
including runs committed beyond a page boundary.

Registration generates a UUID for the source, records the source device/inode,
current committed maximum sequence and its event_id, and atomically writes a
sidecar next to the CLIO DB. A repeated registration of the same path preserves
UUID/cursor; a different path requires disabling first and explicit registration.
Before each scan validate inode and the retained boundary event identity; source
replacement/regression is a visible refusal. A registered empty DB has no
boundary identity until its first page. Missing source never creates a DB.

CLIO `source_event_id` is `t3:<source UUID>:<message id>`, session_id is the
namespaced source UUID plus T3 thread ID. Extend existing identity_payload for
this producer only: identity is origin_id, source_event_id and clio_version,
not mutable observational labels or later message updates. First accepted text,
timestamp and metadata win. Existing/native producer identity stays unchanged.
The source lock serializes capture and configuration. For a known T3 record,
reuse the already committed payload or durable pending receipt before capture;
this freezes all metadata across retries, including crash after acceptance and
before atomic cursor publication. Only then advance sequence/boundary together.
Use the canonical capture/normalize/insert path; no second event writer/table.

Use message.runId to find run_id in the V2 run projection (covers steering);
fallback to matching userMessageId only when message.runId is absent. Run
modelSelection/providerInstanceId supplies model and instance, never the mutable
thread default. Resolve driver from the run's provider session when present;
otherwise keep the instance as agent identity and mark driver unknown in extras.
Missing run/instance metadata refuses that page visibly without advancing.
Missing project metadata retains the submission with empty repo/checkout/branch
and an explicit metadata warning. Current project/worktree/branch and driver
labels are observation-time metadata, explicitly marked in extras, not claims
about historical checkout state. Timestamp comes from message.createdAt.

Existing alternative: provider hooks alone miss providers and IDE attribution.
T3 app-specific hooks would require an application rebuild and separate write
integration, while existing durable events already carry the required input.

Non-goals: T3 code changes, remote-machine discovery, automatic historical import,
attachment contents, CLIO schema migration, changes to existing native capture,
fleet rollout, installing the unmerged branch, merge, or synthetic frameworks.
Independent native transcript observations may coexist; this feature guarantees
once per T3 submission on retry, not global cross-harness reconciliation.

## Acceptance and verification

1. Verify the explicit source/version/identity contract above against T3 code.
2. Extend existing `test/clio-store.py` using small synthetic T3 SQLite fixtures:
   human short/multiline text, multiple providers, automated/import exclusions,
   duplicate updates/rerun, queued capture/retry and source-regression refusal;
   steering, fresh input in imported/subagent threads, page-boundary attribution,
   unknown versions, missing metadata, projection changes between retries and
   crash after acceptance before cursor publication.
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

Plan round 1: Changes requested. All four findings accepted: steering uses
message.runId; exclusions apply per submission; explicit source UUID/boundary and
first-observation identity; exact V2 contract and missing-metadata policy.
Plan round 2: Approved. Final: pending. Implementation started after approval.

Host orchestration requires T3-managed delegated review rather than a shell
relay child. The independent review scope and three-round cap are unchanged.
