# GH-232 Luna High bounded narrative trial

## Result

The authorized three-case trial ran as a **newly composed dataset**, with the recovered September 16 CLIO capture and one September 30 read-only GitHub observation. It did not compare against the missing earlier enriched run. The private dataset, six unedited candidate samples, both deterministic controls per case, full audit and blinded review views are in the [private Git Pulse Sync trial folder](https://github.com/Hypercart-Dev-Tools/rebalance-git-pulse/tree/d475db03/experiments/gh232-luna-2026-09-30). The dataset was committed before inference at `f8d8b6e8`; outputs and receipts landed at `d475db03`. Operator usefulness is pending.

| Case | Frozen packet | Critical evidence in both repeats | Factual audit |
|---|---|---|---|
| XYZ Forge #508 → PR #535 | 7 selected prompts, 1 captured attempt, 3 GitHub facts | Superseded verdict and relocation intent retained | Both substantively supported |
| #568 → PR #581 | 6 prompts, 2 attempts, 2 unassigned mentions, 3 facts | Unassigned mentions and separate attempts retained | Both substantively supported |
| #623 → PR #640 | 8 prompts, 2 attempts, 3 facts | Z Code and agy kept separate | Repeat 1 supported; repeat 2 says “restarted” four times where the source says **re-prompted** four times |

The candidate cited the packet's unlabeled `gaps` array in every case. Those uncertainty statements are present in the supplied packet, but the array lacks a source ID, so the citations do not satisfy the fixed prompt contract. This is a dataset/instrument limitation; no output was repaired. The #623 overstatement is one unsupported factual claim. The preregistered rule therefore **does not advance this candidate** to a held-out trial, regardless of prose preference. This is not a general verdict on Luna or an inference of operator feedback.

## Execution

- Protocol frozen before inference in [PROTOCOL.md](PROTOCOL.md). CLIO capture SHA-256: `27a4dad7eb843a13e4e2727180a6cd3e5d07464192e5fa14d2f27057d5d02eaf`; its 288 eligible prompts/nine journeys/212 unassigned are coverage counts, not accuracy. New packets are SHA-256 `e365e29e1f63af6cb8ac6bb5df539a19f15ae01dc1e2c174f43a57ce24cad8ae` (#508), `21793675c1f331e5741ffec6ae27963d33ae296c3f43d6ce9567da501a05f211` (#568), `da3c095afb71e93c0214b9208b8bc907c6e6c460a3f3907616e7651b8df91e70` (#623).
- One synthetic probe tested same-number/different-repository ambiguity, merged-without-deployment and an injected completion instruction. It preserved the boundaries. A changed citation and removed required relationship were rejected by the deterministic packet validator. No tools were used.
- Exact requested runner: Codex CLI `0.155.0-alpha.16`, `gpt-6-luna`, effort `high`, fresh isolated read-only process per attempt. Six real samples completed, no transport retry or tool event. The CLI's catalog lists Luna High, and all invocations succeeded; its JSON events do **not** return model identity, so a server-returned identity is unverified.
- Six real calls: 112.84 seconds aggregate call wall time; reported input 27,111–27,524 tokens/call, output 488–651 tokens/call. Standard API-equivalent estimate $0.012105 for real calls and $0.013814 including the probe, using [official GPT 6 Luna rates](https://developers.openai.com/api/docs/models/gpt-6-luna). These are not billed charges. No attempt exceeded the issue's reported token, time, attempt or estimated-cost envelopes.
- Deployment, prompt-to-PR causation and activity outside the captured prompts remain unknown. Current GitHub relationship observations do not establish when those relationships first became visible. No source status, Daily job, vault or model default was changed.

## Decision and review

The private `review-508.md`, `review-568.md` and `review-623.md` present anonymized A/B/C views; the candidate's **both** repeats are shown. The operator can still judge which view helps explain and resume each case and flag misleading language. That feedback does not override the factual gate. A corrected citation-bearing packet or prompt would require a separately registered experiment; this run remains frozen. No production adoption is recommended from these three cases.

Current verification commands/results are recorded in [QA.md](QA.md). Detailed trial decisions and subsequent scope remain in [issue #232](https://github.com/HiQS-Labs/rebalanceOS/issues/232).
