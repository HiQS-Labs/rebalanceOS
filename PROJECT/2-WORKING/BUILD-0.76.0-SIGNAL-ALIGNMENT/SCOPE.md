---
title: "Build 0.76.0 Signal Alignment and Staling Invariants Scope"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Align What's next signal staling, reminder disappearance reconciliation, and candidate ranking"
gh_issue: 113
source: https://github.com/HiQS-Suite/rebalanceOS/issues/113
effort: 2
complexity: 2
risk: 2
phases: 2
ratings_provisional: false
roadmap_exempt: false
---

# Build 0.76.0 — Signal Alignment & Staling Invariants (GH-113)

## Status

| What was just completed | What's next |
|---|---|
| Phase briefs and MARATHON.yaml authored for Issue #113 umbrella alignment. | Execute preflight, contract validation, and marathon dry-run. |

## Overview

Addresses the signal alignment and staling issues identified in #113:
- **Phase `sa1`**: Verify and test Sleuth reminder disappearance reconciliation and staling sweep (`is_active=0`, `state='stale'`) to ensure completed/expired reminders reliably drop from What's next even when export feeds experience clock skew or delays.
- **Phase `sa2`**: Verify What's next candidate ranking and author attribution fallback invariant (preserving raw UIDs as traceable receipts rather than degrading to anonymous items).

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/pytest tests/ -q",
  "fix_probes": [
    { "type": "grep_absent", "path": "tests/test_sleuth_reminders.py", "pattern": "test_staling_sweep_reconciles_missing_reminders" },
    { "type": "grep_absent", "path": "tests/test_next_actions.py", "pattern": "test_sleuth_candidates_unmapped_sender_id" }
  ],
  "artifacts": [
    "src/rebalance/ingest/sleuth_reminders.py",
    "src/rebalance/ingest/next_actions.py",
    "tests/test_sleuth_reminders.py",
    "tests/test_next_actions.py"
  ],
  "remediation": {
    "source": "issue#113",
    "criteria": "Sleuth reminders staling sweep is comprehensively regression-tested and verified against delayed export feeds; What's next candidate ranking and author fallback semantics are locked down with behavioral tests."
  },
  "lanes": {
    "agy_safe": [
      "src/rebalance/ingest/sleuth_reminders.py",
      "src/rebalance/ingest/next_actions.py",
      "tests/test_sleuth_reminders.py",
      "tests/test_next_actions.py"
    ],
    "orchestrator_only": []
  }
}
```

## Execution

```bash
.xyz/relay-automation/marathon.sh \
  --plan PROJECT/2-WORKING/BUILD-0.76.0-SIGNAL-ALIGNMENT/MARATHON.yaml \
  --pre-advance-cmd ".venv/bin/pytest tests/ -q" \
  --dry-run
```
