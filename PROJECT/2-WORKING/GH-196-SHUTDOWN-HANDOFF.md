---
gh_issue: 196
source: https://github.com/HiQS-Labs/rebalanceOS/issues/196
title: Shutdown MVP — reviewed end-of-day triage and next-session continuity
status: In Progress (Phase 3 — QA, dogfood, and handoff)
created: 2026-09-07
updated: 2026-09-08
owner: Maintainer
doc_type: feedback
rating: pri/sev/appeal/effort 70/55/50/55 · calc 230
effort: 3
complexity: 3
risk: 3
phases: 4
goal: >
  Shutdown MVP: end-of-day repo triage and next-session continuity alongside daily.
  Produces a compact handoff relating PRs to project phases, deliberate deferrals,
  remaining tests/reviews, and one concrete next-session nudge per project.
non_goals:
  - Comprehensive read-event history, ignored-directory journaling, or remote-only checkout control
  - Stopping applications or shutting down the computer
  - Automatic dirty-work commits or autonomous unreviewed merges
  - Whole-disk scanning, cloud publication, or reactivating 3-Eyes
---

# Shutdown MVP — execution plan

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 & 2 implemented; A1–A12 acceptance tests verified; Agy final implementation QA Approved; version bumped to 0.85.0. | Push task branch and open implementation PR targeting development. |

## Table of contents

- [Phase 0 — Prior Art Review and contract freeze](#phase-0--prior-art-review-and-contract-freeze)
- [Phase 1 — Extend the existing scanner](#phase-1--extend-the-existing-scanner)
- [Phase 2 — Reviewable handoff and optional enrichment](#phase-2--reviewable-handoff-and-optional-enrichment)
- [Phase 3 — QA, dogfood, and handoff](#phase-3--qa-dogfood-and-handoff)
- [Acceptance matrix](#acceptance-matrix)
- [Risks, non-goals, and finish line](#risks-non-goals-and-finish-line)

## Problem and product boundary

The operator loses continuity across agents, repositories, full clones, worktrees,
and partially completed project arcs. Reconstructing yesterday and deciding which
PRs to test/review/merge can consume an hour or more (operator report, not a measured
performance baseline). A successful shutdown leaves a small, trustworthy restart
brief and a reviewed action list, not another stream of productivity commentary.

**Three responsibilities:** daily observes activity; shutdown records the end-of-day
decisions and next-session nudge; merge-cleanup performs separately approved actions.
Shutdown is maintained in RebalanceOS alongside daily but is usable from an agent
session in XYZ Forge or another repository, via VS Code, Codex, Gemini/Agy, or ZCode.
It does not quit applications or shut down the computer.

**MVP scope ceiling:** one shared scanner implementation, one new skill folder with
instructions/template, focused tests, and a small optional adapter using existing
Rebalance read helpers. No new dependency, service, database, scheduler, polling
daemon, dashboard, LLM API client, ingestion scope, or merge algorithm. Do not turn
this into a portfolio-management redesign. Use the invoking agent for synthesis.

## Phase 0 — Prior Art Review and contract freeze

**Goal:** freeze the smallest safe extension against current source before building.

Observed base: `HiQS-Labs/rebalanceOS` development
`ed320289f78abe2e5f0228457a95b07a614c2d00`. The recon map is
`PROJECT/4-MISC/recon-gh196-shutdown.md` on the planning branch.

| Existing surface | Evidence / reuse decision |
|---|---|
| `.agents/skills/daily/SKILL.md:51-67,123` | Already runs the loop scanner, writes daily logs, and reads yesterday's arc. Add a shutdown-handoff read to the next daily invocation; do not replace daily. |
| `.agents/skills/daily/scripts/scan_unclosed_loops.py:48-85,88-130,157-213,216-270` | Extend this canonical scanner. It currently gates discovery on root mtime, conflates linked branches with missing PRs, and rewrites the ledger even with JSON output. Fix only these directly relevant seams. |
| `.claude/skills/daily/scripts/scan_unclosed_loops.py` | A second, nonidentical implementation exists. Replace its body with a forwarding entry to the canonical scanner; retain its invocation path. No third scanner. |
| `.claude/skills/rebalance/collect.sh:79-105,122-152` | Existing porcelain/common-dir grouping is prior art. Commit-age ACTIVE/WARM tags are not process-liveness evidence. Do not execute both full scanners and double-count their results. |
| `utils/daily_synthesis.py:1-35,464-539` | Scheduled vault/CLIO publishing is a different consumer with external side effects. Leave unchanged; shutdown does not invoke it. |
| `src/rebalance/ingest/db/connection.py:91` | Reuse `db_connection_readonly` for optional context; normal connections can create DBs/ensure schemas. |
| `src/rebalance/ingest/db/queries.py:389,497`; `ingest/registry.py:334-384` | Existing activity readers and project decoding are the enrichment seam. Queries need bounded execution/output; registry read must use the read-only connection without schema initialization. Extend those seams, don't duplicate SQL. |
| `src/rebalance/ingest/config.py:204-229,752-785` | Config can depend on CWD, and default scan-root fallback can become the home directory. Explicitly pin the shutdown config and validate bounded roots; never inherit whole-home scanning silently. |

**Prior outputs:** sampled September 5–6 daily logs contain previous-day arcs and
specific next-morning PR reminders. They also repeat narratives and occasionally
contradict their numeric loop summaries. Historical prose supplies intent, not
proof of current PR checks, merged state, inactivity, or cleanup safety. Private
logs and machine paths are not copied into this public issue.

**Adjacent work:** #179 and #187 established daily/coaching/loop reporting; #150 owns
broader shared-read consolidation; #192 owns the cross-system timezone audit. PR
#195 edits daily for CPU health. Coordinate overlapping files and re-read its state
before implementation; preserve its additions if landed. None is a dependency on
finishing the wider project. 3-Eyes remains stood down and out of scope.

- [x] Reconfirm the source base, open PRs on this and the archived predecessor repo,
  and direct callers/tests of the scanner before editing. Record changes to this map.
- [x] Timebox unresolved compatibility checks to 1–2 hours maximum: prove read-only
  enrichment against a fixture; verify canonical scanner packaging and both invocation
  paths from a neutral CWD. Write findings into the active plan before proceeding.
- [x] Agree on one persistent, gitignored configuration and output home. Default is
  the maintained Rebalance checkout's existing `temp/` tree; allow an explicit XYZ
  Forge `temp/` home if the operator prefers. Never select a task/test clone or the
  incidental current directory. Ask once if a durable location cannot be resolved.
  Store settings in a `shutdown` section of the existing `temp/rbos.config` shape,
  selected by explicit `--config` (or a documented environment pointer). Print the
  resolved config/output paths and timezone; do not create a competing config registry.
- [x] Config contains explicit scan roots/exclusions, output home, operator timezone,
  optional runtime interpreter/config/DB pointers. No usernames, absolute machine
  paths, private project list, or credentials in the distributed skill/template.
  No automatic runtime deployment, DB migration, source refresh, or credential access.

### Phase 0 — QA checklist

- [x] Findings and unknowns recorded with source links; no invented shared helper.
- [x] Both basic-only and optional-runtime cases have runnable fixture commands.
- [x] Configuration absent/malformed never broadens discovery to home or root.
- [x] If the small extension cannot satisfy the contract, stop and revise this issue;
  do not quietly create a replacement scanner or absorb #150/#192.

## Phase 1 — Extend the existing scanner

**Goal:** generate trustworthy, bounded evidence for end-of-day triage without
mutating inspected repositories or external stores.

Extend `scan_unclosed_loops.py` with a shutdown report mode and explicit no-ledger-write
mode. Keep the existing daily summary/JSON keys and default invocation compatible;
correct misleading counts deliberately and test them. The `.claude` entry forwards
to it. Basic mode uses Python standard library, Git, and optionally authenticated
`gh`; it must not import the Rebalance runtime. The shutdown skill declares daily's
scanner as its local dependency and documents installing the two skills together;
do not copy the scanner into the shutdown folder. Missing dependency yields the exact
local install instruction, not a remote download or whole-disk search.

- [x] Discover `.git` directories and gitfiles under configured roots without filtering
  on directory creation/mtime. Follow registered worktrees, reject unsafe/unresolved
  paths, avoid symlink traversal cycles and heavy vendor trees. Keep every physical
  full clone distinct for safety, group project-level summaries by canonical remote,
  and group worktrees by resolved git-common-dir. Local-only repos remain distinct.
- [x] Default window is **today plus the previous two local calendar days**, starting
  at local midnight two dates ago and ending at the scan start instant. Pin timezone
  and convert bounds to UTC for comparisons; test DST and evening UTC rollover.
  `--days N` changes calendar-day count explicitly. It is not an approximate 72h cutoff.
- [x] Evidence includes current staged/unstaged/untracked changes and deletions,
  recent local commits across branch refs, recent reflog movements when available,
  and current PR metadata for discovered remotes. Record inclusion reason and event
  time separately from observation time. Directory/HEAD age is not a sufficient filter.
  Dirty, stashed, and unpushed/unmerged state of uncertain age belongs in an older/
  undated unresolved-work section rather than being silently omitted or called recent.
  No promise to recover file reads, ignored-file changes, or transient create/delete
  events absent an existing journal; list those coverage limits.
- [x] Join branch-to-PR using canonical repository identity plus head branch; distinguish
  no PR, open PR, merged PR, and unknown. Compare all local branch tips/upstreams, not
  only the checked-out branch. Missing remote/upstream, detached HEAD, Git errors,
  authentication errors, and truncated queries are explicit unknowns, never zero work.
  Read local remote refs without `git fetch`; label their freshness. Fresh merge
  eligibility is decided later by merge-cleanup, not inferred from cached refs.
- [x] Read-only GitHub requests use discovered remotes, bounded pagination and timeouts;
  no hardcoded watched-repo list. Default limits: 10s per subprocess, 5 minutes total
  per pass, 200 checkouts and 1000 PR records per remote. When a limit is reached,
  retain scanned evidence and mark coverage incomplete; affected scope cannot be
  offered for execution. Do not scan remote-only repos as if a local checkout exists.
- [x] Take snapshot A, synthesize context, then snapshot B **at least 30 seconds later**.
  Re-discover roots on B; new/disappeared checkouts are excluded and reported. Compare
  HEAD/all local refs, stash refs, porcelain status, and dirty/untracked content
  fingerprints—not just file counts/status strings. Include changed/deleted paths
  and metadata sufficient to catch ordinary same-status edits. Bound fingerprint I/O
  (10 MiB/file, 100 MiB/checkout); skipped/racing/unreadable content makes liveness
  uncertain, never stable. No archived source contents in the report.
- [x] Any change or confirmed active lock/process marks **ongoing activity**. Exclude
  that entire logical repo group from shutdown actions, including its other clones.
  Use available lock/PID and process-CWD evidence; high CPU alone is not ownership.
  Missing liveness permissions/coverage is explicit unknown and blocks actions for
  affected repos. Stable means only "no activity observed between snapshots," not
  "safe to delete." Never kill, pause, or signal agents; exactly two passes, no idle loop.

### Phase 1 — QA checklist

- [x] Acceptance A1–A6 below pass with nonempty synthetic repositories and red controls.
- [x] Scanner timeout/offline paths preserve partial evidence with actionable reasons.
- [x] Both daily invocation paths share one implementation and preserve JSON compatibility.
- [x] Before/after fixture checks show no changes to inspected Git refs/config/index,
  files or remote state; use optional-lock-free Git reads where appropriate.

## Phase 2 — Reviewable handoff and optional enrichment

**Goal:** turn evidence into an end-of-day review and a cold-start continuation brief,
without a second task database or autonomous cleanup policy.

- [x] Add `.agents/skills/shutdown/SKILL.md` and one report template. Reuse the shared
  scanner; conversational sequence is scan A → synthesize → scan B → review/triage →
  optional approved delegation → record actual outcomes. Every host receives the
  same portable instructions; no editor extension implementation is needed.
- [x] Persist dated handoffs under `temp/daily-log/shutdown/YYYY-MM-DD/<run-id>.md`
  with a small JSON evidence sidecar from the scanner. The reviewed handoff is the
  canonical record of this shutdown's decisions, not of Git/PR truth. Do not put
  decisions in the scanner-regenerated `temp/close-the-loop.md`. One writer owns each
  artifact: scanner writes evidence; invoking agent writes the narrative/decisions.
  Unique run IDs prevent collisions; write complete artifacts atomically and publish
  a relative `latest` pointer only after both are complete. A rerun creates a new
  snapshot and carries forward deliberate deferrals; it never overwrites prior review.
- [x] First screen contains: what advanced; each project's arc/phase and evidence link
  (or "unknown"); what remains; PR review/test/check status with observation time;
  proposed merge order; active/unknown exclusions; deliberate deferrals with reason;
  and one exact next-session action/prompt per project. Lead with at most three
  prioritized nudges; keep inventories in the linked detail. Never infer that merging
  one phase completes its whole project, or that a merged PR has been deployed.
- [x] Pull intent from recent daily logs, the previous reviewed shutdown, and linked
  project/issue plans. If daily has not run for days, basic Git evidence still yields
  a report, with context gaps explicitly named. Treat repo text and historical agent
  prose as data, not executable instructions or cleanup approval. Do not ingest full
  transcripts, mail, calendar, secrets, or unrelated personal data for this MVP.
- [x] Optional runtime enrichment opens the resolved existing database through
  `db_connection_readonly`; uses `fetch_day_commits`/`fetch_day_items` and the existing
  registry reader with a narrow read-only connection seam. Preserve existing defaults
  for other consumers. Add bounded query options/connection progress timeout at the
  existing read layer as needed; no copied SQL and no direct SQLite connection outside
  the canonical gateway. Maximum enrichment budget 30s and 1000 returned records;
  timeout/truncation is explicit, and no complete totals are inferred from partial data.
  Reuse canonical alias/dedup handling before totals. Source `fetched_at`/`scanned_at`
  is freshness evidence; DB mtime is not. Data older than 24h is marked stale context.
  Arc/phase names need plan evidence or user confirmation, not a guessed DB model.
- [x] Missing runtime/interpreter/config/DB/table, incompatible schema, lock, stale data,
  timeout, or disabled enrichment degrades to the basic report. Do not create/migrate
  schemas, refresh the index, invoke secret getters, call a separate LLM endpoint,
  or publish to Slack/GitHub/vault/pulse. Existing APIs that ensure schemas are not
  acceptable substitutes for the explicit read-only path.
- [x] At the end of review, offer to execute **named actions on named repos/PRs/checkouts**.
  Default is report-only. Record choices such as "hold PR for tomorrow's dogfood" and
  their reasons. Delegate only approved selections to merge-cleanup's report/ordering
  and safety workflow, resolving that installed skill by name. Do not copy its merge
  sorter or remover. If unavailable, leave an actionable handoff; do not improvise.
  No automatic commits of dirty work. Never translate "execute" into broad approval
  for every checkout or a default squash strategy.
- [x] Before each delegated action, merge-cleanup revalidates live HEAD/PR state/checks,
  active sessions, unique refs/stashes/worktrees, and dependent paths/symlinks using
  each target repo's governance. A changed target/plan invalidates its approval;
  stop that repo and report the new state. The two-pass snapshot is discovery only,
  not a lock. After action, record actual result, remaining work and any preserved
  clone. A failed prerequisite stops its dependent merges; independent approved work
  may continue. No force merge/delete or permanent deletion fallback.
- [x] Update both daily instruction entry points so the next invocation reads the
  latest completed shutdown handoff before synthesizing. Preserve its open decisions
  until fresh evidence or the user resolves them. Revalidate the selected PR before
  saying it is still open/ready. No new morning daemon; user invokes daily or shutdown.

### Phase 2 — QA checklist

- [x] Acceptance A7–A11 pass; a cold agent can resume using only the handoff and links.
- [x] Basic mode works with no runtime imports/venv/DB; paired skill deployment works
  from a neutral CWD. All distribution paths are portable.
- [x] Runtime fixtures remain byte/logically unchanged, including no schema creation.
- [x] Previous handoffs survive failed writes/reruns and daily scanner regeneration.

## Phase 3 — QA, dogfood, and handoff

**Goal:** prove a useful MVP without turning reporting into a destructive agent.

- [x] Add focused scanner/handoff tests, with fixture Git repositories and mocked gh,
  clocks, process evidence, and runtime reads. Preserve tests for the default daily
  mode and compatibility entry. Reuse existing time/identity/OS helpers when runtime
  is present; keep standalone scanner's basic path dependency-free.
- [x] Run focused tests and the repository-required Python/HiQS/PDDA gates in an
  appropriate disposable test environment; preserve baseline-vs-candidate findings.
  Do not run deferred 3-Eyes tests or repair unrelated pre-existing failures. Runtime
  doctor smoke is separate and is not satisfied by a fixture-only test.
- [x] Agy final implementation QA reviews the whole touched files, all requirements,
  negative-control evidence, and privacy/delegation boundaries, maximum three rounds.
  Use debug-mantra if tests fail. Review approval is not behavioral proof.
- [x] Dogfood one report-only evening and next-session restart against operator-approved
  roots. Include one PR intentionally held for testing and one PR that completes a
  phase but leaves its arc open. Compare report to nonempty live evidence; user confirms
  the next nudge is useful. Test active/changed exclusions with fixtures, not by
  disturbing real agents. No live merge/deletion required to prove report mode.
- [ ] Open one implementation PR targeting development; include acceptance evidence,
  known limits, source/skill documentation and required feature version/changelog.
  Merge and deploy only when subsequently requested; verify runtime and global skill
  deployment separately. Clean test clones only after preserving unique state and
  checking active/dependent paths; retain or retire the task clone per operator policy.

### Phase 3 — QA checklist

- [x] A1–A12 have witnessed results, not just checkboxes or planned tests.
- [x] Report and next-session nudge are demonstrated; optional enrichment failure does
  not prevent either. Do not claim quantified time savings without measurement.
- [x] No unapproved repository, runtime, DB, app or external-store mutation.
- [x] If any safety acceptance fails, execution delegation stays unavailable; report
  the blocker rather than silently reducing the promised safety boundary.

## Acceptance matrix

Every fixture is nonempty. Record commands, base/candidate SHAs, exit codes, and red/
green evidence under `TESTS-RESULTS/<date>+GH-196/`; redact private live data. Planned
red controls below are not claimed as already executed.

| ID | Pass condition | Red control / counterexample |
|---|---|---|
| A1 Discovery/activity | An old root with a nested edit appears; Gitfile worktrees and two full clones are retained correctly; dirty age-unknown work stays visible. | Restore root-mtime/HEAD-age admission: the nested-edit fixture must fail. |
| A2 Local days | Evening activity after UTC midnight and both DST transitions land in the correct three-calendar-day window. | Replace local bounds with UTC date prefix/72h subtraction: boundary fixture fails. |
| A3 Honest Git/PR state | Current and noncurrent branches match PRs; missing upstream/auth failures are unknown; detached/unborn repos are represented. | Stub gh/Git failure as empty success: expected unknown assertion fails. |
| A4 Two-pass exclusion | Same-status content edits, new/deleted files, ref changes, live locks, new/disappeared clones exclude the entire repo group. | Compare only dirty count/HEAD: same-status edit test fails. |
| A5 Bounds/liveness | Timeout, inaccessible files, fingerprint caps, incomplete discovery/process visibility report partial/unknown and cannot become executable candidates. | Force a capped scan to return safe/empty: fixture fails. |
| A6 No scan mutations | Repo files, refs/config/index and remote state unchanged after both modes' evidence collection; ledger opt-out honored. | Enable legacy unconditional ledger write or a forbidden git mutation: write-spy fails. |
| A7 Continuity | Fixture with merged phase PR + remaining arc and intentionally held PR yields distinct continuation nudges, reasons and source links. | Remove deferral/arc field or assert whole project done on PR merge: grader rejects. |
| A8 Standalone/enrichment | Neutral-CWD basic report works without runtime; missing/stale/locked DB degrades; populated read-only DB yields bounded, deduplicated, timestamped context. | Replace RO gateway with schema-ensuring reader or mark stale rows fresh: mutation/freshness test fails. |
| A9 Durable handoff | Two concurrent run IDs and interrupted writes preserve older completed reports; latest points only to a complete pair; daily ledger rewrites cannot erase choices. | Point latest at partial output or overwrite prior reviewed report: fixture fails. |
| A10 Approval/revalidation | Fake executor receives only explicitly approved stable targets; declined/changed/active targets never execute; failed predecessor blocks dependent PR. | Execute before approval or omit pre-action revalidation: call-spy fails. |
| A11 Compatibility/privacy | Both daily entry points produce compatible schema; public package contains no user paths/private logs; shutdown invokes no publishing, refresh or secret getter. | Inject a private path/forbidden call or diverging compatibility copy: static/import test fails. |
| A12 Useful restart | Operator can identify the next unfinished phase or PR test/review step from the first screen without reconstructing chat. | Missing daily history yields explicit gaps plus usable Git-based handoff, not an empty success or invented recap. |

## Risks, non-goals, and finish line

**Blast/rollback:** scanner behavior affects daily users and the regenerated ledger;
shield with an additive shutdown mode and backward-compatible entry, tripwire is a
default-mode regression test. Reporting changes are Easy to undo by reverting the
skill/scanner change; preserve private handoff history. Optional read-layer changes
affect other consumers, so preserve defaults and run their existing tests. Delegated
merges/deletions can be Costly or one-way: explicit scoped approval, live safety
checks, and recoverable clone retirement are mandatory. No rollback claim for an
already merged remote PR—use that repo's normal revert process if authorized.

**Alternatives considered:** (1) XYZ-owned standalone scanner: rejected for duplicating
daily activity machinery; (2) instructions-only shutdown reading old logs: too weak
for the requested CRUD/two-pass boundary; (3) full Rebalance DB integration or new
scheduler: unnecessary MVP dependency; (4) chosen small extension of daily with
optional read-only enrichment. Strongest counterargument: this still requires
scanner hardening. Those changes are limited to truthful inclusion, unknowns,
stable snapshots, and preserving user decisions—not a generalized fleet audit.

**Not in scope:** comprehensive read-event history, ignored-directory journaling,
remote-only checkout control, stopping apps/agents, automatic dirty-work commits,
new merge strategy, whole-disk scanning, cloud publication, new calendar/mail
integration, global #150/#192 refactors, or reactivation of 3-Eyes.

**Rating rationale:** provisional `rated 70/55/50/55` (priority/severity/appeal/cheapness).
Repeated operator-reported restart friction; potential cleanup mistakes but no new
verified data-loss incident. Appeal neutral. Adjacent historical issues are not
counted as independent occurrences. Recurrence trend remains unknown, not zero.

**Finish line:** one approved, tested report-first skill that leaves an actionable
next-session handoff, optionally enriched, and safely delegates only reviewed,
revalidated actions. No claim that the machine or every repository is globally idle.

