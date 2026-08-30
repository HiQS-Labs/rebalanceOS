# ROUTER.md

> ## 🛑 Before you build anything: check whether it already exists.
>
> This repo's most expensive recurring defect is **re-inventing a subsystem that is already
> here** — not writing bad code. It has happened repeatedly, to humans and agents alike, and
> reading this sentence is not enough to prevent it. **Run these four checks; they take under a
> minute and each one has caught a real duplicate:**
>
> 1. `gh pr list -R HiQS-Suite/rebalanceOS` **and** `gh pr list -R Hypercart-Dev-Tools/rebalance-OS`
>    — work in flight is invisible to a code search. An entire `rebalance/lib/*_ops` consolidation
>    campaign was resumed from scratch in 2026-08 because its remaining phases were sitting in
>    unmerged PRs on the *other* repo.
> 2. **`ROADMAP.md` → "In progress"** — the ledger of campaigns already under way.
> 3. **`grep -rn "<the concept>" --include="*.py" .` across `src/`, `utils/`, `HiQS/`** — a helper
>    you are about to write may exist in a package you were not looking at. A clean-room import
>    gate (`HiQS/tests/test_clean_room.py`) was duplicated in 2026-08 by someone who never looked
>    in `HiQS/`.
> 4. **Run the full suite, including the parts CI skips** — `pytest tests/ utils/3-eyes/tests
>    HiQS/tests`. A test that exists but never runs will not tell you it already covers your idea.
>
> If a thing exists and is inadequate, PDDA Phase 0 requires you to state **why extending it does
> not work** before replacing it. "I did not know it was there" is the failure this block exists
> to stop, and it is not a reason.

This file is the first entry point for an AI agent working in this repo: it tells you what to read, what to run, and which files are canonical. **This repo is an MCP server** — reach for the MCP tools before scanning code or writing ad-hoc shell pipelines.

## Role split

- `ROUTER.md` = startup order and canonical entry points (this file)
- `AGENTS.md` = behavioral rules, the MCP tool surface, the onboarding flow, and decision quality
- `ARCHITECTURE.md` = system orientation (Signal Sources, Source→Table fanout, "Adding a New Source") — read at session start
- `GUIDING-PRINCIPLES.md` = the *why* behind architecture and design decisions; includes the AI doc-review heuristics appendix
- `README.md` = human-facing repo/product overview and install path
- `CLAUDE.md` = the Claude Code entry stub; it defers to `AGENTS.md` for all behavioral rules
- `ROADMAP.md` = pointer ledger of in-progress, completed, attempted, and deferred work
- `CHANGELOG.md` = the end-of-iteration running log
- `RELEASES.md` = forward-looking release-planning ledger (governed by `PROJECT/PDDA.md`)
- `PROJECT/**` docs = canonical execution detail for a specific effort
- `PROJECT/PDDA.md` = document contract and PDDA automation rules

## Startup sequence

1. Read `ROUTER.md` to understand the repo's operating order and canonical files. -> expect one clear next file, not a repo-wide scavenger hunt.
2. Read `AGENTS.md` before making recommendations or edits. -> expect the MCP tool surface, the onboarding flow, explicit assumptions, and verified-claims-only discipline.
3. Read `ARCHITECTURE.md` for orientation, then `src/rebalance/ingest/index_ops.py` — the `COLLECTORS` registry is the data-plane spine. -> expect to extend a source with one `register_collector(...)` call, not edits to the dispatch chain.
4. Read `ROADMAP.md` to find the active effort. -> expect links outward to the canonical `PROJECT/**` docs; `ROADMAP.md` is a pointer ledger, not a plan body.
5. Read the linked `PROJECT/**` document that owns the work you are touching. -> expect a near-top `## Status` table telling you what was just completed and what is next.
6. If the task touches project docs, read `PROJECT/PDDA.md` and follow the PDDA contract. -> expect `PROJECT/2-WORKING` docs to have frontmatter, the exact status table, and QA gates when phased.
7. Before reporting success on code or runtime work, run `rebalance doctor` and `pytest tests/`. -> expect doctor clean and the suite green; do not claim completion if either fails or was skipped.
8. Before reporting success on doc-hygiene or roadmap work, run `utils/pdda/pdda.sh run` (or the relevant `utils/pdda/pdda.sh <check>` command). -> expect deterministic findings first, then any LLM review.

## Canonical rules

- This repo **is** an MCP server. Use the MCP tools (`index_status`, `refresh_index`, `semantic_query`, …) for data refresh and retrieval, and `rebalance doctor` for setup/health. Do not write ad-hoc `rebalance ...` shell pipelines or grep for setup scripts.
- Do not put phase checklists, build steps, or deep execution notes in `ROADMAP.md`.
- Every active doc in `PROJECT/2-WORKING/` must be reflected by a one-line pointer in `ROADMAP.md` — or opt out with `roadmap_exempt: true` in its frontmatter. Enforced by `utils/pdda/pdda.sh roadmap-coverage`; governance lives in `PROJECT/PDDA.md`.
- Every captured GitHub issue doc in `PROJECT/1-INBOX/GH-*.md` is first-class intake and must also be parked in `ROADMAP.md` as a one-line queue entry immediately at capture, then promoted or removed later. Enforced by `utils/pdda/pdda.sh roadmap-coverage`; governance lives in `PROJECT/PDDA.md`.
- Do not create a second competing plan when a canonical `PROJECT/**` doc already exists.
- Do not build a redundant solution when extending an existing one is viable (enforced by PDDA Phase 0 review). If >50% of the new solution overlaps with an existing one, the plan MUST include deprecating/deleting the old one.
- SQLite has exactly two gateways, and they are **separate stores by design** — `src/rebalance/ingest/db/` opens this project's own index (path resolved from `REBALANCE_DB`), while `HiQS/hiqs/db.py` opens the HiQS clean-room rebuild's app-data store, staged to spin out to its own repo. They address different database files and are not converged (settled in GH-136, 2026-08-30). New SQLite access goes through one of them: a direct `sqlite3.connect` anywhere else is pinned by `utils/pdda/check_banned_imports.py --check` against `utils/pdda/sqlite_connect_baseline.json` and fails CI — additions *and* stale baselines both block.
- Do not override deterministic PDDA findings with prose.
- Do not report a win you did not verify with `rebalance doctor`, `pytest tests/`, or the relevant PDDA check.

## Command rails

For setup/health:

```bash
rebalance doctor
```

For code correctness:

```bash
pytest tests/
```

For document hygiene:

```bash
utils/pdda/pdda.sh run
```

For local job health (3-Eyes — optional, inert unless activated on the device):

```bash
cd utils/3-eyes && PYTHONPATH=$PWD python3 -m three_eyes status   # is it active, what is managed
PYTHONPATH=$PWD python3 -m three_eyes health                      # fleet health (run UNSANDBOXED — see below)
PYTHONPATH=$PWD python3 -m three_eyes catalog --check             # catalog drift vs the live machine
PYTHONPATH=$PWD python3 -m three_eyes why <job>                   # why a job did/didn't run
```

`health` and `catalog` shell out to `launchctl list`; a sandboxed shell blocks it and every job
reads back `not-loaded`. Re-run unsandboxed before believing a health result.

For targeted PDDA debugging:

```bash
utils/pdda/pdda.sh frontmatter
utils/pdda/pdda.sh status-table
utils/pdda/pdda.sh hardcoded-paths
utils/pdda/pdda.sh roadmap
utils/pdda/pdda.sh roadmap-coverage
utils/pdda/pdda.sh changelog
utils/pdda/pdda.sh stale
utils/pdda/pdda.sh quad-concepts     # opt-in: a "## Quad Concepts" section of 1-4 bullets (lever: .pdda-quad / PDDA_QUAD)
utils/pdda/pdda.sh glance            # read-only roll-up: title + Quad Concepts for each PROJECT/2-WORKING doc
utils/pdda/pdda.sh issue-doc-sync    # flag 2-WORKING/GH-*.md docs drifted from their GitHub issue state (warn-only)
utils/pdda/pdda.sh gh-refresh        # refresh the cached GitHub issue-state file issue-doc-sync reads offline (needs gh)
utils/pdda/pdda.sh releases    # validate RELEASES.md, the release-planning ledger (warn-only nudge)
utils/pdda/pdda.sh releases-current  # read-only roll-up: RELEASES.md entries whose Status isn't "Shipped"
utils/pdda/pdda.sh governance  # governance-doc cross-reference + doc/code drift (this file, AGENTS.md, CLAUDE.md, ...)
utils/pdda/pdda.sh banned-imports # AST-level import linter flagging banned modules outside rebalance.lib
utils/pdda/pdda.sh doc-ready   # LLM readiness review — set PDDA_LLM_BIN (codex/claude/agy) for recommendations, else it self-skips
utils/pdda/pdda.sh catchup     # LLM repo triage and ROUTER.md recommendations — opt-in like doc-ready
utils/pdda/pdda.sh help
```

## Routing hints

- If the task is about current priorities or active work, start in `ROADMAP.md`, then follow the linked `PROJECT/**` doc.
- If the task is about data sources, refresh, or "why is X empty?", start with `rebalance doctor`, then `src/rebalance/ingest/index_ops.py` (the `COLLECTORS` registry).
- If the task is about retrieval or synthesis (the read side), start in `src/rebalance/querier.py`.
- If the task is about the MCP tool surface or operator onboarding, start in `AGENTS.md`.
- If the task is about document quality, active-doc lifecycle, roadmap sprawl, or automation policy, start in `PROJECT/PDDA.md`.
- If the task is about installing PDDA into another repo, read `PDDA-INSTALL.md`.
- If the task originates from a GitHub issue, capture it as `PROJECT/1-INBOX/GH-<number>-SHORT-DESCRIPTION.md`, then follow the normal `1-INBOX` → `2-WORKING` flow.
- If the task is about job health, what is scheduled on this device, or adopting an automation under supervision, use the `/3-eyes` skill (`utils/3-eyes/`, `python -m three_eyes health|catalog|list`). For raw launchd triage below that layer, use `/launchd-triage`. 3-Eyes is **inert by default** — a clone with no gitignored `config/runtime.env` is a clean no-op, so "3-Eyes says nothing" on a fresh machine means *not activated*, not *nothing wrong*.
