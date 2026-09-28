---
gh_issue: 296
source: https://github.com/HiQS-Labs/rebalanceOS/issues/296
title: "job_guard memory guard: per-device on/off (and thresholds) via per-device config, plus a guard-off tech spike"
status: "Active — fix in flight on fix/gh296-job-guard-swap-scaling"
created: 2026-09-27
updated: 2026-09-27
owner: noel
doc_type: bugfix
goal: >
  Stop the job guard refusing healthy runs on small-swap Macs by scaling the swap corroboration to
  the swap file, make an inner (embedding) memory refusal deferred instead of fatal, and give each
  Mac a memory-check on/off switch that keeps the single-instance lock and timeout.
effort: 3
complexity: 3
risk: 2
phases: 4
ratings_provisional: false
roadmap_exempt: false
---

# GH-296 — job_guard swap corroboration scaled to the swap file, both guard layers

## Status

| What was just completed | What's next |
|---|---|
| Spike on the MacBook Pro 14" (24 GB, 2 GB swap): the old guard refused all 5 small jobs at ~50% free; the proposed rule ran all 5. Remediation plan written as the issue body and approved by an agy relay (2 rounds). | Implement Phases 1–4 on this branch, full suite, final relay QA, PR. |

## Canonical plan

The plan lives in the [issue body](https://github.com/HiQS-Labs/rebalanceOS/issues/296) (approved by agy, relay
`relay-system/2026-09-27/gh296-plan-qa.md`). It is deliberately not copied here. Evidence is in the
issue comments (spike, memory-use evidence, three-way test, QA outcome).

## Rating

rated 85/70/50/55 (2026-09-27).
- **sev 70:** work-blocking for every guarded scheduled job on small-swap Macs (pulse-sync, pulse-web-sync, pulse-warning-watch, github-sync, embeddings), with no data loss. The embeddings path misreports as `fatal` (exit 1), which doctor flags.
- **pri 85:** severity-led. The operator asked to close it the same day.
- **Recurrence:** the same class hit the Mac Studio in GH-157 (179 refusals in 9 days, fixed by adding the corroboration rule this issue corrects). It recurred on the 14" on 2026-09-27: 4 refusals and 1 mid-run kill in the morning, and 5/5 refusals in each of two manual runs.
- **appeal 50:** neutral.
- **effort 55:** moderate; four phases in one module plus its bridge.
