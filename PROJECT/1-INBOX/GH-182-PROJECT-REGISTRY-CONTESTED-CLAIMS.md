---
title: "GH-182 project_registry contested claims — naming rule + unmarked writer"
status: "Queued (issue filed, decision deliberately deferred)"
created: 2026-09-04
issue: "https://github.com/HiQS-Labs/rebalanceOS/issues/182"
trigger: "PR #181 shipped project-level duplicate detection; the 7 survivors need a naming rule before any repair can be automated"
effort: 3
complexity: 3
risk: 2
ratings_note: >-
  Rated on the honest axes, then held down by an explicit roadmap override (`ovr 90`) so the item
  stays visible in the ledger without competing for the next build slot. The decision is worth
  making and is not urgent: detection already blocks regressions, so nothing degrades while it waits.
privacy: >-
  Concrete organisation, project and repository names are deliberately omitted — this repository is
  public. They live in the maintainer's local GH-182 sidecar doc (temp/GH-182-sidecar.md,
  gitignored), which uses the same R1..R7 labels used here.
---

# GH-182 — Seven repositories, two projects each

## Problem statement

`project_registry` has no uniqueness constraint on the repositories a project claims. Its primary key
is the **project name**, so two rows may each list the same repository in `repos_json` and the schema
raises nothing. Seven repositories are in that state today: each is claimed by two live,
`status=active` project rows, so every project-level read path counts one repository twice.

Three separate code paths write into `project_registry`, they derive project names differently, and
**one of them records no provenance at all**. That is what makes this more than a cleanup task: with
no `generated_by` on one side, nothing can tell a machine-written row from an operator-written one,
so the duplicates cannot be resolved programmatically without risking the deletion of a real,
hand-curated project.

## Verdict up front

- **Detection is done** (PR #181). `tests/test_alias_dedup_invariant.py` fails if two projects claim
  one canonical repository. Nothing new can regress in silence.
- **Repair cannot be automated yet**, and not because the rows are hard to find — because one writer
  leaves no provenance stamp, so no script can safely pick a side.
- **The seven are not one decision.** Five are pure naming duplicates; two are genuine multi-repo
  projects whose narrow twin must be *merged*, not deleted.

## Scope

| | |
|---|---|
| Repositories claimed twice | **7** (`R1`–`R7`) |
| Pure naming duplicates | 5 (`R2`–`R6`) |
| Multi-repo projects with a narrow twin | 2 (`R1`, `R7`) |
| Already removed before #181 | 4 org-rename artifacts, verified machine-owned before deletion |

## The working assumption that was wrong

The natural resolution — *"a curated row beats an inferred one"* — **cannot be used here, because
neither claimant is curated.** Both are machine-written, by different writers, and only one stamps
provenance:

| | claimant A | claimant B |
|---|---|---|
| writer | `project_inference.py` (`rebalance ingest infer-project-registry`) | `preflight.py: discover_candidates()` ([L246-L262](src/rebalance/ingest/preflight.py#L246-L262)) |
| name shape | human-readable label from activity clustering | `repo_full_name` verbatim, **including the owner segment** |
| provenance in DB | `custom_fields_json.inference.generated_by = "activity_inference_v1"` | **`{}` — `provenance="remote-activity"` is set on the model and lost on the write** |
| other fingerprints | `tags: ["inferred", "source:github", …]` | `tier=3`, band tags `["A"]`/`["A","B"]`, summary `Recent activity: … Active bands: …` |

The `owner/repo` spelling *looks* hand-entered precisely because it is verbatim. That is the trap
worth recording: the row that reads as authoritative is the one with no provenance behind it.

A third writer exists — the `commit_threshold_v1` auto-promoter in `index_ops.py` (see #1). Four rows
from that writer were pure org-rename artifacts and were removed ahead of PR #181, taking the
contested set from 11 to 7.

## Why the seven are not one decision

- `R2`–`R6` are one repository under two names. The owner-prefixed spelling carries no information
  the canonical repository key does not already hold, so one row can be retired.
- `R1` and `R7` are **not** renames of their twin. Each is a project whose real scope is broader than
  the single repository the twin claims — `R7` claims three repositories and only one is contested.
  Collapsing these the same way loses a project.

## What resolving it requires, in order

1. **Decide the naming rule** — human-readable name or `owner/repo` slug. Today both are produced and
   neither is authoritative. This is the operator's call and the only genuinely blocked step.
2. **Persist `provenance` on `discover_candidates()` rows** into `custom_fields_json`. Small, and it
   is the precondition for any safe automated repair.
3. **Merge, don't delete, the two multi-repo cases** (`R1`, `R7`). The narrow row's activity history
   has to land on the surviving project.
4. **Add the blocked control** — a guard in `project_inference.py` refusing to create a project for a
   repository an existing project already claims, compared canonically. Excluded from PR #181 on
   purpose; #181 shipped *detect* only.

Steps 2 and 4 do not depend on step 1 and can land independently.

## What this deliberately does NOT propose

**A new CLI writer for projects/repos.** `rebalance ingest infer-project-registry` already is the
disciplined path. A second writer is a parallel path to keep in sync — the drift class `ROUTER.md`
opens by warning about and SOP.md §6 exists to stop. The gap is a missing canonicalisation guard, not
a missing command.

## Related

- PR #181 — detection (project-level claim collision fails the suite)
- #150 — activity-signal read-layer consolidation, same alias-blind class one layer down
- #158 — monitored-repo rules
- #1 — sustained-activity auto-promotion (`commit_threshold_v1`)
- SOP.md §6 — counted-once policy
