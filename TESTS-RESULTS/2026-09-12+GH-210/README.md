# GH-210 Phase 0 capability receipt — Terra with ad-hoc Muse comparator

Date: 2026-09-12  
Device: Noel's Mac Studio, 64 GB  
Branch: `feat/gh210-terra-work-synthesis`  
Baseline: `8a5df5ca26b51a7dcb0acc455af0d7bba8c18794` (`rebalance 0.87.2`)  
Codex CLI: `0.153.4`

## Scope and caveat

This is a synthetic capability probe, not the frozen evaluation campaign and not a
quality grade. No Rebalance, CLIO, repository, calendar, reminder, email, or other
private work evidence was sent. Private-data egress remains unapproved and disabled.

After the initial Terra receipt, the operator requested an **ad-hoc pivot** to add
`muse-spark-1.3-contributor` as a secondary comparator. The pivot changes neither the
frozen-campaign gate nor the intended Terra product decision. It answers only whether
the native Muse route can satisfy the same trivial synthetic classification contract.
The Contributor tier may use content, including inter-session messages, for product
improvement, so this arm is synthetic-only unless a later explicit policy decision
authorizes a different payload.

The commands used an empty temporary directory, read-only sandbox,
`--ignore-user-config`, `--ignore-rules`, `--ephemeral`, and a prompt that prohibited
tool use. The JSONL receipts contained only an agent-message event and no tool event.

Muse used its native CLI in empty temporary workspaces with session logging, web tools,
foreign personal context, shell, writes, parallel tool calls, and interactive approval
disabled. Muse has no forced-output-schema CLI flag, so it was instructed to emit the
same shape and the returned JSON was validated locally against the same schema. That is
a weaker generation-time guarantee than Terra's provider-enforced Structured Output.

## Contract checked

- Primary model: `gpt-5.6-terra`; ad-hoc comparator:
  `muse-spark-1.3-contributor`
- Reasoning settings: `low` and `medium` for both models
- Noninteractive invocation: `codex exec` for Terra; native `muse exec` for Muse
- Forced output: [`p0-capability-schema.json`](p0-capability-schema.json)
- Input: two synthetic evidence IDs describing a test edit followed by a passing test
- Expected classification: repo `example/widgets`, phase `verification`, both evidence
  IDs, and no abstention

Official OpenAI documentation retrieved on 2026-09-12 states that GPT-5.6 Terra
supports Low and Medium reasoning plus Structured Outputs. It lists token prices of
$2.00 per million input tokens, $0.20 per million cached input tokens, and $12.00 per
million output tokens:
<https://developers.openai.com/api/docs/models/gpt-5.6-terra>

## Results

| Attempt | Result | Input | Cached input | Output | Reasoning output | Approx. wall time | Cost status |
|---|---|---:|---:|---:|---:|---:|---|
| Invalid schema / Low | Rejected HTTP 400: `uniqueItems` unsupported | Not reported | Not reported | Not reported | Not reported | 0.1 s after turn start | Not measured |
| Valid schema / Low | Accepted; correct JSON | 18,169 | 0 | 48 | 0 | 4.0 s | Estimated $0.036914 |
| Valid schema / Medium | Accepted; correct JSON | 18,169 | 0 | 48 | 0 | 4.1 s | Estimated $0.036914 |
| Muse Contributor / Low | Accepted; locally schema-valid, correct JSON | Not exposed | Not exposed | Not exposed | Not exposed | 11.93 s full call | Not measured |
| Muse Contributor / Medium | Accepted; locally schema-valid, correct JSON | Not exposed | Not exposed | Not exposed | Not exposed | 14.33 s full call | Not measured |

The estimate is `(18,169 × $2 + 48 × $12) / 1,000,000`. Codex did not expose an
actual billed-cost field, so these values must not be described as billed cost.

Low receipt thread ID: `01a096b7-0263-7b51-a357-5242224741bb`  
Medium receipt thread ID: `01a096b7-1264-7bb2-a1d6-49dde3660bd5`

Low output:

```json
{"primary_repo":"example/widgets","phase":"verification","confidence":0.98,"evidence_ids":["synthetic-1","synthetic-2"],"abstain":false}
```

Medium output:

```json
{"primary_repo":"example/widgets","phase":"verification","confidence":0.99,"evidence_ids":["synthetic-1","synthetic-2"],"abstain":false}
```

Muse Low output was schema-valid and correct; confidence varied from 0.90 to 1.00
across two identical attempts. Muse Medium was also schema-valid and correct;
confidence varied from 0.90 to 0.95 across two attempts. This variation is recorded,
not scored, because confidence calibration was not part of this capability case.

Timed Muse Low receipt: session `01a09858-fa65-7da3-88ae-93556cac73a1`, request
`15f3d44f-2732-4c70-9457-7913b02669f8`, response
`resp_6aa5fa1dca1dd98602784cc7`.

Timed Muse Medium receipt: session `01a09859-6c93-74e2-adc7-a96fbac4e6e0`, request
`123b6142-d46f-4156-891a-ecc4364541d2`, response
`resp_6aa5fa39095070e744974cef`.

## Ad-hoc non-Contributor Muse synthetic battery

The operator next requested `muse-spark-1.3` (the non-Contributor tier) against a
full battery and Terra Low/Medium. No prior full #210 battery existed: the planned
12–20 historical-window campaign was still unfrozen and private-data egress remained
unapproved. This pivot therefore froze a separate 12-case **synthetic preliminary
battery** before inference. It is not the planned historical battery or a product
grade.

Artifacts:

- [`synthetic-battery.json`](synthetic-battery.json) — frozen cases and expected labels
- [`run_synthetic_battery.py`](run_synthetic_battery.py) — isolated, randomized runner
- [`synthetic-results.jsonl`](synthetic-results.jsonl) — 48 per-attempt receipts
- [`score_synthetic_battery.py`](score_synthetic_battery.py) — deterministic scorer
- [`synthetic-summary.json`](synthetic-summary.json) — aggregate metrics and mismatches
- [`muse-cost-samples.json`](muse-cost-samples.json) — post-battery native usage samples

The matrix used 12 cases for each of Terra Low, Terra Medium, Muse Low, and Muse
Medium. Order was randomized with seed 210. Each call used an empty temporary
workspace, no tools, and a 60-second timeout. Terra used provider-enforced Structured
Output. Muse Code 1.1.1 has no equivalent CLI option; its JSON was validated locally
against the same schema. All 48 recorded attempts completed without retry or process
failure.

| Arm | Strict exact | Abstention-aware exact* | Repo | Non-abstain phase | Abstain | Evidence IDs | Schema | p50 / p95 / max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Terra Low | 9/12 | 11/12 | 12/12 | 8/9 | 12/12 | 12/12 | 12/12 | 4.47 / 6.59 / 7.02 s |
| Terra Medium | 9/12 | 11/12 | 12/12 | 8/9 | 12/12 | 12/12 | 12/12 | 4.41 / 5.15 / 5.28 s |
| Muse non-Contributor Low | 10/12 | 11/12 | 12/12 | 8/9 | 12/12 | 12/12 | 12/12 | 13.54 / 24.58 / 24.91 s |
| Muse non-Contributor Medium | 10/12 | 11/12 | 12/12 | 8/9 | 12/12 | 12/12 | 12/12 | 19.27 / 27.66 / 29.52 s |

\* The abstention-aware score was added after viewing results and is therefore
supplementary, not a replacement for the frozen strict score. The schema requires a
phase even when `abstain=true`; this supplementary score ignores that placeholder
phase. It makes explicit that Muse's one-point strict advantage comes only from filler
phase choices on abstained cases. On substantive fields, all four arms tie at 11/12.

Every arm made the same substantive miss on S07, where a new function caused tests to
fail. The frozen expectation was `blocked`; Terra returned `implementation`, while
Muse returned `verification`. This may be a taxonomy ambiguity rather than evidence of
a model-quality difference and should be resolved before a historical campaign.
Neither Medium arm improved classification accuracy over its Low counterpart.

### Token and cost comparison

Official OpenAI documentation checked 2026-09-12 lists Terra at $2.00/M uncached
input, $0.20/M cached input, and $12.00/M output. The recorded battery replay yielded:

| Terra arm | Input total | Cached input | Output | Reported reasoning output | Estimated recorded cost |
|---|---:|---:|---:|---:|---:|
| Low | 227,171 | 163,840 | 655 | 107 | $0.167290–$0.168574 |
| Medium | 226,218 | 178,176 | 678 | 128 | $0.139855–$0.141391 |
| Combined | 453,389 | 342,016 | 1,333 | 235 | $0.307145–$0.309965 |

The lower estimate treats reported reasoning tokens as a subset of output tokens; the
upper estimate conservatively charges them again. These are dated list-price
estimates, not a provider bill. The first attempted matrix issued the same 24 Terra
calls but lost its in-memory receipts when the final writer encountered byte-valued
timeout output. Therefore total Terra spend for this request is not exactly measured;
it is likely roughly twice the recorded replay, about $0.61–$0.62. The runner now
normalizes timeout bytes and checkpoints each row immediately; a direct red/green
probe witnessed the original serialization failure and the correction.

The local model catalog records non-Contributor Muse at $1.25/M input, $0.15/M cached
input, and $4.25/M output. The battery's no-session-log JSONL receipts exposed request
and response IDs but not token counts or billed cost. After the battery, two identical
S03 probes with local session tracing enabled exposed the native provider usage:

| Muse sample | Input | Cached | Output | Reasoning | Estimated sample cost | Projected 12-call arm |
|---|---:|---:|---:|---:|---:|---:|
| Low | 29,824 | 0 | 356 | 276 | $0.038793–$0.039966 | $0.465516–$0.479592 |
| Medium | 29,827 | 0 | 546 | 470 | $0.039604–$0.041602 | $0.475248–$0.499224 |
| Projected combined battery | — | — | — | — | — | $0.940764–$0.978816 |

The same lower/upper reasoning-token convention is used. These are projections from
one representative case per effort, not actual battery usage or a provider bill; the
other cases may tokenize differently. They are more defensible than applying Muse's
prices to Terra's envelope because the samples capture Muse's roughly 29.8K-token
native request and its lack of cache reuse. The first failed-receipt matrix also issued
24 Muse calls, and the two tracing probes added one call per effort. Including those,
total Muse spend for this request is estimated around $1.96–$2.04. Actual billed cost
remains unavailable.

For the single recorded battery replay, projected Muse cost is about 3.0–3.2 times
Terra's estimated cost while Muse is also materially slower and shows no
abstention-aware accuracy gain. That gives Terra the operational advantage in this
synthetic probe, but it is not a promotion decision: the cases are synthetic, the
sample is small, Muse cost is projected, and the historical-window evaluation remains
unrun.

## Initial findings and next gate

1. Model entitlement and noninteractive authentication work on this device for both
   requested reasoning settings.
2. Structured output fails closed on an unsupported schema keyword and succeeds after
   narrowing to the provider-supported subset.
3. The Codex agent envelope dominates this deliberately tiny request: 18,169 input
   tokens per attempt. Before freezing a campaign, compare this path with the lean
   Responses API boundary or another existing constrained runner; do not assume the
   CLI is economical enough for a 15-minute cycle.
4. Terra and Muse, at Low and Medium, are indistinguishable on correctness for this
   trivial case. No model or setting decision is justified until the blinded, frozen,
   paired evaluation is defined and reviewed.
5. Muse's full native-CLI calls were roughly three times slower in this tiny probe, but
   the invocation envelopes differ, so this is not a model-only latency comparison.
   Muse emitted no token-usage receipt; its cost must remain `not measured` rather than
   being estimated from unknown token counts.
6. Muse's lack of a forced-schema CLI option and its Contributor data-use clause are
   material product constraints. A future frozen Muse arm needs local validation,
   fail-closed handling, synthetic/redacted inputs, and an explicit privacy gate.
7. Remaining P0 work includes cancellation/timeout receipts, privacy/redaction rules,
   request-receipt sanitization, frozen windows, controls, budgets, and witnessed
   malformed-output/empty-input/auth/quota failure paths.

## Opt-in real-work canary pivot

Later on 2026-09-12, the operator explicitly approved beginning a bounded Terra
`/daily` canary while the historical evaluation continues. This authorizes the
minimized Daily evidence packet to leave the Mac Studio for `gpt-5.6-terra`; it does
not promote the synthetic battery into a product grade or waive the pending blinded
comparison.

The new runner is default-off and scheduled separately from the incumbent 18:20
publisher. It reads existing CLIO, ranked-action, calendar, Sleuth, Apple Reminder,
repository-loop and CPU-health seams; redacts obvious secret assignments and email
addresses; caps packet size; invokes Terra Low ephemerally in an empty directory with
read-only sandboxing, no rules, no tools and provider-enforced structured output; then
validates citations before a deterministic append. Daily call, input/output-token,
estimated-cost and consecutive-failure ceilings fail closed. A local kill switch can
disable it without changing source or the existing publisher.

The first real accepted cycle used 18 evidence records and a 4,835-character packet.
Its Codex receipt reported 21,020 input tokens, 0 cached input tokens, 361 output
tokens and 109 reasoning-output tokens in one accepted call. The conservative dated
list-price estimate was $0.0477; this is not billed cost. The output correctly
abstained because the persisted CLIO table was stale and the packet carried no recent
intent record. That observation produced a pre-deploy correction: the packet now
reads the bounded live CLIO JSONL tail first and uses the persisted table only as a
fallback. A post-correction dry run contained 30 evidence records in 10,418
characters. Real usefulness, sleep/wake behavior, and Low-versus-Medium quality remain
unmeasured until the canary accumulates operator ratings and the frozen campaign runs.

The first post-correction output still abstained because the prompt over-weighted the
absence of completion evidence. The policy was narrowed again: fresh intent may support
an explicitly labelled *apparent* focus, but it may never support an execution or
completion claim. The next accepted cycle then identified the active XYZ-forge
CI/runner-recovery thread from five recent CLIO records, retained the completion caveat,
and cited every source ID. Its receipt reported 23,232 input tokens, 565 output tokens,
44 reasoning-output tokens, 13.68 seconds, and a conservative $0.0538 list-price
estimate. At that observed rate, a full 72-cycle active day projects to about $3.87
($116 per 30-day month); those figures are extrapolated estimates, not billed cost or a
quality verdict. The configured $4 daily ceiling and 72-call ceiling bound the canary.
