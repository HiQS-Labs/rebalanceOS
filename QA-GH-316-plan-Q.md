# Plan review request — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter

You are reviewing a PLAN (pre-implementation) for a small, operator-directed naming change in the rebalanceOS repo. Grade against the stated requirements and commensurate complexity — this is a labels-and-aliases change, not a schema migration; do not demand enterprise machinery.

## Task (issue #316, abridged)

Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project GitHub work-activity signal:

1. REQUIRED backwards-compatibility adapter: MCP tool `github_balance` stays registered + functional (docstring marks it deprecated alias); new canonical MCP tool `hiqs_work_activity`; Python `get_hiqs_work_activity()` canonical with `get_github_balance` kept as alias.
2. Contract freeze: SQLite table `github_activity`, SQL reader `fetch_github_balance`, and ALL output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by external experiments (issue #300, Needle-fork#79).
3. Operator-facing strings presenting the SIGNAL relabel to "HiQS work activity"; strings describing ingestion of the raw GitHub data source stay literal.

## Plan doc (review this)

- `PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md` — includes Phase 0 prior-art with file:line cites, requirements, ordered smallest surface, non-goals, risks, test/gate.

## Source paths to verify claims against

- `src/rebalance/mcp/tools/projects.py` (FastMCP tool `github_balance`; `projects.register`)
- `src/rebalance/ingest/github_scan.py` (`get_github_balance`, ~line 741)
- `src/rebalance/ingest/querier.py` (line ~287 "## GitHub Activity (last 7 days)")
- `src/rebalance/cli/query.py` (~line 118), `src/rebalance/cli/github.py` (~64,72), `src/rebalance/cli/onboard.py` (~124)
- `src/rebalance/ingest/db/queries.py` (`fetch_github_balance`, `CLOUD_AGENT_AUTHORS`), `src/rebalance/ingest/db/schema.py` (`github_activity` table)
- `tests/test_mcp_probe.py`, `tests/test_queries_mirror_invariance.py` (guard baselines)
- `README.md`, `AGENTS.md`

## Questions

1. Are the plan's file:line claims grounded in the actual code? Any surface the plan MISSES where the signal is operator-facing (CLI output, pulse/dashboard renderers, MCP descriptions, docs)?
2. Is the adapter design right — is aliasing at the MCP-tool + Python-function boundary sufficient, and is freezing the table/SQL/JSON contract the correct line? Any consumer you can find that would break?
3. Does any relabel risk corrupting the ingestion-vs-signal distinction (the label rule)? Name specific strings if so.
4. Are there existing tests/ratchets (`mirror_invariance`, read-layer, script-inventory) that the change would trip? 
5. Version: plan proposes 0.98.0 → 0.98.1 PATCH (aliases + labels, no behavior change). Agree?
6. Are the ratings (55/15/50/55) grounded for a naming-consistency ask?

Output: verdict APPROVE / CHANGES with numbered findings, each citing file:line evidence.
