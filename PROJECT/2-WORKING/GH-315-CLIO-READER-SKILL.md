---
gh_issue: 315
source: https://github.com/HiQS-Labs/rebalanceOS/issues/315
title: CLIO history and HiQS activity lookup skill
status: In progress
created: 2026-10-02
doc_type: feedback
updated: 2026-10-03
owner: Codex
goal: Make existing CLIO history and HiQS activity readers discoverable
branch: codex/clio-reader-skill
---

# CLIO history and HiQS activity lookup skill

Create a repository skill reusing the merged XYZ-CLIO SQLite reader and existing Rebalance `github_activity` readers, with optional Pulse/Daily summaries. Preserve configured paths, stable provenance, bounded lookup, and read-only retrieval. No new query implementation or runtime change.

PRS rated 55/30/50/90: requested discovery improvement; no observed data loss; neutral appeal; inexpensive documentation over existing readers.

## Status

| What was just completed | What's next |
|---|---|
| Final Codex relay approved revised authorship instructions | Final documentation gate and PR; awaiting merge |

## Scope and acceptance

- [x] Reuse installed XYZ-CLIO query helper; configuration precedence and missing-store behavior are explicit.
- [x] Explain exact filters, bounded pagination, stable IDs, pending/fleet limits and seven-day note scope.
- [x] Route activity requests to `github_activity` via existing MCP readers and the shared read-only query layer; Pulse/Daily are optional.
- [x] Skill validator and mirror comparison pass; doc links pass (632 checked). PDDA reports pre-existing findings in unrelated docs (7 frontmatter, 9 status-table); none name GH-315.
- [x] Obtain independent final Codex approval.
- [ ] Merge the resulting PR against development after hosted checks.

## Recon and implementation decision

Base: `cfb91a2180adac9e550d9de5b314bff89ddfda94`. XYZ-CLIO #4 merged September 30; #5 and #6 merged October 2. Canonical `utils/CLIO/clio-store.py` implements config, query and argument parsing. This repository's legacy CLIO directory does not carry that helper. The graph generation was September 2 and reported changed source metadata, so current source was read directly. No Rebalance retrieval MCP was exposed in this session.

Current source anchors: `src/rebalance/paths.py`, `src/rebalance/ingest/config.py::get_pulse_config`, `src/rebalance/lib/git_ops.py::fleet_output_path`, `src/rebalance/ingest/pulse.py::fleet_view`, `utils/daily_synthesis.py`, and the existing Daily skill. Operator clarified the work activity source is `github_activity`. The skill now names that snapshot table, the shared read-only gateway/query layer, authorship-versus-participation semantics, aliases/deduplication, timestamps and bounded raw-row fallback. Pulse/Daily remain optional derived summaries.

This is a simple, reversible documentation change over existing interfaces. Pre-implementation plan QA is skipped under start-task Step 6's simple-change exception; final independent QA remains required. No production code, helper, query path, install, migration, scheduler, cloud inference or live database mutation is introduced. Use the repository's existing `.agents` and `.claude` skill layout with identical content.

Verification is skill validation, mirror comparison, interface/source checks, documentation links and PDDA. Runtime tests/doctor are not a completion claim for this documentation-only task. No retrieval quality, fleet completeness or performance claim is made. Rollback removes the skill copies and their discovery pointer.

## PRS and ledger

Rated 55/30/50/90: priority reflects the requested discoverability gap; severity is moderate inconvenience with no observed data loss; appeal remains neutral; effort is inexpensive because query logic has already landed. No recurring-incident claim. The repository's older ledger only offers whole-roadmap sync/list, not per-row add/update. Use that writer and disclose any pre-existing mirror drift it also reconciles.

## QA record

Final Codex relay approved both initial and clarified packets (driver exit 0, attested Approved). The initial Pulse-focused approval was superseded after the operator identified `github_activity`. The revised review found no blockers/shoulds; its plan-opener wording nit is applied. Review log: `TESTS-RESULTS/2026-10-02+GH-315/final-review.log`. The reviewed skill SHA-256 is recorded in `provenance.json`. Runtime behavior/deployment is not claimed.

The standard whole-roadmap writer also reconciled existing stale mirror rows (the first sync added 3 existing rows and updated 76; the task registration then added 1 and updated positions). These generated changes are ledger synchronization, not new scope or status assertions; DB/dump receipt checks pass with existing warnings.

Final documentation gate: skill validator, mirror comparison, relative links, front-door board, machine-path guard, ledger consistency and diff whitespace pass. Roadmap coverage is observe-mode exit 0 with unrelated existing findings; it is not reported clean. Evidence: `TESTS-RESULTS/2026-10-02+GH-315/final-checks.log`. No tracked pre-push hook ships on the base; the clone uses the repository hooks directory. No runtime tests or doctor run is claimed for this documentation-only change.

## Naming follow-up — 2026-10-03

Aligned both skill copies with PR #320: HiQS means High Quality Signals; canonical MCP `hiqs_work_activity` and Python `get_hiqs_work_activity`, with deprecated-name fallback for older runtimes. Kept table `github_activity`, SQL reader `fetch_github_balance`, output shape and read-only gateway guidance unchanged. Checked the PR head source for the actual adapter signatures. PR #320 was still open at this update; no merge or deployment is assumed. The earlier relay approval covers the prior revision; this narrow documentation follow-up receives focused validation recorded in `TESTS-RESULTS/2026-10-02+GH-315/naming-checks.log`.
