---
gh_issue: 368
source: https://github.com/HiQS-Labs/rebalanceOS/issues/368
title: "Restore Codex prompt capture"
status: PR ready — merge and deployment acceptance pending
created: 2026-10-29
updated: 2026-10-29
owner: Codex
doc_type: bugfix
complexity: 2
risk: 2
effort: 2
phases: 1
ratings_provisional: false
non_goals:
  - No response_item import
  - No new suite or gate
  - No direct standalone edits
related:
  - https://github.com/HiQS-Labs/XYZ-forge/issues/1255
  - https://github.com/HiQS-Labs/XYZ-CLIO/issues/14
goal: >
  Restore submitted Codex prompt capture with source provenance and durable replay.
---

## Key concepts

- Submitted-event provenance
- Explicit replay with stable IDs
- Operational zero-capture warning

> **Note for plan writers:** apply the `/ponytail` lens — favor the laziest approach that actually
> works over new infrastructure, and question whether new surface needs to exist at all.

# Restore Codex prompt capture

## Status

| What was just completed | What's next |
|---|---|
| Plan QA Approved; implemented modern parsing, durable replay and diagnostic warning. | Publish reviewed PR; after merge, publish standalone and verify authorized target deployment/backfill. |

## Idea

Implementation of Forge #1255; canonical plan in XYZ-forge PROJECT/2-WORKING/GH-1255-CODEX-CAPTURE.md. Accept modern submitted events, preserve retries, explicitly replay seen root files, warn on active zero-delivery ticks, extend existing suite only.

## Why

Silent Codex history loss after submitted-event format changed.

## Verification

All six existing CLIO suites pass, including 17 store cases after the existing stale-window fixture correction. Three negative controls fail as expected. Receipts, commands, revisions, failures and dispositions: [verification summary](../../TESTS-RESULTS/2026-10-29+GH-368/SUMMARY.md), with provenance.jsonl in the same directory. Static push gate passes. Independent final Codex QA Approved in round 2; receipt: `relay-system/2026-10-29/gh1255-final.codex.md`. Live target acceptance remains pending.

## Canonical plan and rating rationale

[Forge #1255 plan](https://github.com/HiQS-Labs/XYZ-forge/blob/fix/XYZ-forge-gh1255-codex-capture-2026-10-29/PROJECT/2-WORKING/GH-1255-CODEX-CAPTURE.md) owns the ordered cross-repository execution and acceptance checks. This document is the upstream execution pointer. rated 85/85/50/65, 2026-10-29: silent ongoing history loss; two linked reports describe one incident, and recent/preceding 14-day incident trend is unknown. Neutral appeal; bounded implementation cost, no operator override. No new suites, CI machinery or schema changes. Extend existing parser/state/writer integration. Independent Codex plan QA Approved in round 2; receipt: `relay-system/2026-10-29/gh1255-plan.codex.md`. Implementation follows the approved parser/replay/canary scope, with existing suite extensions and no new suite or gate.

## Delivery boundary

Author upstream here, then publish unchanged to standalone only after merge. Deployment through Skills Army HQ and target-device two-minute capture/backfill remain post-landing acceptance; no automatic merge or task-checkout installation. One requested source session has no submitted events and cannot be recovered via response_item under this contract. Rollback code only; preserve additive history.

## Existing verification correction

The adjacent store suite had a pre-existing date-dependent failure: its activation case expected five rows in the current seven-day projection, but its imported source row was fixed at September 29. The same failure (4 != 5) reproduced against unchanged development. Change only that case's source row to the existing store.utc() timestamp helper; preserve five-row assertions and all production store code. This keeps the existing suite truthful without a new test or relaxed check. Final QA includes the one-line fixture correction and retained base/control receipts.

Lessons: NO_ENTRY. Existing dated-fixture correction and documentation typo are recorded with their controls; no general lesson is asserted from a single intervention.

Final machine gate: the cross-repo transcript approval could not publish its machine record because its parent is ignored. The supported Forge external-artifact review supersedes that attempt: [round-3 final QA and driver attestation](https://github.com/HiQS-Labs/XYZ-forge/blob/126ccd2a/relay-system/2026-10-29/gh1255-publication.codex.md). relay-drive returned 0 and its receipt validated; capture code remains unchanged since the tested revision.
