---
title: CLIO — capture the first prompt of new Codex sessions
status: Captured
created: 2026-09-08
updated: 2026-09-08
owner: Codex
gh_issue: 199
goal: Capture newly submitted root-session prompts before the first polling tick without importing history or child-session context.
context_tags: [clio, capture, correctness]
effort: 2
complexity: 2
risk: 2
phases: 1
---

# GH-199 — CLIO first-prompt capture

## Status

| What was just completed | What's next |
|---|---|
| Producer ownership confirmed; existing tailer and failure traced. | Promote the grounded repair plan, then Codex plan QA. |

Canonical issue: https://github.com/HiQS-Labs/rebalanceOS/issues/199.
RebalanceOS owns CLIO; XYZ-CLIO receives the matching downstream commit after the
canonical fix. No new subsystem or live installation is requested.

## Recon Map

Base: `0bffc4dab79da4a2a13ecd605af9798181a76bc9`. Verify tier, graph generation
2026-09-02T03:54:57Z. Shell/doc source reads cover the material claims; INSTALL.md
metadata changed in the primary checkout, so that checkout's uncommitted work is
preserved. This fresh clone uses committed origin/development. No primary edits.

Entry: the documented one-minute launchd schedule calls `clio-codex-tail.sh`.
`state_lookup` checks path/inode/byte cursor; every unseen file defaults to EOF and
continues, regardless of whether capture was already running. `extract_rows` then
reads new terminated records with nearest session metadata; the shared writer in
INSTALL.md filters/normalizes and deduplicates `session_id:timestamp` before append.
Only writer acceptance advances `state_update`; downstream exporter/index/Flightdeck
consume that existing log. Changing their readers cannot recover an uncaptured row.

The installed tailer and canonical tailer have matching SHA-256
`9ae347043f9890b0a01c7f0f6f5c4e1a9e93c72a42fb526b381faff8b9349b96`.
A September 8 first prompt is present in a root rollout and absent from CLIO; later
prompts are captured. Its first-discovery offset was not logged. EOF loss is strongly
supported, not historically proven. The synthetic first-poll regression will prove
the code defect. Tests currently assert the undesired behavior for unseen files.

Source file identity matters: first session metadata in observed child rollouts
contains `source.subagent` and `parent_thread_id`; inherited user events have new
timestamps and later metadata switches to the parent. Filtering only the nearest
metadata, or blindly enabling backfill, would log copied context as fresh input.

Knobs: CODEX_HOME, CLIO_TAIL_BACKFILL, persisted cursor/context, newline completion,
inode/size changes, writer lock/exit, source metadata and timestamps, minimum prompt
length. Debugger is unnecessary for this straight-line shell branch: fixture input,
cursor and JSONL output provide a deterministic differential.

Alternatives falsified/bounded: dashboard selector defects were repaired separately;
current writer filters accept the missing request; historical first-poll telemetry
is absent; child inherited input disproves unconditional read-from-zero as sufficient.
A rolling age heuristic would miss sessions after downtime. A persistent capture
boundary is independent of polling delay and source file creation time.

## Assessment

2026-09-08: rated 85/80/50/70 (priority/severity/neutral appeal/cheapness). Silent
loss in the derived prompt log damages audit and task continuity; original rollout
remains recoverable. One observed first-prompt incident. Recent history windows:
2026-08-25–09-08 and 08-11–08-25; related #139 is implementation and #141 indexing,
not separate incidents. #120 records a different exporter delivery loss in the prior
window, not proof of this root cause or an increasing rate. Trend remains unknown.
No user rating override. This repo's CLI mirrors ROADMAP.md (sync/list only), so
its existing rated pointer is the write authority; no new rating tool is installed.

## Phase 1 — surgical repair

1. Extend the existing fixture harness: complete a new root's first prompt between
   polls; expect one exact JSONL row and no duplicates. Run against the baseline
   and retain the failure under TESTS-RESULTS/2026-09-08+GH-199.
2. Store one capture-start timestamp header inside the existing cursor state under
   the tailer lock. Preserve it across state_update. Initialize even when the
   sessions directory is absent. Existing legacy cursor rows remain valid; on
   upgrade establish the boundary now, without replaying previously skipped history.
3. For unseen files, read from byte zero and filter complete prompt timestamps
   against that persisted boundary; explicit backfill bypasses the boundary only
   for unseen files. Known files keep the existing cursor/retry path. First run
   imports no historical complete prompts; events submitted after startup survive
   any polling delay. Invalid timestamps do not become newly submitted prompts.
4. In the existing extractor, inspect the file's first session metadata independently
   of mutable nearest-event context. Exclude files marked as child/subagent even if
   later metadata switches to parent; no second writer or parser module. Preserve
   genuine root resumes and the existing per-event context behavior.
5. Verify initial history exclusion, completed/partial first prompt, absent/empty
   sessions tree, delayed discovery, legacy cursor preservation, child replay and
   second-tick child appends, backfill, rotation, overlap, and append-lock retry.
   Assert source bytes unchanged and make both new positive and exclusion gates
   fail under their corresponding baseline/mutated behavior. Run all four CLIO
   suites, repo-required pytest/doctor and targeted governance checks; disclose
   unrelated failures without changing unrelated components.
6. Update install semantics/version/changelog, commit final evidence and get Codex
   relay approval. Open the canonical PR to development. Copy the tested tailer
   and harness plus the matching documentation paragraph to XYZ-CLIO; preserve
   its independent install-path fixes. Test its four suites, then direct commit
   and push to its default branch as authorized. No downstream PR ceremony.

## Boundaries and rollback

Easy: retain the existing writer, IDs, log format and consumers. State header is
ignored by legacy per-path awk lookups, so rolling the script back preserves rows
and cursors (and restores the old first-discovery behavior). State writes remain
atomic through state_update. No automatic recovery/backfill of the historical
missing prompt, no installed-hook deployment, no scheduler edits, no dashboard
collector. Tests use synthetic prompts and isolated homes; no private content in
commits. Existing timestamp precision/dedup policy stays unchanged.
