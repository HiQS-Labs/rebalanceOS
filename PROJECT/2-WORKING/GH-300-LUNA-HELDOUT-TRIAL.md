---
title: GPT 6 Luna High — corrected held-out storyline trial
status: In progress
owner: Codex
goal: Test whether Luna preserves evidence and attempt boundaries on three unseen CLIO/GitHub cases after GH-232's factual-gate failure.
created: 2026-09-30
updated: 2026-09-30
reversibility: Easy — private read-only experiment and removable outputs; source records unchanged
gh_issue: 300
source: https://github.com/HiQS-Labs/rebalanceOS/issues/300
doc_type: research
---

# GH-300 — Corrected held-out Luna narrative trial

## Status

| What was just completed | What's next |
|---|---|
| Bounded probe and six held-out Luna High samples completed; source audit found both #567 repeats omit supporting `U*` citations, so the factual promotion gate failed | Present private A/B/C views for operator preference; keep Daily off and retain the frozen trial result |

The [sanitized campaign](../../TESTS-RESULTS/2026-09-30+GH-300-LUNA-HELDOUT/SUMMARY.md) records exact limits and results. The private Git Pulse Sync folder `experiments/gh300-luna-heldout-2026-09-30/` holds all packets, controls, candidate repeats and raw run receipts. No source status or runtime code was changed. The first GH-232 results were not rescored or compared to this held-out trial.

## Table of contents

- [Phase 0 — source and runner spike](#phase-0--source-and-runner-spike)
- [Phase 1 — freeze matched views](#phase-1--freeze-matched-views)
- [Phase 2 — bounded inference and audit](#phase-2--bounded-inference-and-audit)
- [Phase 3 — publish and ask](#phase-3--publish-and-ask)

## Phase 0 — source and runner spike

**Goal:** validate source availability and exact runner without changing runtime code; cap at one hour.

- [x] Read #232 results, repo rules, current replay and GitHub relationship seams. The existing `src/rebalance/ingest/clio_journey.py` provides read-only capture/replay and rendering; no collector, database writer or UI is needed. Source is the recovered frozen replay, not a new CLIO capture. The existing Codex CLI and Git Pulse Sync private checkout carry inference and results.
- [x] Verify capture cutoff/hash and candidate membership using strict qualified URL parser. #589 has three qualified prompts across Claude Code/agy; #605 and #567 have one each. Bare #567 mentions are unresolved, not joined. Read-only GitHub GraphQL reports #605→PR #607 and no native closing PR for #589/#567 as observed on September 30.
- [x] Verify existing authenticated runner availability from GH-232: CLI `0.155.0-alpha.16` accepts explicit `gpt-6-luna`/high, model catalog lists it, and prior calls returned usage; JSON events do not return a server model ID. This is recorded as a limitation, not silently treated as a returned identity.

### Phase 0 — QA checklist

- [x] Nonempty capture and all three issue records observed; source times and current observations distinguished.
- [x] No production read/write seam added. Blast radius: private Git Pulse Sync experiment folder, sanitized campaign docs and bounded model usage only; rollback is to stop and retain receipts.
- [x] A missing source, model rejection, privacy check failure or inconsistent relationship is a visible stop condition. Use debug-mantra on a failure; no silent retry.

## Phase 1 — freeze matched views

**Goal:** immutable, minimized packets and controls for all three cases.

- [x] Build stable source IDs for qualified prompts, GitHub facts, relationships and **every gap**. Mark bare mentions unresolved and keep agents/chats separate.
- [x] Freeze A chronological history, B plain list and C packet from identical evidence. The capture cutoff is September 16 and GitHub observation is September 30; later closure is retrospective only. Hash each input and validate source/retrieval times.
- [x] Commit the fixed prompt, rubric, packet hashes, negative-control specification and private dataset before inference. No raw CLIO export, full GitHub response, credential or unrelated personal material in the private sync folder; the outbound model packet is narrower still. Private Git Pulse Sync freeze commit: `84dda605`.

### Phase 1 — QA checklist

- [x] Three nonempty packets and matched A/B controls; IDs unique, hashes stable, redaction scan passes.
- [x] Mutated citation ID and missing required gap/relationship record are rejected by the validator.
- [x] Exact source revision/read/write paths, failure behavior and validation commands recorded in the private manifest and validation receipt.

## Phase 2 — bounded inference and audit

**Goal:** one probe and six fresh, unedited real outputs within the issue's envelope.

- [x] Synthetic probe tests re-prompt versus restart, wrong-repo same-number, merged-without-deployment and embedded instruction; it preserved all boundaries with no tool events.
- [x] Run two independent Luna High sessions per case from identical frozen input. No retry; all six were within 180 seconds/call, reported 30K input/4K output per call and estimated API-equivalent <=$0.25. CLI version, requested identity/effort, returned-identity absence, usage/cache/reasoning, UTC, wall time, exit, tool events and estimated versus billed-unknown cost retained.
- [x] Manually audit every material claim against source IDs for both repeats. No candidate self-grading or output repair. Both #567 repeats lack the `U*` IDs that support their bare-mention details; this fails citation completeness.

### Phase 2 — QA checklist

- [x] Probe and witnessed negative controls retained; six samples completed.
- [ ] Both repeats preserve attempt boundaries, observation time and uncertainty, but the #567 bare-mention detail is not cited to `U1778`/`U1785` in either repeat. Factual citation gate failed.
- [x] Every run and failure receipt retained; no hidden retry or model substitution. Server-returned model identity is unavailable from CLI JSON events and explicitly recorded as unknown.

## Phase 3 — publish and ask

**Goal:** private readable comparison and public-safe audit, with operator preference separate from factual quality.

- [x] Retain both repeats and A/B/C views in a new Git Pulse Sync folder, with a frozen blind map. Operator preference and misleading-details answer remain pending.
- [x] Publish sanitized protocol, counts/hashes, claim audit, per-run latency/usage/API-equivalent cost, gates and limits under `TESTS-RESULTS/2026-09-30+GH-300-LUNA-HELDOUT/`; link this issue and #232.
- [x] Run fresh focused and full repository checks plus doctor/doc checks, report pass/fail separately, and leave Daily and source systems untouched.

### Phase 3 — QA checklist

- [x] Public campaign and issue agree; private views show all six outputs without cherry-picking.
- [ ] Fact gate failed and is recorded independently; human preference is pending. No Daily adoption or broader superiority claim from three cases.

The issue's current body is the authoritative plan. If this document and the issue diverge, correct this document before inference. No earlier result is rescored or compared to this run.
