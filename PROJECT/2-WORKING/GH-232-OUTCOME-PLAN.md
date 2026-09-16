---
title: CLIO work journeys — outcome plan
status: In progress
owner: Codex
goal: Decide whether explicit CLIO and GitHub evidence can produce a useful repeatable work-history companion.
created: 2026-09-16
updated: 2026-09-16
reversibility: Easy — optional private read-only projections; sources remain unchanged
gh_issue: 232
source: https://github.com/HiQS-Labs/rebalanceOS/issues/232
doc_type: research
---

# CLIO work journeys — outcome plan

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 optional issue-evidence view implemented; original frozen records preserved | Phase 2 entry recon and delivery-link checks; automated relay/app gates remain incomplete |

## Table of contents

- [Three possible endings](#three-possible-endings)
- [Phase 0: pin the trial](#phase-0-pin-the-trial)
- [Phase 1: show the missing explicit evidence](#phase-1-show-the-missing-explicit-evidence)
- [Phase 2: verify delivery relationships](#phase-2-verify-delivery-relationships)
- [Phase 3: test usefulness and choose the ending](#phase-3-test-usefulness-and-choose-the-ending)
- [Boundaries and handoff](#boundaries-and-handoff)

## Three possible endings

| Ending | What we would have | When to choose it |
|---|---|---|
| **A — useful, repeatable work-history companion (ideal)** | One local command creates a readable private history: requested work, separate attempts, linked GitHub delivery, changes in direction and visible gaps. It groups explicit issue evidence across chats without pretending they form one continuous task. | Correctly sourced histories are useful to the operator, and repeat on a second small sample without substantial repair. |
| **B — simpler issue-linked evidence notebook** | A reliable list of prompts and GitHub facts under explicitly named issues, with no inferred starts, endings or causal story. We keep the useful search/history part and park journey inference. | Explicit grouping is useful, but inferred boundaries or narrative add confusion or ongoing maintenance. |
| **C — stop this experiment and retain the lessons** | Preserved capture, tested parser, reports and a clear account of what failed. No new live feature or model-training investment. | Even the simple issue-linked view does not help, evidence is too sparse, or privacy/reliability/maintenance costs exceed its benefit. |

**A is most ideal because it answers “what did this work turn into?” with little extra effort.**
It is not a promise to infer every action or reconstruct all work. Missing evidence stays missing.
B is a successful simplification, not a failed A disguised as success. C is a legitimate resource decision.
Broader epics spanning days/devices are a later extension: only explicit shared issue identity can
group available evidence, while attempts and unknown continuity remain separate. No cross-device
claim can be made from the current one-device capture.

The bet: explicit links plus attested delivery can save explanation time without a general-purpose
classifier. Strongest counterargument: a plain issue evidence list may already supply all the value.
Alternatives ranked: evidence-linked companion; plain issue list; existing capture/GitHub only;
semantic boundary detector (deferred, more uncertainty and maintenance). We compare A with B,
not only with an empty baseline.

## Phase 0: pin the trial

**Goal:** an independently reviewed, reproducible trial with a fixed decision rule.

- [ ] Re-run focused runtime/CLIO controls and verify the nonempty frozen capture/window against
  [RUN15](../../TESTS-RESULTS/2026-09-16+GH-232-RUN15/SUMMARY.md); freeze #508, #568 and #623.
- [ ] Record baseline membership: 288 prompts, nine journeys, 212 unassigned; distinguish 47 dated
  retained fields, 12 whole-prompt matches and eight unique original-journey attachments. These
  are coverage counts, not actions completed or accuracy. Recompute rather than assuming them.
- [ ] Obtain Claude Code Fable low-effort plan QA through relay-xyz. Record exact model/effort,
  verdict and exit; allow one remediation and one re-review. If the harness gate is unavailable,
  record a same-model, tools-disabled full-plan review as an advisory fallback and keep the
  automation verdict separate. Failed/unavailable model review stays a blocker; a model PASS
  never becomes a clean relay approval or a silent model substitution. Any future driven work
  still requires its automation gates.
- [ ] Freeze the Phase 3 usefulness rule before generating the new views. No benchmark claims
  without operator-established labels; assistant diagnostics are not ground truth.

### Phase 0 — QA checklist

- [ ] Nonempty input and source/hash/cutoff controls run; missing source fails rather than passes.
- [ ] Reviewer findings have dispositions; execution starts only after plan review passes.
- [ ] Current recon and prior failed guards are cited; no previously rejected prose allowlist returns.

## Phase 1: show the missing explicit evidence

**Goal:** show all explicitly issue-linked prompts, including unassigned ones, without changing starts.

- [ ] Extend the existing replay renderer with an optional issue-evidence section using
  `qualified_references` and existing rows. Original chat/candidate views, IDs, starts and orphan
  membership remain unchanged. The view is a projection, not another collector/database or UI.
- [ ] For #568, display its three explicit mentions: one assigned and two unassigned. Preserve
  different agent/chat attempts; label the earlier same-chat mention “no detected prior start in
  this window.” Never backfill from a later start or claim no task existed before the cutoff.
- [ ] Render readable intent lines and event/retrieval times separately using existing redaction.
  A prompt mentioning several issues may appear under each with its same ID and an “also mentions”
  label; never treat it as a bridge or double-count it in unique totals. Non-explicit text stays unresolved.
- [ ] Add synthetic red controls: wrong-repository issue, ambiguous bare number, future-start
  backfill, same issue/different chats, missing session, multi-issue mention and empty source. Include
  positive qualified issue/PR controls. Witness the failing controls before implementation.

### Phase 1 — QA checklist

- [ ] Original source/prompts/starts/grouping are exactly unchanged in the frozen comparison.
- [ ] #568's two missing mentions are visible but still unassigned; unknown session never fabricated.
- [ ] Wrong-repository and unresolved references attach zero events; red controls retained under
  `TESTS-RESULTS/<UTC-date>+GH-232-OUTCOME/` with synthetic primitives and console output.
- [ ] Private publisher still rejects existing output, verifies source prefix and uses 0700/0600.

### Phase 1 — batch result

Implemented the optional `--issue-evidence` renderer projection. It shows typed, qualified
XYZ Forge issue mentions from every eligible prompt, including unassigned ones; other-repository,
pull-request and ambiguous bare-number references cannot become trial-issue identities. Separate
captured chats have local attempt labels; unknown sessions stay unknown. Multi-issue mentions
share their original prompt ID, show “also mentions” and contribute once to the unique total.
Displayed intent is a redacted excerpt (up to 500 characters), not a new summary or full-text export.

The frozen enriched bundle and entire old preview prefix remain exactly unchanged apart from the
opt-in flag and appended section. All three #568 mentions are now visible; two remain unassigned.
The new view adds no issue-to-PR closing links. Full app checks still fail on missing dependencies;
no merge/deployment or independent implementation approval. See the retained
[batch receipts](../../TESTS-RESULTS/2026-09-16+GH-232-OUTCOME/SUMMARY.md#phase-1-implementation-batch).

## Phase 2: verify delivery relationships

**Goal:** link issue histories to PR delivery only when an authoritative relationship exists.

- [ ] First inspect existing `github_knowledge`/`github_reconciliation` and read-only adapter/link
  contracts from [the recon](../4-MISC/GH-230-RECON.md). Read the current relevant functions before
  planning their extension. If the local index lacks evidence, use the already retained metadata
  for the trial only; report missing data instead of creating a live fetcher/schema.
- [ ] Add only the smallest read-side trial composition for typed canonical PR closing-issue
  relationships: #535→#508, #581→#568, #640→#623. Preserve source and retrieval receipts, deduplicate
  artifact/event identity, and restrict event time to the frozen window. An ordinary mention or
  similarity match cannot establish delivery. Any identity conflict abstains visibly.
- [ ] Test negative cases alongside #567/#589 (merged PR while issue remains open), #608 (direct
  closure without inventing a PR), and #609/#626 (shared delivery without merging child tasks).
  Preserve #508's later superseded verdict; closure is not fulfillment of a changing overall goal.
- [ ] Produce three compact histories in the existing private Markdown output, with evidence
  references and explicit “deployment unknown.” If facts are unavailable, output the evidence list
  and gap instead. No model is needed for this acceptance criterion.

### Phase 2 — QA checklist

- [ ] The implementation owner has recorded a fresh bounded recon of the actual link consumers;
  this is a Phase 2 entry gate before any adapter/composition change.
- [ ] Every attached PR relationship has canonical repo/type/number and an attested closing link.
- [ ] Deliberately swapped issue/PR identity fails; open/shared/direct/superseded controls run.
- [ ] No capture/index writes, API fetch, new collector, live notes or vault publication.
- [ ] Current independent implementation review passes; any wrong attachment blocks progression.

## Phase 3: test usefulness and choose the ending

**Goal:** decide A/B/C from a small practical review, without an expensive labeling project.

- [ ] Show A's three histories beside B's plain explicit issue-evidence lists. Ask the operator once
  whether each helps explain/resume the work, whether the story is more useful than the list, and
  whether anything is misleading. Optional reply per case: useful / list is enough / misleading.
  No response means usefulness unconfirmed; do not substitute an AI reviewer for the operator.
- [ ] Decision rule for this pilot: A remains eligible if at least two of three histories are useful,
  the operator prefers the story over the list for at least two, and no unsupported factual claim
  or misleading connection remains. These thresholds are a product choice, not statistical proof.
  If B helps but A fails these conditions, choose B. If neither helps after one focused correction,
  choose C. Missing source or unresolved privacy authority blocks the trial rather than proves C.
  Any “misleading” reply fails A for that sample. One focused correction is allowed; A can qualify
  only after the operator confirms it is no longer misleading. Otherwise choose B/C as above.
- [ ] If A qualifies, repeat on three explicitly linked tasks from a second disjoint captured period
  with unchanged rules. Same two-of-three usefulness/preference rule; zero unsupported remaining
  claims; at most one focused correction. If the second sample is absent, A remains unconfirmed.
  Track repair effort and missing coverage; do not broaden grammar to rescue the result.
- [ ] Publish the selected ending, limitations, public-safe primitives/receipts and operator decisions;
  update #232/#210/#230 and #231. If A/B succeeds, hand off a separately scoped integration issue.
  #232 closes when the chosen ending, evidence and remaining blockers have been documented—not
  merely because tests pass. No automatic merge/deployment is part of this planning task.

### Phase 3 — QA checklist

- [ ] Actual operator feedback, or its absence, is recorded honestly for both A and B.
- [ ] The frozen rule selects exactly one ending or explicitly leaves it blocked/unconfirmed.
- [ ] Known wrong joins or unsupported completion/deployment claims prevent A; gaps stay visible.
- [ ] Doctor, full `tests/`, applicable PDDA and final review pass before a merge is considered.
  Current missing-dependency failures keep #231 draft; fixing them is separate scoped work.
  The offline A/B/C usefulness decision and experiment handoff can complete independently of
  those unrelated integration fixes; selection is not permission to merge or deploy.

## Boundaries and handoff

Plan QA: Fable 5.1 (`claude-fable-5-1[1m]`) with native `--effort low` returned PASS on the complete
plan, tools disabled, task-local Claude Code 2.1.273. It raised three non-blocking clarifications
above. The global 2.1.29 client was not changed. Full relay-harness validation was capped at
20 minutes without a final verdict; the clean automated relay was not driven. A prior file-reading
advisory exhausted its unchanged $0.50 per-call limit with no verdict. No model substitution or
budget increase. [Review and dispositions](../../TESTS-RESULTS/2026-09-16+GH-232-OUTCOME/QA.md).

Source/replay trace: `load_prompts` → `qualified_references` → `group` → `render` → `publish`.
The current replay source was read in full; the existing recon covers capture/storage/export.
Phase 2's broader link consumers need a fresh bounded trace before changes, not guessed file scope.
Blast radius: optional private preview/evidence composition only. Easy rollback: stop the optional
view or revert scoped commits; no source/schema rollback. Shield: opt-in projection. Tripwire:
wrong attachment, source mutation, private egress or missing input stops progression immediately.

Use debug-mantra during execution: reproduce, trace, falsify, cross-reference the run ledger.
Execute in four-step batches of at most 15 minutes, committing verified scoped results without
asking between safe steps. One focused correction per phase; no endless review/repair loop. Stop
at the batch cap with receipts and a singular next step. Planning/QA now does not authorize build.

Non-goals: universal intent classifier, next-action training, inferred issue closure/deployment,
new database/collector, automatic live publication, source-capture migration or unbounded graph.
Terra summaries are optional later, only through the existing approved privacy/budget/output seam;
its current output coupling is unresolved. Missing Terra integration must not block factual Markdown.
Branch creation time, relay success and marathon completion require authoritative artifacts; prompts
are intent only. Trace those adapter contracts in a separate follow-up before adding them.
