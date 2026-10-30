---
gh_issue: 368
source: https://github.com/HiQS-Labs/rebalanceOS/issues/368
title: "Restore Codex prompt capture"
status: Active — implementation and clone verification
created: 2026-10-29
updated: 2026-10-29
owner: Codex
doc_type: bugfix
complexity: 2
risk: 2
effort: 2
phases: 1
ratings_provisional: true
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
| Captured via HQ (`/hq park`) for project **rebalanceOS** → repo `rebalanceOS`. The GitHub issue is the signal stream; this doc is the in-repo capture and back-reference. | Run isolated existing CLIO suites, witness red controls, then final independent Codex QA. |

## Idea

Implementation of Forge #1255; canonical plan in XYZ-forge PROJECT/2-WORKING/GH-1255-CODEX-CAPTURE.md. Accept modern submitted events, preserve retries, explicitly replay seen root files, warn on active zero-delivery ticks, extend existing suite only.

## Why

Silent Codex history loss after submitted-event format changed.

## Phase 0 — Explore & scope

### Checklist

- [ ] Not applicable to this bounded bugfix: scope-specific checklist items for this idea's Phase 0 pass.

### QA checklist — Phase 0

- [ ] Not applicable to this bounded bugfix: acceptance criteria for the Phase 0 pass above.

## Canonical plan and rating rationale

[Forge #1255 plan](https://github.com/HiQS-Labs/XYZ-forge/blob/fix/XYZ-forge-gh1255-codex-capture-2026-10-29/PROJECT/2-WORKING/GH-1255-CODEX-CAPTURE.md) owns the ordered cross-repository execution and acceptance checks. This document is the upstream execution pointer. rated 85/85/50/65, 2026-10-29: silent ongoing history loss; two linked reports describe one incident, and recent/preceding 14-day incident trend is unknown. Neutral appeal; bounded implementation cost, no operator override. No new suites, CI machinery or schema changes. Extend existing parser/state/writer integration. Independent Codex plan QA Approved in round 2; receipt: `relay-system/2026-10-29/gh1255-plan.codex.md`. Implementation follows the approved parser/replay/canary scope, with existing suite extensions and no new suite or gate.

## Delivery boundary

Author upstream here, then publish unchanged to standalone only after merge. Deployment through Skills Army HQ and target-device two-minute capture/backfill remain post-landing acceptance; no automatic merge or task-checkout installation. One requested source session has no submitted events and cannot be recovered via response_item under this contract. Rollback code only; preserve additive history.
