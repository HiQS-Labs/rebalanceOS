# GH-210 Phase 0 capability receipt

Date: 2026-09-12  
Device: Noel's Mac Studio, 64 GB  
Branch: `feat/gh210-terra-work-synthesis`  
Baseline: `8a5df5ca26b51a7dcb0acc455af0d7bba8c18794` (`rebalance 0.87.2`)  
Codex CLI: `0.153.4`

## Scope and caveat

This is a synthetic capability probe, not the frozen evaluation campaign and not a
quality grade. No Rebalance, CLIO, repository, calendar, reminder, email, or other
private work evidence was sent. Private-data egress remains unapproved and disabled.

The commands used an empty temporary directory, read-only sandbox,
`--ignore-user-config`, `--ignore-rules`, `--ephemeral`, and a prompt that prohibited
tool use. The JSONL receipts contained only an agent-message event and no tool event.

## Contract checked

- Exact requested model: `gpt-5.6-terra`
- Reasoning settings: `low` and `medium`
- Noninteractive invocation: `codex exec`
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

## Initial findings and next gate

1. Model entitlement and noninteractive authentication work on this device for both
   requested reasoning settings.
2. Structured output fails closed on an unsupported schema keyword and succeeds after
   narrowing to the provider-supported subset.
3. The Codex agent envelope dominates this deliberately tiny request: 18,169 input
   tokens per attempt. Before freezing a campaign, compare this path with the lean
   Responses API boundary or another existing constrained runner; do not assume the
   CLI is economical enough for a 15-minute cycle.
4. Low and Medium are indistinguishable on this trivial case. No setting decision is
   justified until the blinded, frozen, paired evaluation is defined and reviewed.
5. Remaining P0 work includes cancellation/timeout receipts, privacy/redaction rules,
   request-receipt sanitization, frozen windows, controls, budgets, and witnessed
   malformed-output/empty-input/auth/quota failure paths.
