---
gh_issue: 315
source: https://github.com/HiQS-Labs/rebalanceOS/issues/315
title: CLIO history and HiQS activity lookup skill
status: In progress
created: 2026-10-02
doc_type: feedback
updated: 2026-10-02
owner: Codex
goal: Make existing CLIO history and HiQS activity readers discoverable
branch: codex/clio-reader-skill
---

# CLIO history and HiQS activity lookup skill

Create a repository skill reusing the merged XYZ-CLIO SQLite reader and existing Pulse/Daily outputs. Preserve configured paths, stable provenance, bounded lookup, and read-only retrieval. No new query implementation or runtime change.

PRS rated 55/30/50/90: requested discovery improvement; no observed data loss; neutral appeal; inexpensive documentation over existing readers.

## Status

| What was just completed | What's next |
|---|---|
| Source/interface recon and skill draft | Focused validation and final Codex relay QA; then PR |

## Scope and acceptance

- [x] Reuse installed XYZ-CLIO query helper; configuration precedence and missing-store behavior are explicit.
- [x] Explain exact filters, bounded pagination, stable IDs, pending/fleet limits and seven-day note scope.
- [x] Route activity requests to existing MCP readers and configured Pulse/Daily outputs.
- [x] Skill validator and mirror comparison pass; doc links pass (632 checked). PDDA reports pre-existing findings in unrelated docs (7 frontmatter, 9 status-table); none name GH-315.
- [ ] Obtain independent final Codex approval and open PR against development.

## Recon and implementation decision

Base: `cfb91a2180adac9e550d9de5b314bff89ddfda94`. XYZ-CLIO #4 merged September 30; #5 and #6 merged October 2. Canonical `utils/CLIO/clio-store.py` implements config, query and argument parsing. This repository's legacy CLIO directory does not carry that helper. The graph generation was September 2 and reported changed source metadata, so current source was read directly. No Rebalance retrieval MCP was exposed in this session.

Current source anchors: `src/rebalance/paths.py`, `src/rebalance/ingest/config.py::get_pulse_config`, `src/rebalance/lib/git_ops.py::fleet_output_path`, `src/rebalance/ingest/pulse.py::fleet_view`, `utils/daily_synthesis.py`, and the existing Daily skill. Pulse is the working interpretation of the requested activity stream, with Daily explicitly labelled derived synthesis.

This is a simple, reversible documentation change over existing interfaces. Pre-implementation plan QA is skipped under start-task Step 6's simple-change exception; final independent QA remains required. No production code, helper, query path, install, migration, scheduler, cloud inference or live database mutation is introduced. Use the repository's existing `.agents` and `.claude` skill layout with identical content.

Verification is skill validation, mirror comparison, interface/source checks, documentation links and PDDA. Runtime tests/doctor are not a completion claim for this documentation-only task. No retrieval quality, fleet completeness or performance claim is made. Rollback removes the skill copies and their discovery pointer.

## PRS and ledger

Rated 55/30/50/90: priority reflects the requested discoverability gap; severity is moderate inconvenience with no observed data loss; appeal remains neutral; effort is inexpensive because query logic has already landed. No recurring-incident claim. The repository's older ledger only offers whole-roadmap sync/list, not per-row add/update. Use that writer and disclose any pre-existing mirror drift it also reconciles.

## QA record

Pending final relay review.
