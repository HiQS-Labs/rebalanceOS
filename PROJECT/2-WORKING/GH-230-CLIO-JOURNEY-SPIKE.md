---
title: CLIO journey replay on XYZ Forge
status: In progress
created: 2026-09-16
updated: 2026-09-16
owner: Codex
goal: Test task-start detection and evidence-linked timelines without changing capture.
gh_issue: 230
source: https://github.com/HiQS-Labs/rebalanceOS/issues/230
doc_type: research
effort: 2
complexity: 2
risk: 2
phases: 3
branch: feat/clio-epic-plan
reversibility: Easy — read-only replay and disposable private projections; no source migration
---

# CLIO journey replay

## Status

| What was just completed | What's next |
|---|---|
| Agy approved the plan; scoped document checks passed | Implement Phase 1 bounded replay, then inspect private previews |

Parent: https://github.com/HiQS-Labs/rebalanceOS/issues/210.
Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/230.
Recon: [source map](../4-MISC/GH-230-RECON.md).

## Table of contents

- [Phase 0 - Prior Art Review](#phase-0---prior-art-review)
- [Phase 1 - Bounded technical spike](#phase-1---bounded-technical-spike)
- [Phase 2 - Comparison and decision](#phase-2---comparison-and-decision)
- [Scope, risk and review](#scope-risk-and-review)

## Phase 0 - Prior Art Review

**Goal:** Ground a minimal replay in existing capture, persistence and synthesis.

- [x] Trace CLIO capture → JSONL → SQLite → consumers; record contracts and unknowns in recon map.
- [x] Inspect related issues/PRs and source across src, utils and HiQS before adding a plan.
- [x] Record operator choices: dynamic start hints, last seven days of XYZ Forge, Terra summaries
  within existing limits, compare separate chats and connected issue journeys.
- [x] Agy approves the committed plan through relay-xyz (maximum three review rounds).

Findings: SQLite ingestion already exists. Keep the JSONL writer and current prompt-note exporter.
The existing daily synthesis has a two-hour/16-prompt input and a daily-note output, so cannot simply
be invoked as a seven-day journey replay. Extend source-owned read helpers and the guarded synthesis
boundary only where necessary; no parallel writer, cloud client, database, daemon or semantic index.
Semantic search cannot establish temporal/causal joins; 3-Eyes is parked and out of scope.
The graph/MCP tools are unavailable here; source recon used file reads, not private activity queries.

### Phase 0 QA

- [x] Source claims checked against committed base; runtime unknowns remain explicit.
- [x] Scoped PDDA frontmatter, status-table and roadmap-coverage checks pass;
  Agy receipt has a valid verdict and driver exit.

## Phase 1 - Bounded technical spike

**Goal:** Reconstruct a private, source-linked timeline from nonempty existing CLIO history.
Timebox: two hours of implementation/replay after plan approval; stop and report gaps at the cap.
The current delivery is plan/QA only; this checklist defines subsequent implementation.

One ordered execution sequence:

1. Freeze `as_of_utc` at run start and window `[as_of - 7 days, as_of)`. Resolve the current CLIO
   source with the existing resolver and copy a stable, complete-line prefix into gitignored private
   scratch (0600). Record prefix byte count/hash; live append growth is allowed, prior-byte mutation
   is not. Cap scan at 100 MB and 10,000 retained rows; report cap hit as incomplete, never silently
   call a truncated tail a seven-day dataset. Record malformed, excluded, missing-session/device,
   and unresolved-repo counts. No nonempty eligible data → coverage blocker, not success.
2. Resolve canonical `HiQS-Labs/XYZ-forge` membership from explicit qualified references or verified
   checkout remote mapping. Do not guess from clone basenames. Use JSONL as frozen capture evidence;
   read existing SQLite GitHub facts through `db_connection_readonly`, with bounded queries (1,000
   per page, 10,000 total), source timestamps and freshness recorded. No refresh/schema/cursor writes.
   Export facts once to the private replay input; unavailable sources produce visible gaps.
3. Implement one opt-in replay entry under `utils/CLIO/` with pure grouping/render helpers, reusing
   `rebalance.lib` time/JSON/redaction helpers and source-owned CLIO normalization. Add a bounded
   source-owned reader only if needed; do not alter the existing daily reader's behavior. Use
   `(source fingerprint, line ordinal)` for replay evidence IDs, not unstable packet positions or
   replacement DB IDs. Persist source IDs separately. Order by UTC timestamp and source ordinal.
4. Feed one prompt at a time. Direct `/start-task` and `/express` commands are strong start hints;
   hotfix/start words require action-request context. Quoted examples, questions, negations such as
   "do not start", and hypothetical requests are not automatic starts. Unknown phrasing abstains.
   Each accepted start opens a candidate journey, not a completed task. Another start in the same
   session opens a new segment; subsequent prompts attach only within that session until another
   start. Orphan prompts stay unassigned. Missing session IDs are not all grouped together.
5. Produce A: separate `(device, agent, session, start)` segments. Produce B: an issue-linked parent
   view of those SAME segments, only when a unique explicit canonical repo+issue reference matches.
   Preserve all child timelines and provenance. Multi-issue prompts stay ambiguous unless membership
   is explicit; no transitive merging merely through a bridging prompt. Missing device is labeled
   unknown, not invented. A completed issue referenced again is a new attempt under the same parent,
   not evidence the previous attempt continued. No cross-device rows → that behavior remains untested.
6. Attach recorded issue/PR creation, closure, merge and checks using explicit artifact links.
   Distinguish `intent`, `recorded event`, `possible association`, and `unknown`. Branch snapshots mean
   "observed", not "created". A request to run a relay/marathon is intent; add execution outcomes only
   after verifying authoritative XYZ artifact/receipt contracts. Missing contracts stay gaps in this
   spike, rather than triggering collector work. Start decisions use no future prompts/events. Current
   GitHub snapshots are retrospective evidence, NOT a proven historical stream; record both event
   and fetched times and do not claim online detection of facts before they were available.
7. Write deterministic A/B private Markdown previews plus machine-readable evidence/membership and
   coverage records. Same frozen inputs/config produce identical evidence timelines (model prose is
   excluded from byte-equality checks). Use a dedicated output directory outside the vault, no existing
   prompt/daily notes. Atomic replacement only after validation; preserve prior output on failure.
8. Add optional Terra narrative AFTER grouping. Reuse `daily_work_synthesis.py` guarded execution,
   redaction, citation validation and shared budget/receipt ownership—not a direct `invoke_terra`
   call. Inspect `run()` before choosing the smallest packet/output injection seam; preserve daily
   defaults, lock, reservations, failure accounting and receipts. Read current approved configuration;
   never use `force` or a fresh scratch budget to bypass limits. Maximum two calls for the spike,
   within remaining shared daily allowance and existing packet/token/time ceilings; zero automatic
   retries. If that seam cannot safely support separate output within the timebox, retain deterministic
   previews and report Terra integration blocked. Raw logs never enter a tool-enabled model session.
   Only scrubbed, repo-scoped excerpts needed for selected journeys leave the device. Operator has
   approved this bounded use; absent safe config or limits → no call. Model adds no links or facts.

### Phase 1 QA

- [ ] Synthetic nonempty fixtures cover positive start commands, negation/quotes, no-marker continuation,
  repeated starts, missing metadata, duplicate events, same issue number in different repos, multi-issue
  bridge, issue reopening/new attempt, out-of-window rows, malformed input and unavailable DB.
- [ ] Demonstrate red controls: enable bare-number joins → cross-repo test fails; treat intent as
  completion → evidence test fails; append future start → prior start decision unchanged; corrupt
  source fingerprint/empty eligible input → run refuses a success result; failed render preserves sentinel.
- [ ] Freeze config and expected synthetic results before replay; synthetic injections live in separate
  fixtures and are excluded from historical counts. Verify no source/cursor/DB/scheduler changes.
- [ ] Run targeted CLIO/daily synthesis tests, then repo-required doctor and pytest gates for any code
  changes; record failures/skips honestly. No operation of parked 3-Eyes. Capture stdout/exit codes.
- [ ] Run both grouping modes on identical nonempty input; counts reconcile and events count once per
  view even if displayed under multiple references. Every factual timeline item has a source ID/link.
- [ ] Terra mocked tests cover exhausted budget, unknown citation, timeout, missing usage, redaction,
  output failure and preservation of daily behavior before any approved live model invocation.
- [ ] Write observed spike findings and blocked seams back into this plan before marking phase complete.

## Phase 2 - Comparison and decision

**Goal:** Decide whether a small journey viewer is useful, not declare predictive accuracy.

- [ ] Publish a sanitized `TESTS-RESULTS/YYYY-MM-DD+GH-230/` receipt with source commit, frozen window,
  configuration, replay command, synthetic fixtures, console checks and primitive aggregate records.
  Keep actual prompt text, device paths and identifying session IDs private. Use opaque IDs in public
  counts; disclose that private semantic correctness cannot be independently reproduced publicly.
- [ ] Present both private views for operator inspection, including false starts, wrongly joined work,
  missed continuations and useful issue-linked context. Show up to ten detected starts in chronological
  order plus ten non-starts where available; fewer examples are reported explicitly. Human review is
  required for correctness labels; Terra/Agy do not supply ground truth. No response means usefulness
  remains unmeasured, not a pass or blocker to recording the technical result.
- [ ] Decision rule frozen before replay: any false completion, cross-repo join, privacy/budget bypass or
  source mutation blocks graduation. Passing mechanical checks permits a private prototype only.
  Default to separate journeys; enable connected view as an optional lens if operator finds its context
  useful without misleading joins. No accuracy superiority or statistical significance claim from this
  convenience sample; a scored comparison requires SOP campaign/paired analysis and human labels.
- [ ] Update #230 and parent #210 with outcome, limitations and recommended next action. Obsidian
  publishing requires a selected destination and verified exclusion from re-ingestion; no live publish,
  scheduling or auto-created GitHub epic in this experiment.

### Phase 2 QA

- [ ] All reported totals recompute from sanitized primitive records; empty/synthetic data are distinct.
- [ ] Explain missing cross-device and relay/marathon coverage, snapshot history limits and capture filters.
- [ ] Final code review uses Agy relay, at most three rounds, before a ready implementation PR.
- [ ] Mark implementation/merge/deployment separately; never close #210 as a consequence of this spike.

## Scope, risk and review

Ponytail: one stdlib-oriented replay script plus focused tests, target <=300 new production lines for
the spike; no generic event platform. If existing boundary reuse needs broader refactoring, stop and
record it rather than building a parallel system. Follow DRY/SOLID proportionally under AGENTS.md.
Debug-mantra is the execution-time protocol: reproduce, trace failure, falsify, retain breadcrumbs.

**Bet:** start hints plus explicit artifact identities provide a useful history without training a model.
Failure mode: scattered prompts and missing capture metadata leave too little reliable linkage.
**Easy undo:** stop the opt-in script; preserve original capture/index/notes. No migration to undo.
**Privacy is not reversible:** minimized Terra egress cannot be recalled; shield is the existing approved
privacy/budget boundary and scoped packet. Tripwire: any raw secret/unknown evidence/budget bypass
blocks the call or output. No permissions or spending limits broadened by this plan.

Ratings live in #230: `rated 60/25/50/65`; no task-rating DB exists in this clone, so no new ledger is
installed. Related work #141/#139/#199 is prior art, not evidence of a recurring journey defect.
Recent-vs-prior 14-day trend remains unknown. PDDA effort/risk fields are separate planning metadata.
No existing plan/PR duplicates this journey replay in the searched issue/PR inventory.

Review inputs are public-safe docs/source only. Agy must check identity, temporal leakage, live-state
preservation, Terra shared guards, phase bounds and falsifiable tests.

Review: Agy `gemini-3.1-pro-high` approved in one round, driver exit 0 (2026-09-16 UTC).
[Verbatim review](../../relay-system/2026-09-16/gh230-plan.md), committed at `4acc673`.
No requested changes; post-review edits only record status/evidence, not the protocol.
The Agy shim fixture suite returned exit 0 (62 pass / 0 fail); vendored harness lacks `validate.sh`,
so no full harness validation is claimed. Scoped PDDA checks returned zero errors/warnings.
Runtime doctor, full application tests and historical replay are not run: this is a documentation-only
delivery, not a verified implementation. No private prompt text entered the review.
