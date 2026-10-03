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
| Phases 1–4 implemented, plus the #297 items the operator pulled in (GitHub embedding guarded; returned collector errors classified). Full suite 2870 passed (6 battery-only failures, pre-existing). On the 14" the fixed guard ran 3/3 jobs the old guard refused. QA: agy plan relay approved; Codex implementation relay closed Escalated on one accepted, documented limitation (the worker-thread guard can't interrupt mid-run). Evidence: [TESTS-RESULTS/2026-09-27+GH-296](../../TESTS-RESULTS/2026-09-27+GH-296/SUMMARY.md). | PR open, awaiting review and merge. After merge: 5.2 full re-embed, 5.3 48 h soak, 5.4 7-day check; dashboard subprocess follow-up in #297. |

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


## PR 298 takeover review — 2026-10-02

- [x] Phase 0: inspect existing GitHub review threads and retained plan/implementation relay;
  use the PR revision as source evidence because the available graph generation predates it.
- [x] Reproduce settings visibility defects: disabled checks omit thresholds, null thresholds
  misattribute defaults, malformed root configuration is silent, and sub-byte overrides truncate to zero.
- [x] Extend the existing resolver/report only; retain lock, timeout, and accepted worker-thread behavior.
- [ ] Verify regression tests fail before fixes, run relevant suites and repository gates, retain receipts
  in the existing campaign, and publish the review to the PR.

Decision rule: each regression must fail on the incoming PR and pass after the narrow correction.
No new hardware-performance claim is made; the existing post-merge soak remains outstanding.

The refresh review also reproduced strict scheduler success for returned collector errors.
Strict policy now belongs to `classify_sync_outcome`, using its existing failure classification;
the wrapper delegates to it. Embedding deferrals and optional next-actions notes remain nonfatal.

Recon: scheduler wrapper → shared classifier; embedding decorator → embedding guard → shared
memory resolver and lock. The changes add no state writer or subsystem. Failure handling stays
at the configuration origin and classification boundary. The approved plan explicitly requires
the standalone stdlib config reader, so importing the application resolver here is not suitable.
The graph generation (2026-09-02) predates the PR; changed source and excluded shell code were
read directly. Read-only recon lanes reviewed guard enforcement and refresh/doctor integration.

External feedback disposition: the main-thread label and stale ceiling documentation were already
fixed; the reserved exit-code concern was withdrawn by its reviewer and is not reopened. Greptile
provided no review because its trial expired. CodeRabbit's telemetry question exceeds the actual
issue requirement: the run record must contain guard mode, while doctor owns thresholds/sources.
The accepted worker-thread interruption limitation and post-merge hardware qualification remain.
