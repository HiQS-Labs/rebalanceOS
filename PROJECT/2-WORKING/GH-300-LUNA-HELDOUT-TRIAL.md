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
| Trial registered in #300; held-out #589/#605/#567 dataset and controls committed privately before inference; altered citation, missing relationship and missing gap rejected | Run the synthetic probe, then six bounded fresh Luna High calls and independent source audit |

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

- [ ] Synthetic probe tests re-prompt versus restart, wrong-repo same-number, merged-without-deployment and embedded instruction; stop on unsupported join/completion/action.
- [ ] Run two independent Luna High sessions per case from identical frozen input. One transport-only retry maximum; eight attempts total. 180 seconds/call, 30 minutes phase, reported 30K input/4K output per call where enforceable, estimated API-equivalent <=$0.25. Record CLI version, exact requested/returned identity status, effort, token/cache/reasoning usage, UTC, wall time, exit, tool events and cost estimate versus billed unknown.
- [ ] Manually audit every material claim against source IDs for both repeats. One invented join, unsupported completion/deployment, erased critical boundary or re-prompt/restart conflation fails promotion. No candidate self-grading or output repair.

### Phase 2 — QA checklist

- [ ] Probe and witnessed negative controls retained; six samples or explicit incomplete coverage.
- [ ] Both repeats preserve attempt boundaries, observation time and uncertainty; all factual claims have valid `[[ID]]` citations.
- [ ] Every run and any failure receipt retained; no hidden retry or model substitution.

## Phase 3 — publish and ask

**Goal:** private readable comparison and public-safe audit, with operator preference separate from factual quality.

- [ ] Retain both repeats and A/B/C views in a new Git Pulse Sync folder, with a frozen blind map. Ask the operator which view helps explain and resume each case and what misleads; never infer a missing answer.
- [ ] Publish sanitized protocol, counts/hashes, claim audit, per-run latency/usage/API-equivalent cost, gates and limits under `TESTS-RESULTS/2026-09-30+GH-300-LUNA-HELDOUT/`; link this issue and #232.
- [ ] Run fresh focused and full repository checks plus doctor/doc checks, report pass/fail separately, and leave Daily and source systems untouched.

### Phase 3 — QA checklist

- [ ] Public campaign and issue agree; private views show all six outputs without cherry-picking.
- [ ] Fact gate and human preference recorded independently; no Daily adoption or broader superiority claim from three cases.

The issue's current body is the authoritative plan. If this document and the issue diverge, correct this document before inference. No earlier result is rescored or compared to this run.
