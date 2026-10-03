---
gh_issue: 316
source: https://github.com/HiQS-Labs/rebalanceOS/issues/316
title: "Rename the work-activity signal to \"HiQS work activity\" (labels + namespace) with a backwards-compatibility adapter"
status: Implemented — plan pending Codex QA; PR open for review
created: 2026-10-03
updated: 2026-10-03
owner: Noel (start-task)
goal: Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project work-activity signal, with a backwards-compatibility adapter so no existing consumer breaks.
doc_type: project
branch: feat/hiqs-work-activity-naming
effort: 2
complexity: 2
risk: 1
phases: 1
---

# HiQS work activity — canonical naming with a compatibility adapter

## Status

| What was just completed | What's next |
|---|---|
| Recon of every surface complete; intake captured and promoted; plan drafted. | Codex plan QA, then implementation of the rename + adapter with a parity test, gate, final QA, PR. |

Rating: **rated 55/15/50/55**.
- **Priority 55:** user-directed; aligns code vocabulary with marketing (HiQS = High Quality Signals); newer work (#315) already adopts the term organically.
- **Severity 15:** naming-consistency debt, no defect or data consequence.
- **Appeal 50:** neutral; the operator didn't set a score.
- **Effort 55:** mechanical but broad — many small string surfaces plus two alias seams.

## Phase 0 — Prior art review

- `src/rebalance/mcp/tools/projects.py:26` — FastMCP tool `github_balance`, registered via `projects.register(mcp, db)` (`mcp/server.py:15`). **Extend:** add the canonical `hiqs_work_activity` tool beside it; keep the old name as a deprecated alias calling the same implementation.
- `src/rebalance/ingest/github_scan.py:741` — `get_github_balance()`, the public ingest-layer API. **Rename to `get_hiqs_work_activity()` and keep `get_github_balance` as a module-level alias** (zero callers break).
- `src/rebalance/ingest/db/queries.py` — `fetch_github_balance` + table `github_activity`. **Unchanged:** internal transport names, guarded by `test_queries_mirror_invariance.py:264` and the read-layer ratchet; renaming would be a schema/migration concern with zero operator value (AGENTS.md: function over transport — internals keep transport names).
- `src/rebalance/ingest/querier.py:287` — `"## GitHub Activity (last 7 days)"` header in the gathered context (surfaces in dashboard/pulse output). **Relabel.**
- `src/rebalance/cli/query.py:118` — `"\n--- GitHub Activity ---"`. **Relabel.**
- `src/rebalance/cli/github.py:64,72` — `github-scan` help strings. **Relabel** ("Scan HiQS work activity (GitHub) …").
- `src/rebalance/cli/onboard.py:124` — discovery string. **Relabel.**
- `README.md` / `AGENTS.md` — signal-presenting mentions (`github_balance` rows). **Relabel** where they name the signal; keep "GitHub activity" where it names the raw ingested data source (ingestion vs signal distinction, stated below).
- MCP test pattern: `tests/test_mcp_probe.py`. **Extend** with an alias-parity check (both tool names resolve; identical output for the same DB).
- Nearest prior work: #315 (already says "HiQS activity"), #313 (rename family), #124 (org-rename precedent).

## Requirements

1. **Canonical name:** `hiqs_work_activity` (MCP tool), `get_hiqs_work_activity()` (Python), label "HiQS work activity" (operator-facing strings).
2. **Backwards-compatibility adapter (required):** `github_balance` MCP tool remains registered and functional, its docstring marking it the deprecated alias of `hiqs_work_activity`; `get_github_balance` remains as an alias of the canonical function. Both tools return byte-identical shapes for the same inputs.
3. **Contract freeze:** table `github_activity`, SQL reader `fetch_github_balance`, and all output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by #300 / Needle-fork#79.
4. **Label rule:** strings that present the *signal* say "HiQS work activity"; strings that describe *ingesting the raw GitHub data source* stay literal ("GitHub activity"). This keeps the diff honest instead of blind-replacing.

## Smallest surface (ordered)

1. `ingest/github_scan.py` — rename `get_github_balance` → `get_hiqs_work_activity` (+ docstring), add `get_github_balance = get_hiqs_work_activity` alias line with a deprecation note.
2. `mcp/tools/projects.py` — add `hiqs_work_activity` tool (canonical docstring); reduce `github_balance` to a deprecated alias calling the same function.
3. `ingest/querier.py:287` + `cli/query.py:118` + `cli/github.py:64,72` + `cli/onboard.py:124` — relabel to "HiQS work activity".
4. `README.md`, `AGENTS.md` — relabel signal-presenting mentions of `github_balance` / "GitHub activity".
5. `tests/test_mcp_probe.py` (or a focused new test file following its pattern) — alias parity: both tool names registered; same DB → identical rows; `get_github_balance is get_hiqs_work_activity` alias assertion.
6. Version bump 0.98.0 → 0.98.1 + CHANGELOG entry.

## Non-goals

- No table rename, no schema migration, no JSON key changes, no `agent_tags` value changes, no SOP §8 contract changes, no close-loop (#308) renaming.

## Risks and rollback

- **Consumer drift:** external MCP clients referencing `github_balance` keep working (alias) — the only risk is them never migrating; acceptable, the alias docstring steers them.
- **Over-replacement:** blind string replacement could corrupt the ingestion-vs-signal distinction; mitigated by the label rule above and surgical per-file edits.
- **Rollback:** purely additive aliases + label strings; revert the PR.

## Tests and gate

- Focused: alias parity test + `tests/test_mcp_probe.py` + `tests/test_queries_mirror_invariance.py`.
- Gate once on the final commit: `pytest tests/`, `utils/pdda/pdda.sh run`, `check_script_inventory.py --check`, `check_read_layer.py`.

## Acceptance

- Both MCP tool names live with identical shapes; `get_github_balance` alias intact.
- No signal-presenting operator string says bare "GitHub activity"; storage and JSON keys unchanged.
- Full suite + ratchets green; issue #316 acceptance boxes checkable.
