---
title: "Build 0.73.0 Subsystem Unification Marathon Scope"
status: "Completed — all six phases shipped as PR #40 (0.73.0) on 2026-08-17"
created: 2026-08-16
updated: 2026-08-17
owner: noel
goal: "Autonomous marathon execution plan for Release 0.73.0 Subsystem Unification"
effort: 3
complexity: 3
risk: 2
phases: 6
ratings_provisional: false
roadmap_exempt: false
---

# Build 0.73.0 — Subsystem Unification Scope

## Status

| What was just completed | What's next |
|---|---|
| All six phases (su1–su6) executed and merged as PR #40, released as 0.73.0 on 2026-08-17. | Nothing — this scope is closed. The one carry-forward is a process note: the marathon's pre-advance gate ran the test suite but not the lint gate, so two lint regressions reached the PR and were fixed at merge time. |

## Overview

Build 0.73.0 unifies foundational primitives across the repository and eliminates shared-process test leakage:
- Phase `su1` (#7): Isolate and fix test state leakage between `tests/` and `HiQS/tests`.
- Phase `su2` (#25): Consolidate timestamp handling through `src/rebalance/lib/time_ops.py`.
- Phase `su3` (#26): Route all GitHub API operations through `src/rebalance/ingest/_http.py::GitHubClient`.
- Phase `su4` (#27): Deduplicate database persistence loops and extract shared `table_exists` / `db_connection_readonly`.
- Phase `su5` (#28): Converge private git subprocess wrappers onto `src/rebalance/lib/git_ops.py`.
- Phase `su6` (#30): Remove dead functions (`_render_sleuth_groups`, CSS composite) and correct stale MCP docs.

## Execution

```bash
.xyz/relay-automation/marathon.sh \
  --plan PROJECT/2-WORKING/BUILD-0.73.0-SUBSYSTEM-UNIFICATION/MARATHON.yaml \
  --pre-advance-cmd "pytest tests/ HiQS/tests/ -q" \
  --dry-run
```
