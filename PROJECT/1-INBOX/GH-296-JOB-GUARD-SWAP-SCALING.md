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
| Phases 1–4 implemented on `fix/gh296-job-guard-swap-scaling`: swap bar scaled to the swap file, inner refusals deferred, per-device settings, doctor line. Full suite green (2829 passed). On the 14" the fixed guard ran 3/3 jobs the old guard refused in the same minute. Evidence: [TESTS-RESULTS/2026-09-27+GH-296](../../TESTS-RESULTS/2026-09-27+GH-296/SUMMARY.md). | Final relay QA, PR. After merge: 5.2 full re-embed, 5.3 48 h soak, 5.4 7-day check. |

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
