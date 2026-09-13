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
