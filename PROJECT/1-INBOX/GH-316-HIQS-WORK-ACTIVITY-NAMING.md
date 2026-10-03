---
gh_issue: 316
source: https://github.com/HiQS-Labs/rebalanceOS/issues/316
title: "Rename the work-activity signal to \"HiQS work activity\" (labels + namespace) with a backwards-compatibility adapter"
status: Proposed (1-INBOX — not yet active)
created: 2026-10-03
updated: 2026-10-03
doc_type: feedback
effort: 2
complexity: 2
risk: 1
phases: 1
---

## Capture (from [#316](https://github.com/HiQS-Labs/rebalanceOS/issues/316))

The work-activity signal (the per-project GitHub activity rollup behind `github_balance()`,
the pulse dashboard, and project balance scoring) is named inconsistently: code says
`github_balance` / "GitHub activity"; marketing says **HiQS (High Quality Signals)**, and
newer work already adopts the term (#315, `hiqs-digest`).

**Ask:** make "HiQS work activity" the canonical label and namespace, with a **backwards-
compatibility adapter** — `github_balance` MCP tool stays functional as a deprecated alias;
`get_github_balance` stays as a Python alias; storage table (`github_activity`) and JSON
output keys are unchanged (consumed by #300 / Needle-fork#79).

**Acceptance:** both MCP tool names live with identical shapes; Python alias intact; zero
bare "GitHub activity" operator-facing strings for this signal; focused alias-parity test;
full suite + ratchets green.

Rating: **rated 55/15/50/55** — user-directed naming consistency (marketing alignment),
no defect consequence (sev 15); mechanical but broad surface (effort 55); appeal neutral.

Related: #315, #313, #124.
