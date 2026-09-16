---
title: CLIO journey follow-up
status: In progress
created: 2026-09-16
updated: 2026-09-16
owner: Codex
goal: Improve reference trust and reconstruct evidence-linked journeys in bounded batches.
gh_issue: 232
source: https://github.com/HiQS-Labs/rebalanceOS/issues/232
doc_type: research
effort: 2
complexity: 2
risk: 2
phases: 1
---

# CLIO journey follow-up

## Status

| What was just completed | What's next |
|---|---|
| Separate formatting fix and conservative mode pass; three explicit issue histories reconstructed | Test one qualified task transition, then review current implementation |

The [GitHub issue](https://github.com/HiQS-Labs/rebalanceOS/issues/232) owns the actionable plan,
if/then scenarios, acceptance checks and batch limits. This is a continuation of
[#230](https://github.com/HiQS-Labs/rebalanceOS/issues/230), under
[#210](https://github.com/HiQS-Labs/rebalanceOS/issues/210), not a replacement for their evidence.
Implementation remains in draft [#231](https://github.com/HiQS-Labs/rebalanceOS/pull/231).

## Sustained continuation — eight steps

The operator authorized separate clear fixes followed by uncertain-project handling and a longer
plan. This continuation supersedes batch 1's exhausted repair cap; it is a new scoped approach.
Reversibility is Easy: optional replay policy and private projections. No database format change.
The bet is that conservative links plus visible gaps can yield useful history; too few explicit
references may limit coverage. No claim that unresolved candidates are correct labels.

1. Pin and fix formatted typed PRs and labeled AgentChorus/agent2agent IDs separately → completed;
   five failures witnessed before the fix, valid closed PR and large issue-number controls preserved.
2. Trace consumers and add optional explicit-links mode → completed; grouping and rendering read
   only `refs`, while `unresolved_refs` remains diagnostic. No project-name word registry.
3. Run focused controls and the frozen replay → completed; source/window/prompt/start identities
   and child membership unchanged. Preserve original previews. Compare coverage, not accuracy.
4. Inspect evidence availability through the existing read-only adapter and retained snapshots →
   local index still supplies zero target events. Record which explicit URLs have usable snapshots;
   if missing, limit reconstruction to the attested subset rather than fill gaps from prompts.
5. Reconstruct 2–3 explicit cases from retained facts → proceed only where URL identities and
   event timestamps are available; show intent, creation, merge/closure and unknown deployment.
   No source match means a readable coverage report instead. Shared delivery preserves child tasks.
6. Test one explicit task transition within a chat → if it names a new qualified issue, offer a
   separate candidate segment alongside the original view. Ambiguous “next” wording is flagged
   for review. Read grouping fully before editing; no broad semantic detector.
7. Review the current small implementation and preview rules → one independent review plus at
   most one focused remediation. Dependency-blocked app gates keep #231 draft. Reviewer unavailable
   means documented outstanding review, not an approval or endless review loop.
8. Publish receipts, update #232/#230/#210 and #231, and recommend continue/simplify/park → each
   independently verified implementation gets a scoped commit/push. Stop after the batch's two-hour
   cap or at a requested merge/deployment, new private egress/spending, capture/schema change, or
   new ingestion system. Safe missing-evidence fallbacks may finish without further user nudges.

If explicit links provide adequate examples, continue steps 5–7. If coverage is too sparse, retain
the replay as a conservative preview and scope evidence availability next. If a valid explicit link
is lost or an unresolved mention attaches an event, fix that focused defect before progression.
No plan step requires resolving a project name by guessing which GitHub number happens to exist.

## Evidence and next batch

Continuation findings: the optional explicit-links mode retains 21 qualified URL occurrences and
71 unresolved candidates on the same 288 prompts/nine journeys. Fifty focused tests pass.
Existing index coverage remains absent; retained GitHub snapshots supported separate histories
for #508/535, #568/581 and #623/640. Each preserves explicit prompt mentions and merge/closure times;
deployment remains unknown. #508's superseded verdict remains important historical context.
See [continuation receipts](../../TESTS-RESULTS/2026-09-16+GH-232-BATCH2/SUMMARY.md).
Steps 1–5 have progressed; step 6 and current independent review remain outstanding. No broad
task-boundary change or automated snapshot import was made. This is a longer resumable plan,
not a claim that all eight steps are complete.

See the [source recon](../4-MISC/GH-230-RECON.md),
[original plan](../2-WORKING/GH-230-CLIO-JOURNEY-SPIKE.md), and
[reference rerun](../../TESTS-RESULTS/2026-09-16+GH-230/REFERENCE-RERUN.md).
The replay retained 288 prompts and nine journeys. Reference extraction changed 24 prompts;
partial review found at least four incorrect additions across three prompts. These are not
accuracy measurements. No automatic-linking promotion is justified yet.

The next batch progresses from synthetic regression cases to a minimal abstention guard,
then the identical frozen replay, then a conditional 2–3-journey reconstruction using retained
GitHub evidence. Maximum two repair passes and two hours; report failures instead of expanding
scope. No source capture changes, new collector, unguarded model calls, merge or deployment.

## Frozen protocol — batch 1

Baseline: parser f8a2078, retained GH-230 capture and cutoff 2026-09-16T04:25:38Z.
Compare exact reference sets, not model scores. Preserve capture hash, prompts, start decisions,
window, device/session metadata, assigned prompt membership and source coverage. Parent identity
may change when a spurious issue is removed; report that separately rather than hiding it.
Publish synthetic tests and non-identifying per-case changes under TESTS-RESULTS/2026-09-16+GH-232.
Raw prompts and reviewer-only source excerpts stay in private ignored scratch, never in QA packets.

Decision rule, frozen before rerun: all synthetic negative and positive controls must pass, and
every changed reference must be inspected for known-good losses and unresolved/wrong additions.
Include the prior 24 changed cases, not just newly affected cases. Any known-good loss or wrong
new association OR unresolved retained/new association in the reviewed cases blocks progression.
Every changed reference (including all prior 24 cases) needs a recorded disposition. Intentional
abstention is reported, not counted as a correct link. Maximum two narrow repair passes, two-hour total batch cap.
If the reference gate passes, inspect 2–3 candidate journeys with retained GitHub evidence; if it
fails, step four is a failure report with a narrower next proposal, not a forced reconstruction.
Assistant inspection is diagnostic, not human ground-truth labeling; no accuracy/generalization
claim or statistical comparison. Human usefulness review remains outstanding.

Grounding: load_prompts → references → group → render. Only references changes in this batch;
no settings, timing or capture knobs affect this pure function beyond text and verified context.
Ranked explanations: (1) checkout context overrides explicit foreign-project wording,
(2) typed numbers include planned ordinals, (3) markup/non-GitHub hashes escape typed consumption.
Disproof controls retain explicitly qualified URLs, valid typed IDs and formatted PR identities.
HiQS literal-reference projection was inspected; it resolves IDs against its separate database,
does not handle these typed/ordinal distinctions, and is not a replacement for this replay seam.

## Verification

Protocol review: Agy timed out without findings (driver exit 7). The bounded Codex fallback found
the unresolved-addition gap above; its FAIL findings are retained in
../../relay-system/2026-09-16/gh232-protocol-codex.md. The run itself exited 6 because a generated
gate-evidence directory appeared during containment; it is not an approved relay. The blocker was
addressed before the replay by strengthening the gate. No further protocol-review loop this batch;
current implementation QA remains required before promotion.

## Batch 1 outcome

All four steps were attempted in order, with step four taking its explicit failure-report branch.
The first guard passed its synthetic suite but lost known-good references in the frozen replay.
Five new regression cases pinned that overreach. The second/final guard still failed one synthetic
case and lost a valid “CLOSED PR” reference in real input; no third pass and no new reconstruction.
Both runs preserved 288 prompts, nine journeys and 212 unassigned prompts. All 24 affected cases
were inspected, including the prior parser's changes; retained bare-hash type conflicts and
unresolved candidates remain. These are assistant diagnostic findings, not human accuracy labels.

The [campaign](../../TESTS-RESULTS/2026-09-16+GH-232/SUMMARY.md) retains both runs, all-case disposition
counts, witnessed failures, comparison controls and the rejected patch. Runtime parser and tests
were restored to the pre-batch state; its 41 focused tests pass. Six comparator controls pass.
Doctor and full-suite collection remain blocked by missing dependencies. PR #231 remains draft.

Next bet: isolate the unambiguous formatting/chat-ID fixes before attempting any representation
change for uncertain project/type references. Growing a prose-word allowlist was not reliable enough
in this batch. Any later representation change needs the consumers reviewed first; no capture,
database, privacy/budget or deployment expansion is authorized by this result.

Require witnessed failing negative controls, preserved positive controls, unchanged replay input,
review of all changed references, and evidence for every claimed outcome. Earlier Agy approval
does not cover the parser follow-up or this plan. Full application gates remain blocked by
missing dependencies. Filing did not begin implementation; the operator subsequently authorized
this bounded batch. No application readiness claim is permitted while those gates are blocked.
