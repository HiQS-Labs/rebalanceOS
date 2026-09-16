# Fable outcome-plan QA

Primary review model: `claude-fable-5-1`, pinned as `claude-fable-5-1[1m]`.
Reviewed plan revision: `3566534`, before the requested non-blocking clarifications and the
disclosed operational-fallback note. No claim of a subsequent review of those edits.
Request: native `--effort low`, task-local Claude Code 2.1.273, tools disabled, full plan supplied.
No global installation change. Exact successful model identified in native `modelUsage`.
The CLI also reports ancillary `claude-haiku-4-5-20251001` usage; it was not the plan reviewer.

**Plan-only verdict PASS; automated relay not approved.** The relay-xyz locator/harness setup and
Claude shim tests ran, but full harness validation had nonzero parallel cases and a live-worker
test that did not finish within the 20-minute cap. It was stopped (exit 143); no final global verdict
or clean driven relay. Central working tree and HEAD remained unchanged. The owned leftover
fixture worker was terminated. No harness defect was fixed as part of this documentation task.

The global 2.1.29 CLI's first probe was rejected: the server requires 2.1.251 or newer for Fable.
The temporary newer CLI verified the first-party subscription route through the shipped helper.
A file-reading advisory through the shipped consult fallback then exhausted the unchanged $0.50
per-call budget flag (exit 5 at the harness level) with no verdict. Its CLI metadata reports
list-price-equivalent usage of $0.582801, so that flag must not be described as a hard spend ceiling.
The lean tools-disabled retry completed (exit 0), reported list-price-equivalent usage $0.168737,
and returned the verdict below. Subscription usage metadata is not an invoice. No budget flag
increase, extracted credentials, private prompt packet, model substitution or runtime build.

This review sweeps the plan only; it does not independently validate the implementation or operator
usefulness. The successful retry used the native CLI advisory fallback, not a completed relay loop.

## Reviewer response — verbatim

VERDICT: PASS

Swept file: yes (plan only). No tools used; no runtime validation performed; nothing here constitutes relay approval.

**Three endings and ideal choice**
- A/B/C are distinct and each has a stated trigger. A is correctly framed as bounded: "It is not a promise to infer every action or reconstruct all work. Missing evidence stays missing." B is explicitly "a successful simplification, not a failed A disguised as success." C is "a legitimate resource decision." Good.
- The ideal justification ("answers 'what did this work turn into?' with little extra effort") is plausible; the plan names the strongest counterargument ("a plain issue evidence list may already supply all the value") and commits to comparing "A with B, not only with an empty baseline." That is the right comparison.
- Minor: cross-device/epic scope is deferred honestly ("No cross-device claim can be made from the current one-device capture").

**Scope**
- Tight: "The view is a projection, not another collector/database or UI"; Phase 2 limited to three typed relationships (#535→#508, #581→#568, #640→#623) and "report missing data instead of creating a live fetcher/schema."
- Non-goals list is explicit and excludes the classifier, training, inferred closure/deployment, live publication.
- Finding (low): Phase 2 says broader link consumers "need a fresh bounded trace before changes, not guessed file scope" but does not state who produces it or that it is a Phase 2 gate. Suggest adding it to the Phase 2 QA checklist.

**Safety**
- Source immutability repeatedly asserted ("Original source/prompts/starts/grouping are exactly unchanged"); publisher hardening retained (0700/0600, rejects existing output); tripwire covers "wrong attachment, source mutation, private egress or missing input."
- Red controls listed concretely (wrong-repo, bare number, future-start backfill, missing session, multi-issue, empty source) with "Witness the failing controls before implementation." Good.

**Usefulness comparison and operator feedback**
- Decision rule is frozen before views are generated (Phase 0) and stated numerically ("at least two of three histories are useful… prefers the story over the list for at least two… no unsupported factual claim"). Explicitly "a product choice, not statistical proof."
- Operator is the sole usefulness authority: "do not substitute an AI reviewer for the operator"; "No response means usefulness unconfirmed." This correctly prevents AI judgments from being treated as operator feedback.
- Finding (medium): the "misleading" option per case is not wired into the rule as clearly as "useful/list is enough." Suggest stating that any "misleading" reply on a history disqualifies A for that sample, matching the "no unsupported factual claim or misleading connection remains" clause.

**Stop conditions**
- Batch cap ("at most 15 minutes… Stop at the batch cap"), "One focused correction per phase; no endless review/repair loop," and "Planning/QA now does not authorize build" are clear.
- Second-sample requirement for A ("If the second sample is absent, A remains unconfirmed") prevents single-sample overclaim.

**Acceptance loopholes checked**
- Test-passing ≠ closure: "#232 closes when the chosen ending, evidence and remaining blockers have been documented—not merely because tests pass." Good.
- Review unavailability: "Unavailable/failed review stays a blocker, never becomes approval or a silent model substitution." Good.
- Baseline counts flagged as "coverage counts, not actions completed or accuracy. Recompute rather than assuming them." Good.
- Finding (low): "Doctor, full `tests/`, applicable PDDA" while "Current missing-dependency failures keep #231 draft" — clarify that A/B/C selection can complete independently of #231's dependency fixes, so the ending decision isn't blocked on unrelated CI.

**Dispositions requested**: the two low and one medium findings above; none block PASS.

## Producer dispositions

1. Implemented: the implementation owner must record the fresh link-consumer trace; explicit
   Phase 2 entry gate, not merely an eventual source read.
2. Implemented: any misleading history fails A for the sample; one focused correction requires
   operator confirmation before it can qualify again. No silent repair counts as usefulness.
3. Implemented: offline ending selection/handoff can finish independently of integration fixes;
   merge/deployment still require their own passing gates.

The reviewer explicitly stated none block PASS. These requested clarifications were incorporated;
no additional claim of a second review or automated approval. Broader source validation was not
performed by this plan-only review. The changed operational fallback is disclosed separately in
the plan; it was not part of the original reviewed text.
