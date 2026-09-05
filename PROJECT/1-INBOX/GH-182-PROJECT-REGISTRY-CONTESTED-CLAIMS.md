---
title: "GH-182 project_registry contested claims — naming rule + unmarked writer"
status: "Decided 2026-09-04 — rule settled, enforcement sequenced, not yet implemented"
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
| writer | `project_inference.py` (`rebalance ingest infer-project-registry`) | `preflight.py: discover_candidates()` ([L246-L262](../../src/rebalance/ingest/preflight.py#L246-L262)) |
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

## Decision (2026-09-04)

**The naming dilemma is false, and that is what settles it.**

`preflight.discover_candidates()` names a candidate after its repository because at discovery time
there *is* no project yet — the `owner/repo` string is a **placeholder standing in for a name nobody
has supplied**, not a competing naming convention. `confirm_and_write()` then appends it straight
into `active_projects` with no check, so the placeholder becomes permanent and, when a human-named
project later claims the same repository, contested.

**Human-readable names win, always** — not because curation outranks inference (neither row is
curated) but because the slug was never a name.

### The rule

> A project whose `name` is equal to one of the repositories in its own `repos` list is a discovery
> placeholder, not a project.

A pure function of the row: no per-case judgement, no provenance lookup, no operator input. That is
what makes it deterministic. It resolves all seven contested cases the same way, with no tie.

It also classifies the **seven further placeholders that have no human-named twin** — 14 slug-named
entries sit in `active_projects` today. Those seven are not duplicates and must not be deleted; they
are the only record of their repository. They get *renamed* when a real name exists and keep working
until then. That asymmetry is the intuitive half of the rule.

### Where the source of truth actually is

```
Projects/00-project-registry.md   (hand-editable YAML in the vault — SOURCE OF TRUTH)
        -> Registry model -> _registry_to_projection() -> projects.yaml -> sync_db()
        -> project_registry table                        (a PROJECTION, not the store)
```

All seven contested rows live in the registry markdown under `active_projects`, each with
`custom_fields: {}`. **Repair is an edit to one file followed by `rebalance ingest sync --mode pull`**
— not SQL surgery on the live database, and so free of the delete-before-rename hazard SOP.md §6
clause 4 exists to prevent.

### Enforcement — three points, each where it belongs, no new subsystem

1. **`confirm_and_write()`** — refuse to append an entry claiming a repository an existing entry
   already claims, compared through `canonical_github_repo_name()`. This is the write that created
   all seven; roughly ten lines, and it is the *blocked* control.
2. **The projection boundary** (`_registry_to_projection` / `sync_db`) — refuse to project two
   entries claiming one canonical repository. The registry is hand-edited YAML, so this is the only
   layer that can catch a human edit; it must fail loudly at sync rather than write through.
3. **`doctor`** — the existing `projects` check reports anything that slips past both. Detection in
   the test suite landed in PR #181.

### Why not a `project_repos` table with a `UNIQUE` index

The textbook answer, and the wrong trade here. The source of truth is hand-edited YAML in the vault,
not SQLite. A database constraint cannot prevent a bad edit to that file — only fail *after* it, at
exactly the boundary where control 2 already sits. The join table buys a migration and a second
representation of the same fact, for enforcement still needed at the YAML boundary regardless.
Control 2 gives the same determinism for less code (GUIDING-PRINCIPLES #6), and SOP.md §6 clause 1 is
explicit that identity should not rest on a constraint over a mutable key.

### Correction to this doc's earlier framing

Earlier revisions said `provenance` is "set on the model and lost on the write". Imprecise: the
round-trip works in **both** directions and has since the initial public release
(`registry.py:141` writes it into `custom_fields`; `registry.py:218` reads it back). The registry
markdown contains **zero** provenance fields — it is dropped at *accept* time in
`confirm_and_write()`, not at projection time. Same missing stamp, smaller and better-located fix,
and it belongs in the same ten lines as control 1.

## What resolving it requires, in order

| # | Change | Depends on |
|---|---|---|
| 1 | `confirm_and_write()`: claim guard + carry `provenance` onto accepted entries | — |
| 2 | Projection boundary: refuse two entries claiming one canonical repository | — |
| 3 | Repair the 7 contested entries in the registry markdown, then `sync --mode pull` | 1, 2 |
| 4 | Rename the 7 orphan placeholders as real names become available | 3 |

1 and 2 are independent of each other and of the repair. Before deleting a contested slug entry,
decide whether its `priority_tier` carries onto the survivor — the twins hold `null` today and the
tier feeds `next_actions.py` low-cadence gating. Concrete identifiers are in the maintainer's local
GH-182 sidecar doc.

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
