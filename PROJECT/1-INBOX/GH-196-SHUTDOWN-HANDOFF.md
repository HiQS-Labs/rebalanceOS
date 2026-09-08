---
gh_issue: 196
source: https://github.com/HiQS-Labs/rebalanceOS/issues/196
title: Shutdown — end-of-day triage and next-session continuity
status: Proposed (1-INBOX — plan QA, implementation not started)
created: 2026-09-07
updated: 2026-09-07
owner: Maintainer
doc_type: feedback
effort: 3
complexity: 3
risk: 3
phases: 4
---

The operator requested an execution plan in the GitHub issue and Agy plan QA only.
The issue body is the current planning artifact; review evidence will be attached
there. At implementation start, promote this capture to 2-WORKING and import the
approved issue revision as the active execution plan. Do not maintain two editable
execution plans. No shutdown code, deployment, merge, or cleanup is authorized by
this planning task.

## Requirements

- Extend daily in RebalanceOS; retain merge-cleanup as the approved action executor.
- Detect activity within existing repositories, not repository creation dates.
- Report and triage first; offer optional execution only after scoped approval.
- Two snapshots exclude repositories with ongoing activity.
- Produce a compact handoff relating PRs to project phases, deliberate deferrals,
  remaining tests/reviews, and one concrete next-session nudge per project.
- Work without the Rebalance runtime; configured runtime data enriches optionally.
- Keep private handoffs and machine configuration gitignored; invoke conversationally
  from any agent host, including a session opened in XYZ Forge.
- MVP: no new scheduler, database, dashboard, ingestion pipeline, or cleanup engine.

## Prior art and boundaries

See [recon map](../4-MISC/recon-gh196-shutdown.md). Coordinate with #150 (shared
activity reads), #192 (timezone boundaries), and PR #195 (daily skill edits), but
do not wait for or absorb their wider scopes. Do not reactivate 3-Eyes.

## Provisional task assessment

2026-09-07: rated 70/55/50/55 (priority/severity/appeal/cheapness). The operator
reports recurrent hour-scale restart cost; loss of context can also lead to unsafe
cleanup, but no new data-loss incident is established here. Appeal remains neutral.
This is a moderate feature, not a one-line skill edit. Existing #179/#187 and
#150/#192 establish adjacent prior work, not distinct incidents of this defect.
No numerical recurrence trend is claimed. Rebalance's current roadmap CLI supports
sync/list only; ROADMAP.md is its canonical writer, not XYZ's newer rate/add CLI.
