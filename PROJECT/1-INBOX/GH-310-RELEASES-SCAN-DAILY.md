---
gh_issue: 310
source: https://github.com/HiQS-Labs/rebalanceOS/issues/310
title: Opt-in RELEASES ledger scan and /daily close-loop inputs
status: Proposed (1-INBOX — not yet active)
created: 2026-10-02
doc_type: feedback
effort: 3
complexity: 3
risk: 2
phases: 1
---

# Opt-in RELEASES ledger scan and /daily close-loop inputs

Captured from #310. Two add-ons are in scope for this run:
- **(b)** A read-only `--releases-scan <dirs>` on `rebalance github-close-loop`. It reports per-repo ledger tasks, conflicts between clones, and drift against the GitHub corpus.
- **(c)** `/daily` optionally reads that output and the close-loop JSON. The output is deduped and source-tagged, items are re-verified against live GitHub, and when the inputs are off the output is unchanged.

Focus 5 (a) Phase 1 is assessed during recon. Phase 2 is out of scope.
