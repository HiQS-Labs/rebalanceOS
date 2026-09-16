---
gh_issue: 210
source: https://github.com/HiQS-Labs/rebalanceOS/issues/210
title: Gemini 3.8 Flash Low versus Terra Low synthetic classifier comparison
status: Active — protocol frozen before inference
created: 2026-09-15
updated: 2026-09-15
owner: Mac Studio comparison arm
goal: Compare the two CLI-backed classifier arms on an identical, evidence-bound synthetic contract without private-data egress.
branch: feat/gh210-terra-work-synthesis
effort: 2
complexity: 3
risk: 2
phases: 2
context_tags: [daily, classifier, model-comparison, synthetic-evaluation]
---

# GH-210 — Gemini 3.8 Flash Low versus Terra Low

## Status

| What was just completed | What's next |
|---|---|
| Independent pre-run review findings were resolved; final review approved revision 2, and all negative controls pass before inference. | Execute the frozen revision-2 matrix and publish the complete campaign under `TESTS-RESULTS/2026-09-15+GH-210/`. |

## Table of contents

1. [Question and bet](#question-and-bet)
2. [Phase 0 — Prior art and protocol](#phase-0--prior-art-and-protocol)
3. [Frozen dataset and arms](#frozen-dataset-and-arms)
4. [Metrics and decision rule](#metrics-and-decision-rule)
5. [Phase 1 — Execution and publication](#phase-1--execution-and-publication)
6. [Threats fixed before inference](#threats-fixed-before-inference)

## Question and bet

Can the end-to-end Agy CLI arm `gemini-3.8-flash-low` match or exceed the existing
Codex CLI arm `gpt-5.6-terra` at Low reasoning on the evidence-bound work-state
classification contract, while preserving schema validity, citation integrity, and
completion-claim safety?

**Bet:** Flash Low will be competitive on classification correctness and may have a
better latency profile. **Falsifier:** it loses materially on paired correctness,
emits unsupported evidence/completion claims, fails schema enforcement, or has no
operational advantage large enough to justify another provider path.

This is an end-to-end **CLI-arm** comparison, not a base-model benchmark. The Codex
and Agy agent envelopes differ, so token counts and latency include their respective
clients. No private Rebalance, CLIO, repository, calendar, reminder, email, or other
operator evidence may enter this campaign.

Reversibility: **Easy** — synthetic calls and a results-only branch; no runtime setting
or scheduled job changes.

## Phase 0 — Prior art and protocol

The existing `TESTS-RESULTS/2026-09-12+GH-210/` harness is extended rather than
replaced. Its 12-case battery established basic schema/correctness capability but was
too small, mostly easy, single-shot, and contained an ambiguous `blocked` expectation.
This campaign keeps its isolated temporary workspaces, randomized ordering,
checkpointed JSONL receipts, and deterministic scoring, while adding balanced states,
repeat attempts, adversarial evidence, a dumb baseline, and paired inference.

No new collector, model service, store, or production query path is introduced.

### Phase 0 QA gate

- [x] Full model identifiers and CLI versions are recorded by the runner.
- [x] Dataset, expected labels, prompt, schema, attempts, seed, metrics, and decision
  rule are committed before the first model call.
- [x] Primitive rows are checkpointed immediately and contain no private evidence.
- [x] An independent reviewer examines the protocol before inference; the verbatim
  transcript is retained under the campaign's `qa/` directory.
- [x] The scorer is witnessed red by deliberately corrupting one expected result and
  observing a strict-exact decrease, then restored before the real run.

## Frozen dataset and arms

Artifact: `TESTS-RESULTS/2026-09-15+GH-210/battery.json`.

- 24 synthetic cases, balanced across `planning`, `implementation`, `verification`,
  `blocked`, `complete`, and `unknown` (four cases each).
- Cases include stale evidence, intent-only evidence, simultaneous repositories,
  distractors, contradictory chronology, prompt injection, external blockers, failing
  tests, merge/deploy completion, and must-not-claim-complete controls.
- Ground truth is by construction: each synthetic case explicitly defines the current
  event chronology and the evidence IDs that support the expected state. Ambiguous
  cases are excluded rather than adjudicated after outputs are visible.
- Focus precedence is frozen: within the current window, substantive source/test/
  deploy work outranks an incidental cosmetic documentation edit; newer evidence
  updates the same work chain; two simultaneous substantive repositories with no
  distinguishing evidence require `unknown`. Stale evidence outside the declared
  current window cannot establish current focus.
- Citation scoring accepts only the predeclared evidence sets in `acceptable_evidence_sets`.
  This permits a minimal sufficient terminal event (for example, the merge itself) or
  the complete immediate causal chain when either is defensible. No acceptable set is
  added after inference.
- Two fresh, state-isolated attempts per case and arm: 24 × 2 × 2 = 96 model calls.
- Randomized job order with seed `21038`; no continuation/session reuse or retry for a
  better answer.
- Identical prompt, JSON schema, 45-second deadline, and empty temporary workspace.
- Terra arm: `gpt-5.6-terra`, Low reasoning, `codex exec`, provider-enforced schema.
- Flash arm: `gemini-3.8-flash-low`, `agy --print`, provider-enforced schema exposed by
  Agy. The arm consumes Agy's validated `structured_output`, never its display string.
- Baseline: a frozen deterministic keyword/recency heuristic with no model calls.

The output contract is exactly:

- `project`: selected repository or `unknown`
- `state`: one of the six frozen states
- `completion_claimed`: true only for attested completion
- `evidence_ids`: exactly the supplied IDs supporting the selected current state
- `abstain`: true only when the primary focus is unsupported

## Metrics and decision rule

Primary quality metric: per-attempt **strict exact** over all five contract fields.
Secondary metrics: field-level correctness, schema validity, unsupported evidence-ID
rate, false completion claims on non-complete cases, abstention correctness, and
within-arm two-attempt consistency. Operational metrics: completion/failure counts,
p50/p95/max wall time, and the CLI-provided token receipt. Token counts across clients
are descriptive, not a provider-cost comparison.

Paired inference clusters repeats by case. For each case, strict accuracy is averaged
over its two attempts. The scorer applies a two-sided exact Wilcoxon signed-rank test
to non-zero paired case differences and reports mean paired effect in percentage
points. No test-set prompt edits, label changes, dropped failures, or retries are
allowed after inference begins.

Predeclared decision rule:

1. An arm is **ineligible** if provider acceptance or local contract validity is below
   100%, it cites an unknown evidence ID, or it makes any false completion claim on
   the must-not-complete cases.
2. Call a quality winner only if **both arms are eligible**, the winner improves mean
   strict exact by at least 10 percentage points, and the paired two-sided p-value is
   below 0.05.
3. If quality has no declared winner, call an **operational lead** only when both arms
   are eligible and one lowers p95 wall time by at least 25%. This nominates a private
   shadow comparison; it does not replace the production arm.
4. Otherwise report no measured winner and retain Terra Low. Synthetic evidence alone
   cannot authorize production replacement, private egress, or a schedule/config change.

The constant/deterministic baseline contextualizes task difficulty but cannot win the
provider decision.

## Phase 1 — Execution and publication

1. Run the independent protocol review and save it verbatim. -> expect no unresolved
   blocker before calls begin.
2. Run the scorer's deliberate-corruption negative control, retain console evidence,
   restore the frozen battery, and verify its checksum. -> expect strict exact to drop.
3. Execute the randomized 96-call matrix with a 45-second per-call timeout and
   immediate JSONL checkpoints. -> expect exactly 48 rows per arm; failures remain in
   the denominator.
4. Run the deterministic scorer and recompute every summary number from primitive
   rows. -> expect one aggregate JSON plus mismatch records and paired statistics.
5. Publish `SUMMARY.md`, primitive JSONL, raw console output, scripts, frozen inputs,
   checksums, and QA transcript. -> expect no credentials, private evidence, or local
   absolute paths.
6. Comment GH-210 with the bounded conclusion and links. -> expect synthetic scope,
   invocation-envelope caveat, and no unmeasured cost claim.

### Phase 1 QA gate

- [ ] Non-empty battery and exactly 96 primitive attempt rows.
- [ ] Every input case receives two attempts from both arms.
- [ ] Aggregates reproduce from the published primitive.
- [ ] Threats to validity and every protocol deviation are explicit.
- [ ] `utils/pdda/pdda.sh run` passes for the documentation changes.

## Threats fixed before inference

- Synthetic cases may not represent noisy real work windows or operator preference.
- The author of the harness also constructed the synthetic ground truth; independent
  pre-run protocol review limits but does not remove that bias.
- Two attempts measure only coarse response variance.
- CLI agent envelopes differ and may dominate tokens/latency; this is intentional for
  the deployable-arm comparison but prevents a base-model claim.
- Agy does not expose billed cost in the capability receipt, so this campaign cannot
  make a cost-winner claim without a separately verified price/usage contract.
- Twenty-four paired cases have limited power. Failure to reject equality is not proof
  of equivalence.

## Pre-run review disposition

Independent reviewer: `gpt-6-astra` Low via Codex CLI 0.153.4, read-only session
`01a0a7f8-3f50-7b62-8160-2aac84c5da48`. Verbatim final review:
`TESTS-RESULTS/2026-09-15+GH-210/qa/protocol-review.md`.

- **Accepted blockers:** explicit focus precedence plus acceptable citation sets;
  malformed envelopes/values become checkpointed failed attempts; both arms must pass
  safety eligibility for any comparative winner.
- **Accepted shoulds:** provider acceptance is distinguished from stricter local
  contract validation; sanitized raw and parsed provider receipts plus frozen hashes are retained
  and checked; consistency normalizes citation order and never counts two failures as
  agreement.
