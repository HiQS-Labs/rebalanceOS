# GH-210 — Gemini 3.8 Flash Low versus Terra Low

| Field | Value |
|---|---|
| Date | 2026-09-15 America/Los_Angeles |
| Tracking issue | [HiQS-Labs/rebalanceOS#210](https://github.com/HiQS-Labs/rebalanceOS/issues/210) |
| Frozen protocol commit | `a8dc188` |
| Systems | Agy CLI 1.2.3 / `gemini-3.8-flash-low`; Codex CLI 0.153.4 / `gpt-5.6-terra` Low |
| Dataset | 24 frozen synthetic evidence-bound work-state cases, two attempts per arm |
| Primitive | [`results.jsonl`](results.jsonl), 96 rows |
| Derived | [`summary.json`](summary.json), [`mismatches.jsonl`](mismatches.jsonl) |
| Instrument | [`run_comparison.py`](run_comparison.py), [`score_comparison.py`](score_comparison.py), [`test_instrument.py`](test_instrument.py) |
| QA | [`qa/`](qa/) |

## Verdict

**No quality winner; retain Terra Low, which is the predeclared operational lead.**

Flash Low's strict-exact score was 40/48 (83.3%) versus Terra Low's 39/48
(81.3%). Clustered by case, Flash's mean paired advantage was only 2.1 percentage
points; one case favored each arm, 22 tied, and the exact two-sided Wilcoxon p-value
was 1.0. This does not clear the frozen rule requiring at least +10 points and p<0.05.

Both arms cleared every safety and contract gate: 48/48 provider-accepted calls,
48/48 locally valid contract outputs, zero unknown evidence IDs, zero false completion
claims, zero malformed/missing usage receipts, and zero failed calls.

Terra Low's p95 end-to-end CLI wall time was 6.409 seconds versus Flash Low's
20.638 seconds. Terra was about 3.22× faster at p95 (69% lower), comfortably clearing
the frozen 25% operational-lead threshold. Synthetic evidence does not authorize a
production replacement; the result supports keeping the current Terra Low arm.

## Headline results

| Metric | Terra Low | Gemini 3.8 Flash Low |
|---|---:|---:|
| Attempts | 48 | 48 |
| Provider accepted / contract valid | 48 / 48 | 48 / 48 |
| Strict exact | 39/48 (81.3%) | 40/48 (83.3%) |
| Project correct | 47/48 | 46/48 |
| State correct | 48/48 | 48/48 |
| Completion flag correct | 48/48 | 48/48 |
| Abstention correct | 48/48 | 48/48 |
| Evidence set correct | 39/48 | 40/48 |
| False completion / unknown citation | 0 / 0 | 0 / 0 |
| Two-attempt consistent cases | 23/24 | 24/24 |
| p50 / p95 / max wall time | 4.560 / 6.409 / 10.118 s | 12.957 / 20.638 / 35.785 s |
| Total measured wall time | 231.122 s | 656.391 s |

The deterministic baseline scored 10/24 strict exact (41.7%), establishing that the
battery was not passed by the frozen keyword/recency heuristic.

## Paired analysis

- Flash-better cases: 1
- Terra-better cases: 1
- Tied cases: 22
- Flash minus Terra mean strict-exact delta: +0.020833
- Exact Wilcoxon signed-rank: `n_nonzero=2`, `W+=2.0`, two-sided `p=1.0`
- Frozen decision: `quality_winner=null`, `operational_lead=terra-low`

The two repeated attempts are clustered before inference; they are not treated as 48
independent cases. No multiple-comparison correction is needed because the protocol
declared one inferential quality comparison. Field scores and latency are secondary.

## Usage receipts

| Receipt field | Terra Low | Gemini 3.8 Flash Low |
|---|---:|---:|
| Input tokens | 952,051 | 1,125,019 |
| Cached/cache-read input | 716,032 | 82,925 |
| Output tokens | 2,099 | 124,096 |
| Reported reasoning/thinking | 120 | 120,821 |
| Agy total-token field | n/a | 1,249,115 |

These are CLI-reported fields, not normalized provider billing units. In particular,
the two agent envelopes differ, and reasoning/thinking may be included in output.
No billed cost was exposed for both arms under a verified common contract, so this
campaign makes **no cost-winner claim**.

## Mismatch analysis

Seventeen attempt rows missed strict exact. Every output still chose the correct
state, abstention flag, and completion flag.

- Most misses were the frozen evidence-set requirement on abstentions. Both models
  commonly returned an empty evidence list with `unknown`/`abstain=true`, while the
  frozen answer required the evidence demonstrating why focus was unsupported.
- C04 exposed a protocol defect: its expected current repo was the newer documentation
  publication, while protocol revision 2 told models that substantive work outranks a
  cosmetic documentation edit. Both arms mostly selected the older substantive merged
  fix, following the written precedence rule. The primary score remains untouched; the
  defect is disclosed rather than repaired after viewing outputs.
- Terra varied on C04 across its two attempts, accounting for its 23/24 consistency;
  Flash was internally consistent on all 24 cases.

The C04 defect and abstention-citation sensitivity do not rescue a quality-winner
claim: the frozen paired result is non-significant and far below the +10-point gate,
while the operational latency lead is large and in Terra's favor.

## Protocol and controls

The protocol, battery, schema, metrics, decision rule, and seed were committed and
pushed at `a8dc188` before inference. Jobs were randomized with seed `21038` and used
fresh temporary workspaces, identical prompt/schema content, a 45-second deadline,
and no retry or continuation. The runner checkpointed each row immediately.

Independent pre-run review initially returned changes required. All blockers and
should-fix findings were applied: focus/citation ambiguity, malformed response and
usage handling, eligibility alignment, frozen-input hashes, normalized consistency,
complete sanitized receipts, timeout evidence, and baseline citation parity. The
final bounded review returned `APPROVE` before model calls.

An independent post-run audit then reproduced the aggregate and mismatch files from
the primitive, verified all 96 raw receipts against their parsed outputs and usage,
checked the frozen decision rule and disclosed limitations, and returned `APPROVE`.
Its receipt is retained in [`qa/results-review.md`](qa/results-review.md).

The instrument's witnessed negative controls are in
[`instrument-console.txt`](instrument-console.txt): one deliberate wrong completion
reduced Flash's fixture score from 48/48 to 47/48, malformed attempts remained in the
denominator and failed eligibility, and parser/usage/sanitization failures were
exercised for both arms.

## Deviations and threats to validity

- **Ground truth is synthetic and author-constructed.** It measures a bounded
  classifier contract, not noisy real-work usefulness or operator preference.
- **C04 contradicts revision-2 precedence.** Absolute exact rates are therefore not a
  clean estimate of semantic classifier accuracy. The frozen comparison is retained.
- **Abstention citation policy is brittle.** Empty citations are reasonable for an
  abstention even though the frozen answer required explanatory evidence IDs.
- **Only 24 case clusters and two attempts per arm.** Power and variance estimates are
  limited; p=1.0 is not evidence of equivalence.
- **Different CLI envelopes.** Latency and tokens measure deployable end-to-end arms,
  not isolated base models. Network/provider conditions were not counterbalanced
  beyond randomized serial order.
- **No private historical windows.** Privacy was preserved, but product replacement
  remains untested. A later private shadow campaign needs explicit authorization.
- **No common billed-cost receipt.** Token fields are descriptive only.

## Reproduction

```bash
python3 TESTS-RESULTS/2026-09-15+GH-210/test_instrument.py
python3 TESTS-RESULTS/2026-09-15+GH-210/run_comparison.py \
  --output TESTS-RESULTS/2026-09-15+GH-210/results.jsonl \
  --console TESTS-RESULTS/2026-09-15+GH-210/run-console.txt
python3 TESTS-RESULTS/2026-09-15+GH-210/score_comparison.py \
  --input TESTS-RESULTS/2026-09-15+GH-210/results.jsonl \
  --output TESTS-RESULTS/2026-09-15+GH-210/summary.json \
  --mismatches TESTS-RESULTS/2026-09-15+GH-210/mismatches.jsonl
```

The runner refuses to overwrite a non-empty primitive. Reproduction therefore needs
a new output path or a clean checkout; published records must not be rewritten.
