# GH-316 final consult (verbatim)

Codex review of HEAD 61c431f, 2026-10-03. Verdict: CHANGES with two small omissions
(manifest tool metadata; date-sensitive parity fixture) — both fixed in the next commit;
raw transcript fenced verbatim (GH-88 rationale).

## Prompt

```
# FINAL implementation review — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter

You are reviewing the COMMITTED implementation on branch `feat/hiqs-work-activity-naming` (HEAD). This is the final QA after plan round 1 (CHANGES) whose corrections were accepted. Grade against the stated requirements and commensurate complexity — labels-and-aliases change; do not demand enterprise machinery.

## Requirements (issue #316)

1. REQUIRED backwards-compat adapter: canonical MCP tool `hiqs_work_activity`; `github_balance` stays registered, functional, docstring marks it deprecated alias; Python `get_hiqs_work_activity()` canonical, `get_github_balance` alias.
2. Contract freeze: table `github_activity`, SQL reader `fetch_github_balance`, and the NINE output keys (`project_name`, `repos_linked`, `repos_touched`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `is_idle`) unchanged.
3. Label rule: signal-presenting strings say "HiQS work activity"; raw-source ingestion strings stay literal ("GitHub activity"). Dashboard "Recent GitHub Activity" (org rollup via `fetch_org_activity`) deliberately RETAINED — different signal, disposition recorded in the plan QA log.

## Review these

- `git log --oneline origin/development..HEAD` and `git diff origin/development..HEAD` (5 commits: intake capture, plan promotion, implementation, evidence retention)
- `src/rebalance/ingest/github_scan.py` (rename + alias), `src/rebalance/mcp/tools/projects.py` (two tools), `src/rebalance/ingest/querier.py`, `src/rebalance/cli/query.py`, `src/rebalance/cli/github.py`
- `tests/test_hiqs_work_activity_alias.py` (parity test: both tool names via real FastMCP server, identical populated rows, exact nine-key set, `get_github_balance is get_hiqs_work_activity`)
- `MCP.md`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, version 0.98.1 in `pyproject.toml`/`manifest.json`/`src/rebalance/__init__.py`
- `PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md` (QA log + dispositions), `TESTS-RESULTS/2026-10-03+GH-316/`

## Test evidence (already run)

- Focused: `test_hiqs_work_activity_alias.py` (2, red-first witnessed) + `test_mcp_probe.py` + `test_queries_mirror_invariance.py` + `test_github_readiness.py` — 40 passed.
- Full suite: 2651 passed / 2 failed — (a) `test_doctor_scheduled_stack::test_declared_root_overrides_running_checkout` reproduces on unchanged `development` on this machine (device-environment, pre-existing); (b) `test_doc_links::test_repo_is_clean` failed on the raw consult transcript left untracked at repo root — fixed by committing it fenced under `TESTS-RESULTS/2026-10-03+GH-316/qa/`; `test_doc_links.py` now 9/9 green. No src/ changes after the full-suite run; doc-links + ratchets re-run green on the final head.
- Ratchets: read-layer clean (52 sites), script-inventory clean; ruff format/check + mypy clean; `pdda.sh run` 25 observe-mode errors, all pre-existing on unrelated docs, none referencing GH-316.

## Questions

1. Does each issue requirement hold in the actual code? Any consumer broken by the rename?
2. Is the alias seam correct at both boundaries (MCP tool + Python function), with the frozen contract intact?
3. Does the parity test substantiate the adapter claim (would it catch a regression)?
4. Any duplicate subsystem, accidental file, or scope creep in the diff?

Output: verdict APPROVE / CHANGES with numbered findings citing file:line.

```

## Advisor output

```
**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)

> **ATTESTATION**
> Model: gpt-6-astra
> Provider: openai
> Sandbox: read-only

Reading additional input from stdin...
OpenAI Codex v0.159.1
--------
workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
model: gpt-6-astra
provider: openai
approval: never
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a1009e-7a01-79e3-83b5-1dd808c5c6ce
--------
user
You are an INDEPENDENT advisor in a one-shot cross-model consult. Another model is answering the SAME question separately and a coordinator will reconcile both answers, so give your own honest, specific read — do not hedge toward a consensus you cannot see. Read any repo files the question references (cite file:line). Respond with: (1) a short direct ANSWER; (2) graded FINDINGS — [Blocker]/[Should]/[Nit]/[Pass] — where applicable; (3) a one-line RECOMMENDATION. You are ADVISORY ONLY: output your analysis as text; do not rely on writing files (you are running in a throwaway copy).

=== CONSULT QUESTION ===
# FINAL implementation review — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter

You are reviewing the COMMITTED implementation on branch `feat/hiqs-work-activity-naming` (HEAD). This is the final QA after plan round 1 (CHANGES) whose corrections were accepted. Grade against the stated requirements and commensurate complexity — labels-and-aliases change; do not demand enterprise machinery.

## Requirements (issue #316)

1. REQUIRED backwards-compat adapter: canonical MCP tool `hiqs_work_activity`; `github_balance` stays registered, functional, docstring marks it deprecated alias; Python `get_hiqs_work_activity()` canonical, `get_github_balance` alias.
2. Contract freeze: table `github_activity`, SQL reader `fetch_github_balance`, and the NINE output keys (`project_name`, `repos_linked`, `repos_touched`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `is_idle`) unchanged.
3. Label rule: signal-presenting strings say "HiQS work activity"; raw-source ingestion strings stay literal ("GitHub activity"). Dashboard "Recent GitHub Activity" (org rollup via `fetch_org_activity`) deliberately RETAINED — different signal, disposition recorded in the plan QA log.

## Review these

- `git log --oneline origin/development..HEAD` and `git diff origin/development..HEAD` (5 commits: intake capture, plan promotion, implementation, evidence retention)
- `src/rebalance/ingest/github_scan.py` (rename + alias), `src/rebalance/mcp/tools/projects.py` (two tools), `src/rebalance/ingest/querier.py`, `src/rebalance/cli/query.py`, `src/rebalance/cli/github.py`
- `tests/test_hiqs_work_activity_alias.py` (parity test: both tool names via real FastMCP server, identical populated rows, exact nine-key set, `get_github_balance is get_hiqs_work_activity`)
- `MCP.md`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, version 0.98.1 in `pyproject.toml`/`manifest.json`/`src/rebalance/__init__.py`
- `PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md` (QA log + dispositions), `TESTS-RESULTS/2026-10-03+GH-316/`

## Test evidence (already run)

- Focused: `test_hiqs_work_activity_alias.py` (2, red-first witnessed) + `test_mcp_probe.py` + `test_queries_mirror_invariance.py` + `test_github_readiness.py` — 40 passed.
- Full suite: 2651 passed / 2 failed — (a) `test_doctor_scheduled_stack::test_declared_root_overrides_running_checkout` reproduces on unchanged `development` on this machine (device-environment, pre-existing); (b) `test_doc_links::test_repo_is_clean` failed on the raw consult transcript left untracked at repo root — fixed by committing it fenced under `TESTS-RESULTS/2026-10-03+GH-316/qa/`; `test_doc_links.py` now 9/9 green. No src/ changes after the full-suite run; doc-links + ratchets re-run green on the final head.
- Ratchets: read-layer clean (52 sites), script-inventory clean; ruff format/check + mypy clean; `pdda.sh run` 25 observe-mode errors, all pre-existing on unrelated docs, none referencing GH-316.

## Questions

1. Does each issue requirement hold in the actual code? Any consumer broken by the rename?
2. Is the alias seam correct at both boundaries (MCP tool + Python function), with the frozen contract intact?
3. Does the parity test substantiate the adapter claim (would it catch a regression)?
4. Any duplicate subsystem, accidental file, or scope creep in the diff?

Output: verdict APPROVE / CHANGES with numbered findings citing file:line.

hook: SessionStart
hook: SessionStart Completed
codex
I’ll inspect the committed diff, adapter boundaries, and parity test, then give an advisory verdict with file-and-line evidence.

exec
/bin/zsh -lc 'git log --oneline origin/development..HEAD
 git diff --stat origin/development..HEAD
 cat ARCHITECTURE.md SOP.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
 succeeded in 6597ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-J2GZJp2O' (errno=Operation not permitted)
2026-10-03 00:16:00.323 xcodebuild[34156:320123269]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:00.899 xcodebuild[34156:320123163] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YPWPYCU5' (errno=Operation not permitted)
2026-10-03 00:16:01.828 xcodebuild[36825:320127292]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:02.078 xcodebuild[36825:320127200] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
61c431f docs(GH-316): retain plan-consult transcript verbatim under TESTS-RESULTS
a35b023 feat(GH-316): rename the work-activity signal to HiQS work activity with a backwards-compatibility adapter
f83ad2e docs(GH-316): promote HiQS work activity naming plan to 2-WORKING
054262f docs(GH-316): capture HiQS work activity naming intake in 1-INBOX
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-PtQNxXUI' (errno=Operation not permitted)
2026-10-03 00:16:03.626 xcodebuild[38349:320129838]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:03.869 xcodebuild[38349:320129792] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-7BDKrKQ7' (errno=Operation not permitted)
2026-10-03 00:16:04.576 xcodebuild[39090:320131189]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:04.834 xcodebuild[39090:320131157] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
 AGENTS.md                                          |    6 +-
 CHANGELOG.md                                       |    6 +
 MCP.md                                             |    8 +-
 .../2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md  |   95 +
 README.md                                          |    2 +-
 ROADMAP.md                                         |    1 +
 TESTS-RESULTS/2026-10-03+GH-316/SUMMARY.md         |    5 +
 .../2026-10-03+GH-316/qa/plan-consult-r1.md        | 2593 ++++++++++++++++++++
 manifest.json                                      |    2 +-
 pyproject.toml                                     |    2 +-
 src/rebalance/__init__.py                          |    2 +-
 src/rebalance/cli/github.py                        |    2 +-
 src/rebalance/cli/query.py                         |    2 +-
 src/rebalance/ingest/github_scan.py                |   15 +-
 src/rebalance/ingest/querier.py                    |    8 +-
 src/rebalance/mcp/tools/projects.py                |   25 +-
 tests/test_hiqs_work_activity_alias.py             |   83 +
 17 files changed, 2830 insertions(+), 27 deletions(-)
# rebalance OS — ARCHITECTURE.md

> **Before building anything, check whether it already exists.** The four prior-art checks (open PRs on *both* repos, `ROADMAP.md` → In progress, a cross-package grep including `HiQS/` and `utils/3-eyes/`, and the full suite including the parts CI skips) are in [ROUTER.md](ROUTER.md) — canonical there, deliberately not restated here.


> How data flows through the system. For execution decisions see the [PROJECT/](PROJECT) docs — canonical detail for a specific effort, governed by [PROJECT/PDDA.md](PROJECT/PDDA.md) — for tool specs see [MCP.md](MCP.md), for the *why* behind these decisions see [GUIDING-PRINCIPLES.md](GUIDING-PRINCIPLES.md).

> **New maintainer? Start with [Maintainer Orientation](#maintainer-orientation-start-here)** — the load-bearing symbols, the two hubs, where to start reading, and one end-to-end trace. **This doc is load-bearing, not decorative:** `audit_modules` (the `audit_modules` MCP tool / [scripts/audit_modules.py](scripts/audit_modules.py)) and the PDDA gate enforce that collectors, render modules, and scheduled jobs stay documented here — update ARCHITECTURE.md in the *same PR* as any structural change.

---

## Core Pipeline

**Opt-in historical projection (GH-230):** `src/rebalance/ingest/clio_journey.py` (run as `rebalance clio-journey-replay`) reads a frozen CLIO JSONL
prefix or canonical marker-backed Markdown export and existing GitHub snapshots via the read-only
DB gateway. It emits a new private run directory with two journey views, source evidence and coverage.
It is not an `all` collector, never updates the index, and does not call a model or publish into a vault.
Its opt-in `--explicit-links-only` policy joins outcomes only through typed qualified GitHub URLs;
other mentions are retained under `unresolved_refs` and excluded from grouping/event attachment.
The independent `--qualified-transitions` option adds a third candidate view for exact new-task
requests naming a different qualified issue. Its grouping and event joins use qualified URLs
regardless of legacy reference settings. Original views and start hints remain unchanged; a split
is not completion. The GH-232 retained-metadata composition recipe is campaign-only, not a new
runtime adapter or collector.
The independent `--issue-evidence` flag appends all qualified trial-issue mentions, including
unassigned prompts, with separate chat labels and visible coverage gaps. It does not alter original
grouping, start hints or evidence membership. Pull-request/foreign/bare-number mentions cannot
supply trial-issue identity; direct issue facts retain event and retrieval times separately.
The campaign-only retained-facts recipe can compose `closingIssuesReferences` via `--delivery-links`
and append three fixed A/B comparisons via `--review-cases`. Whole artifact URLs, typed identities,
merge state/window, retrieval chronology and conflicting records are checked before publication.
This is not the production `github_links` text-matching store or reconciliation scorer. Optional
renderer metadata adds observed relationship receipts, never chat causation or deployment proof.

**INVARIANT**: **Compose, don't mutate**. No new query surfaces (like `semantic_query` vs `ask`) or UI renderers (web server vs static HTML) may be introduced without a plan to deprecate and replace the old one. If extending an existing pipeline, build reusable primitives in `src/rebalance/lib/` instead of duplicating logic in the caller.

```
Signals (data sources)
  │
  ▼
Ingest Layer (source-specific collectors)
  │
  ▼
SQLite + sqlite-vec (unified local store)
  │
  ▼
Query Layer (context gathering + prompt assembly)
  │
  ▼
Two-Layer LLM
  ├── Layer 1: Local Qwen3 (fast first-pass synthesis)
  └── Layer 2: Host Agent (review, adapt, present)
  │
  ▼
User (via MCP host: VS Code, Claude Desktop, etc.)
```

Every raw incoming source follows the same pattern: **collect → normalize → store → query**. The collector registry in `index_ops.py` currently also includes derived local scans and post-ingest/export jobs (`code`, `semantic`, `sync`, `focus5`, `ask_self`), so not every registered scope is a raw upstream signal. The query layer and LLM layers are source-agnostic once data is in SQLite.

### Sync model (in plain English)

Every `refresh_index` run is **incremental** — nothing is re-downloaded from scratch. What "incremental" means depends on what the upstream API lets us ask for cheaply, but three patterns cover every source:

1. **Hash/ID delta** — only fetch or reprocess what actually changed. Used by: vault notes, GitHub artifacts, embeddings.
2. **Window refetch + upsert** — refetch a bounded time-or-count window every run and upsert by ID; nothing is auto-deleted. Used by: GitHub activity (last 30d events), calendar (30d back / 7d forward), email (newest 100 `in:inbox` messages).
3. **Full refetch + column-diff** — refetch the whole upstream set, compare row-by-row, and keep everything as history. Used by: sleuth reminders.

A few caps to know about up-front:

- **Email** is capped at the **newest 100 inbox messages per run** today (Phase 1, shipped 2026-05-12) — default filter `in:inbox`, overridable via `gmail_query_filter` in `temp/rbos.config`. Not "important and starred." See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).
- **Calendar** refetches a **30-day back / 7-day forward window** by default; a 365-day backfill is available on demand via the CLI.
- **GitHub activity** is bounded by the GitHub Events API's own ~30-day retention.
- **Vault, sleuth, embeddings** are unbounded — they cover everything they can see.

Detailed per-source mechanics live in [Storage Layer → Sync semantics per source](#sync-semantics-per-source).

---

## Maintainer Orientation (start here)

New to the codebase? Read this section first — it is the mental model the rest of the doc assumes.

### The two hubs (the model that prevents confusion)

The system has **two** central things with *opposite* roles. Conflating them is the most common newcomer mistake:

- **Orchestration spine — fan-OUT.** `refresh_index()` plus the `COLLECTORS` registry in
  [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py) reach **out** into every collector. This is the
  one intended write/refresh entry point. New ingestion work registers here (`register_collector(Collector(...))`).
- **Persistence base — fan-IN.** [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_database_path()` (answers *which* DB file)
  → `db_connection()` in [src/rebalance/ingest/db/](src/rebalance/ingest/db) (answers *how* to open it). Everything reaches **down** to these.

They compose in a single hop (`refresh_index() → db_connection()`). Keeping orchestration and persistence in
**separate** nodes is *why the codebase has no god-object* despite `db_connection()` being the single most-connected
symbol: it is a thin, stateless connection factory (a dependency *sink*), not a place where logic lives. **Read from it
freely; think twice before changing it** — its blast radius is the whole system.

### Load-bearing symbols (you will see these in almost every file)

| Symbol | Where | What it is / why it's everywhere |
|---|---|---|
| `db_connection()` | `ingest/db/connection.py` | SQLite factory (WAL, foreign keys, 30s busy-timeout, sqlite-vec). Every collector opens its connection here. **High fan-in, zero business logic.** |
| `resolve_database_path()` | `paths.py` | "Which DB file" — layered resolver (`--database` flag → `REBALANCE_DB` → canonical app-data path → user config). Single source of truth for the DB location. |
| `_read_config()` / `_write_config()` | `ingest/config.py` | Layered config + secrets (`temp/rbos.config` + keyring/secret-store). |
| `CalendarConfig` | `ingest/calendar_config.py` | Validated calendar settings (event filters, signal weights). |
| `normalize_github_repo_name()` | `ingest/github_scan.py` | Canonical `owner/repo` string used across every GitHub path. |
| `refresh_index()` | `ingest/index_ops.py` | The orchestrated ingest entry point (see "two hubs" above). |
| `rank_next_actions()` | `ingest/next_actions.py` | Entry point for the "what to do next" engine (see [Query Layer](#the-next-actions-engine-what-to-do-next)). |
| `run_doctor()` | `doctor.py` | Health-check orchestrator; backs `rebalance doctor` (run it before claiming a change works). |

### Where to start reading when touching X

| If you're working on… | Start in | Then read |
|---|---|---|
| A data source (add/fix ingest) | `ingest/index_ops.py` (the `COLLECTORS` registry) + that source's `ingest/<source>.py` | [Adding a New Source](#adding-a-new-source) |
| The read / query side | `ingest/semantic_index.py` (retrieval primitive) + `ingest/querier.py` (`ask()` orchestrator) | [Query Layer](#query-layer) |
| Focus 5 roster / ranking | `ingest/focus5_scan.py` | the `web.py` `/focus-5` route |
| Apple Reminders | `ingest/apple_reminders.py` (read) + `ingest/apple_reminders_write.py` (write, via signed helper) | — |
| "What to do next" | `ingest/next_actions.py` | [The Next Actions engine](#the-next-actions-engine-what-to-do-next) |
| Web dashboard surfaces | `web.py` + `web_components.py` | [Invocation Modes](#invocation-modes) |
| Config / secrets | `ingest/config.py` + `paths.py` | [Credentials](#credentials) |
| Scheduling / launchd jobs | [SCHEDULER.md](SCHEDULER.md) + `scripts/*_sync.sh` | [Invocation Modes](#invocation-modes) |
| The database itself (schema/migrations) | `ingest/db/` (connection, schema, migrations) | [Storage Layer](#storage-layer) |

### One request, end-to-end (worked trace)

A `rebalance refresh` (or the `refresh_index` MCP tool) flows through real symbols like this:

1. **`refresh_index()`** [`index_ops.py`] resolves the scope and iterates the `COLLECTORS` registry (each entry added via `register_collector(Collector(...))`).
2. Each collector's **`sync_*()`** runs fetch → normalize → upsert — e.g. `sync_apple_reminders()`, `github_scan()`, `sync_sleuth_reminders()`.
3. The collector opens storage via **`db_connection(path, ensure_<source>_schema)`** and upserts (e.g. `sync_apple_reminders()` → `upsert_apple_reminders()` → `db_connection()`).
4. **Derived stages** follow (`code`, `semantic`, `sync`): the unified semantic index is rebuilt by `backfill_semantic_documents()` and embedded.
5. **Read side:** `semantic_index.query()` (raw retrieval primitive; MCP `semantic_query`) and `querier.ask()` (broad synthesis orchestrator) read the *same* SQLite via `resolve_database_path()` → `db_connection()`.
6. **Surfaces:** the `web.py` routes (`/focus-5`, `/auth-log`, what's-next), the Typer CLI, and the MCP tools all read through that one persistence base.

---

## Signal Sources

Raw incoming sources have a priority, a collector module, and a target table. The table below is the canonical field spec; for per-effort execution detail see the [PROJECT/](PROJECT) docs, and for current status see [ROADMAP.md](ROADMAP.md).

| Priority | Source | Collector | Storage | Vectorized | Status |
|----------|--------|-----------|---------|------------|--------|
| P1 | GitHub | `github_scan.py` + `github_knowledge.py` + `github_readiness.py` + `github_reconciliation.py` | `github_activity`, `github_repo_meta`, `github_branches`, `github_items`, `github_comments`, `github_documents`, `github_embeddings` | Yes — structured repo signals plus semantic corpus for issues, PRs, comments, reviews, commit messages, and issue/PR reconciliation | Active |
| P1 | Obsidian Vault | `note_ingester.py` + `embedder.py` | `vault_files`, `chunks`, `keywords`, `links`, `embeddings` | **Yes** — Qwen3-Embedding-0.6B, 1024-dim, sqlite-vec | Active |
| P2 | Google Calendar | `calendar.py` | `calendar_events` table (default window 30d back / 7d forward; no auto-deletion) | No — structured event data | Active |
| P3 | Sleuth reminders (Slack) | `sleuth_reminders.py` | `sleuth_reminders` table | No — structured reminder rows | Active |
| P4 | Email (Gmail) | `gmail.py` + `semantic_index.py` | `email_messages` | Yes — subject + snippet participate in the unified semantic index | Active (Phase 1, shipped 2026-05-12): newest 100 `in:inbox` messages per run; metadata + snippet only, no body parsing yet |
| P4 | Figma comments | `figma.py` + `semantic_index.py` | `figma_comments` | Yes — registry-provider semantic docs for comments | Active (opt-in): requires a PAT plus explicit `figma_file_keys` allow-list |

### Other registered collector scopes

These are registered in `index_ops.py` and dispatch through the same `refresh_index()` orchestrator, but they are not raw upstream data sources:

| Scope | Kind | Purpose | Included in `all` |
|---|---|---|---|
| `code` | derived local scan | AST/code chunk collection into the unified semantic index | Yes |
| `semantic` | projection stage | Unified semantic backfill + embed maintenance | Yes |
| `sync` | export stage | Export calendar/email snapshots to the pulse sync repo | Yes |
| `focus5` | derived local scan | Build the device-local Focus 5 roster + signal cache | No |
| `ask_self` | derived local scan | Inventory ask_self indexes on this device | No |

### Source → Table fanout

```
EXTERNAL SOURCES                  INGESTORS (src/rebalance/ingest/)                  STORAGE
                                                                                     (SQLite @ $REBALANCE_DB
                                                                                      + sqlite-vec)

GitHub REST API ─────▶ github_scan.py            user events (last 30d)       ──▶ github_activity
  (api.github.com)   │                                                            github_repo_meta
                     ├▶ github_knowledge.py      per-repo artifacts:           ──▶ github_items (issues/PRs)
                     │                             issues, PRs, comments,          github_comments
                     │                             reviews, commits, checks,       github_commits
                     │                             branches, milestones,           github_check_runs
                     │                             releases                        github_branches
                     │                                                             github_milestones
                     │                                                             github_releases
                     │                                                             github_links
                     │                                                             github_documents
                     │                                                          ─ github_embeddings (vec0)
                     ├▶ github_readiness.py      release-state inference       ── (reads only)
                     └▶ github_reconciliation.py issue ↔ PR matching           ── (reads only)

Obsidian Vault ──────▶ note_ingester.py          walk *.md, chunk, TF-IDF,    ──▶ vault_files, chunks,
  (filesystem)       │                             wikilinks                       keywords, links
                     └▶ embedder.py              Qwen3-Embedding-0.6B         ──▶ embeddings (vec0, 1024-dim)
                                                   via mlx-embeddings

Google Calendar ─────▶ calendar.py               OAuth token (keyring+JSON),  ──▶ calendar_events
  (Calendar API)                                   30d back / 7d forward

Sleuth Web API ──────▶ sleuth_reminders.py       Bearer auth, stdlib urllib,  ──▶ sleuth_reminders
  (Vultr dev :2020)                                GET /workspace/<name>/
                                                   reminders?format=rebalance

Gmail API ───────────▶ gmail.py                  desktop OAuth (gmail.readonly), ──▶ email_messages
  (gmail.googleapis.com)                           filter in:inbox by default,
                                                   newest 100 messages/run

Gmail MCP connector ─▶ gmail.py                  agent-pushed message payloads ─▶ email_messages
  (opt-in push path)                               via ingest_email_messages()

Figma Comments API ───▶ figma.py                 file-key allow-list + PAT    ──▶ figma_comments
  (api.figma.com)                                                                        │
                                                                                         └─▶ semantic_documents
                                                                                             semantic_embeddings

Project Registry ────▶ registry.py +              MD registry → projects.yaml ──▶ project_registry
  (vault markdown)     preflight.py                → SQLite projection
```

### Invocation points

| Source | CLI | MCP tool(s) | Daily-sync step |
|---|---|---|---|
| GitHub activity | `rebalance github-scan` | `github_balance` | 3 |
| GitHub artifacts | `rebalance github-sync-artifacts`, `github-embed`, `github-query` | `semantic_query`, `github_release_readiness`, `github_close_candidates` | on demand |
| Obsidian vault | `rebalance ingest notes`, `ingest embed`, `query`, `search` | `semantic_query`, `search_vault` | 1 + 2 |
| Google Calendar | `rebalance calendar-sync`, `calendar-create-event`, `calendar-snap-edges`, `calendar-daily-report`, `calendar-weekly-report` | `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges` | 4 |
| Sleuth reminders | `rebalance sleuth-sync` | `sleuth_sync_reminders` | 5 |
| Email (Gmail) | `rebalance refresh`, `semantic-backfill`, `semantic-query` | `refresh_index`, `semantic_query`, `ingest_gmail_messages` | 6 |
| Figma comments | `rebalance refresh` | `refresh_index` | opt-in |
| Focus 5 | `refresh_index(scope=["focus5"])`, `rebalance serve` / pulse server | web `/focus-5` route | opt-in |
| ask_self inventory | `refresh_index(scope=["ask_self"])` | `list_ask_self_repos` | opt-in |
| Project registry | `rebalance ingest preflight`, `ingest sync`, `onboard` | `list_projects`, `run_preflight`, `confirm_projects`, `onboarding_status` | on demand |

> Registry write discipline (Phase 5, `ingest/lifecycle.py`): discovery is
> read-only and stamps candidates with `provenance` (remote-activity /
> vault-note; local-scan reserved); `confirm_and_write` is the only curated
> write path; activity inference maintains only rows it created (marked
> `inference.generated_by`) and never touches curated rows; priority rules
> overlay at read time and are never persisted.

> Preferred write path: `refresh_index(scope=[...])` is the orchestrated entry
> point. Several source-specific CLI/MCP write commands still exist for
> historical/operator reasons, but some of them bypass the collector/orchestrator
> layer and call leaf ingest functions directly.

> **Sleuth production is read from a published file — no inbound access.** The
> Sleuth box pushes its reminders to a private git repo
> (`rebalance-git-pulse:sync/sleuth/reminders-<ws>.json`); rebalance-OS reads the
> local clone (`base_url` is a `file://`/local path). No SSH tunnel, no open port.
> See [SLEUTH_SYNC.md](SLEUTH_SYNC.md). (Dev still hits the API directly.)

### Source → Consumer fanout (report & synthesis surfaces)

The GH-150 contract: every surface that reads the activity signal — script entrypoint,
scheduled job, MCP tool — has a row here, so "is this new report needed, and what does
it read?" is answered in the diff instead of buried in a 400-line file.
`tests/test_consumer_catalog.py` enumerates entrypoints (`__main__` under `utils/` +
`scripts/`, minus the pdda tooling and the stood-down 3-Eyes tree), scheduled-job
scripts (the SCHEDULER.md policy table), and MCP tools (`@mcp.tool()` in
`src/rebalance/mcp/tools/`) and fails on any surface without a row
(`uncataloged consumer`). Column rules the test enforces: **LLM primitive** is `querier`,
`none`, or `own (R2-baseline: <path>)` — a private client may only exist by naming the
ratchet baseline that will shrink when it dies; **Input path** containing "own SQL"
must name its `R1-baseline:` file the same way; **Replaces** is `—` or an existing
Surface. When fe1's shared read layer lands, new rows must read `db/queries.py` and the
baseline references become violations.

| Surface | Entrypoint | Cadence | Input path | LLM primitive | Channel | Replaces |
|---|---|---|---|---|---|---|
| Daily full refresh | scripts/daily_sync.sh | daily 06:30 | orchestrator (`refresh_index`) | none | DB write | — |
| Hourly GitHub sync | scripts/github_sync.sh | hourly :45 | orchestrator (`refresh_index`, artifact window 7d) | none | DB write | — |
| Vault embeddings job | scripts/obsidian_vault_embeddings.sh | hourly :15 | orchestrator (`refresh_index` vault+semantic) | none | DB write | — |
| Pulse page | scripts/pulse_sync.sh | hourly :00 | pulse renderer (own SQL R1-baseline: src/rebalance/ingest/pulse.py) | none | pulse repo README | — |
| Pulse web render | scripts/pulse_web_sync.sh, scripts/pulse_web.py | 30 min | pulse renderer (same snapshot) | none | web/pulse.html | Pulse page |
| Pulse server | scripts/pulse_server.sh, scripts/pulse_server.py | daemon | DB read layer + pulse renderer | none | localhost:8767 | — |
| Pulse warning watch | scripts/pulse_warning_watch.py | 15 min | HTTP probe of pulse-server | none | temp JSONL | — |
| Daily work synthesis canary | scripts/daily_work_synthesis.sh, utils/daily_work_synthesis.py | 15 min, opt-in | existing CLIO/calendar/reminder read APIs + Daily repository/CPU scanners | own (R2-baseline: utils/daily_work_synthesis.py) | append-only temp Daily log + sanitized receipt JSONL | — |
| CLIO journey replay | src/rebalance/ingest/clio_journey.py (`rebalance clio-journey-replay`) | manual, opt-in | frozen CLIO export + bounded read-only GitHub snapshot (GH-230 exception) | none | new private replay directory | — |
| Health issue reporter | scripts/health_issue_reporter.py | hourly :10 + 3×/day triage | doctor subprocess + GitHub API | own (R2-baseline: scripts/health_issue_reporter.py) | GitHub issues | — |
| Daily note rollover | utils/obsidian_rollover.sh, utils/obsidian_daily_rollover.py | daily 00:40 | vault filesystem | none | Obsidian daily note | — |
| Progress digest | scripts/hiqs_digest.sh, utils/hiqs_digest.py | 2×/day 13:05/17:05 | own SQL (R1-baseline: utils/hiqs_digest.py) + doctor + semantic | querier | pulse repo digests/ → Slack relay | — |
| Daily synthesis | utils/daily_synthesis.sh, utils/daily_synthesis.py | daily 18:20 | pulse.collect_pulse_snapshot + git-pulse device files | querier | Obsidian note + CLIO log | — |
| Dashboard note | src/rebalance/ingest/note_builder.py | on refresh | own SQL (R1-baseline: src/rebalance/ingest/note_builder.py) + calendar | own (R2-baseline: src/rebalance/ingest/note_builder.py) | vault dashboard note | — |
| Claude Cloud signal grade | utils/claude_cloud_daily_grade.py | daily | ingest/claude_cloud sessions API | none | Obsidian block | — |
| Claude Cloud jobs POC | scripts/cc_cloud_jobs.py | manual | api.anthropic.com fetch (R2-baseline: scripts/cc_cloud_jobs.py) + gh | none | stdout + temp/ | Claude Cloud signal grade |
| Web dashboard data | scripts/dashboard.py | manual | own SQL (R1-baseline: scripts/dashboard.py) | none | dashboard payload | — |
| Chat eval | scripts/chat_eval.py | manual | eval corpus | none | stdout | — |
| Module audit | scripts/audit_modules.py | manual / MCP | repo tree + docs | none | audit report | — |
| Doc link check | scripts/check_doc_links.py | manual | repo docs | none | stdout | — |
| Extension build | scripts/build_extension.py | manual | capabilities tree | none | built artifacts | — |
| Capabilities index | scripts/generate_capabilities_index.py | manual | repo tree | none | capabilities index | — |
| Calendar OAuth setup | scripts/setup_calendar_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Gmail OAuth setup | scripts/setup_gmail_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Cloud daily grade helpers | utils/job_guard.py | per job | process guard | none | job lifecycle | — |
| Vector store reclaim | utils/gh250/reclaim.py | manual (historical) | vector store | none | store maintenance | — |
| Releases ledger CLI | utils/py/releases_app.py | manual | releases.db | none | ledger + dump | — |
| Releases cycle rollup | utils/py/releases_cycle.py | on demand | releases.db (read-only) | none | rollup markdown/dashboard | — |
| MCP: index_status | src/rebalance/mcp/tools/index.py | on demand | status snapshot (coverage probe) | none | MCP | — |
| MCP: refresh_index | src/rebalance/mcp/tools/index.py | on demand | orchestrator | none | MCP | — |
| MCP: diagnose_repo | src/rebalance/mcp/tools/index.py | on demand | own SQL (R1-baseline: src/rebalance/ingest/diagnose.py) | none | MCP | — |
| MCP: list_watched_repos | src/rebalance/mcp/tools/index.py | on demand | watched-set view | none | MCP | — |
| MCP: list_ask_self_repos | src/rebalance/mcp/tools/index.py | on demand | ask_self index | none | MCP | — |
| MCP: publish_pulse | src/rebalance/mcp/tools/index.py | on demand | pulse renderer | none | MCP | — |
| MCP: peek_source | src/rebalance/mcp/tools/index.py | on demand | parameterized table peek | none | MCP | — |
| MCP: get_next_actions | src/rebalance/mcp/tools/index.py | on demand | next_actions engine (R1-baseline: src/rebalance/ingest/next_actions.py) | querier | MCP | — |
| MCP: semantic_query | src/rebalance/mcp/tools/index.py | on demand | semantic index | none | MCP | — |
| MCP: audit_modules | src/rebalance/mcp/tools/hygiene.py | on demand | repo tree + docs | none | MCP | — |
| MCP: calendar tools | src/rebalance/mcp/tools/calendar.py | on demand | calendar_events | none | MCP | — |
| MCP: onboarding tools | src/rebalance/mcp/tools/onboarding.py | on demand | registry/lifecycle + gmail push | none | MCP | — |
| MCP: projects tools | src/rebalance/mcp/tools/projects.py | on demand | registry; github_balance → own SQL (R1-baseline: src/rebalance/ingest/github_scan.py) | none | MCP | — |
| MCP: retrieval tools | src/rebalance/mcp/tools/retrieval.py | on demand | vault FTS; readiness → own SQL (R1-baseline: src/rebalance/ingest/github_readiness.py) | querier | MCP | — |
| MCP: sleuth tools | src/rebalance/mcp/tools/sleuth.py | on demand | sleuth source | none | MCP | — |

Grouped rows (one row covering several same-shape tools, e.g. "MCP: calendar tools")
name their module; the test resolves them. Two surfaced read paths have no entrypoint
of their own and are carried by the rows above: `pulse.collect_pulse_snapshot`
(daily synthesis) and the querier synthesis primitive itself.

### Credentials

| Source | Secret store | Mechanism |
|---|---|---|
| GitHub | OS keyring + out-of-repo secret store (`~/.config/rebalance-os/secrets`, `0600`) fallback; `gh` CLI as last-resort read fallback | PAT: classic `repo` scope, or fine-grained with All-repos read-only Contents/Metadata (public-only tokens hide private work); persisted to keyring + secret store for launchd reachability — no longer written to `temp/rbos.config` |
| Google Calendar | `google-calendar.env` (client credentials) via `resolve_secret_path()` + OAuth user-token in keyring with a JSON fallback at `~/.config/rebalance-os/secrets/google-calendar-oauth` (a legacy pickle migrates to JSON on read) | OAuth 2.0 user consent |
| Sleuth | OS keyring + secret store (`~/.config/rebalance-os/secrets/sleuth_web_api`); legacy `*.env` files still read for un-migrated devices | Bearer token, 64-hex |
| Gmail | Desktop OAuth token in keyring + JSON fallback at `~/.config/rebalance-os/secrets/google-gmail-oauth`, or MCP push-ingest mode | `gmail.readonly` desktop OAuth, or agent-pushed `ingest_gmail_messages` path when `gmail_ingest_method=mcp` |
| Figma | OS keyring + secret store for the PAT; `temp/rbos.config` holds only the (non-secret) file-key allow-list | Personal access token + explicit file selection |
| Obsidian vault | none | filesystem read only |

Env-file paths resolve via [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_secret_path(name)` — the layered chain is `REBALANCE_SECRETS_DIR` env var → `secrets_dir` field in `~/.config/rebalance-os/config.json` (set via `rebalance config set-secrets-dir`) → `~/secrets/` legacy default. The domain CLI loaders (for example, [src/rebalance/cli/calendar.py](src/rebalance/cli/calendar.py) and [src/rebalance/cli/sleuth.py](src/rebalance/cli/sleuth.py)) use this resolver, so the repo is portable across operator home directories without hardcoded env-file paths. Env files should sit at mode 600. Env files are parsed manually (no `python-dotenv`). Nothing with a secret value is committed.

### Adding a New Source

> **The current preferred way to add a source is the collector / `SourceModule`
> contract — see [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py)
> and the developer guide [PLUGINS.md](PLUGINS.md).** It covers the registry
> descriptor, the optional `semantic_docs` provider, secrets/keyring, numbered
> migrations, and tests, with Figma as the worked example. The steps below are
> the practical recipe for the built-in sources.

1. **Collector** — write `src/rebalance/ingest/<source>.py` following the `sleuth_reminders.py` or `github_scan.py` shape: a dataclass for one record, a `sync_*()` function that fetches → normalizes → upserts, and a module-local `ensure_<source>_schema(conn)`. Use `db_connection(path, ensure_fn)` from the `ingest/db/` package.
2. **Schema** — keep the `CREATE TABLE` inside `ensure_<source>_schema`. Only promote to the shared `ingest/db/` package if more than one module needs it. Use existing tables for unstructured text that should be embedded.
3. **Registry** — register the source in `index_ops.py` with `register_collector(Collector(...))`. Add `requires=...`, `semantic_docs=...`, and/or `candidates=...` metadata if the source needs preconditions, participates in the unified semantic index, or contributes next-action candidates to the HiQS ranking. The `candidates=` provider is how a source reaches the ranked "what to do next" verdict — no edit to the ranker's dispatch.
4. **Credentials** — if the source uses env-style secret files, resolve them through `resolve_secret_path()` and a small domain loader (see `cli/calendar.py` / `cli/sleuth.py`). Never hardcode secrets in repo files.
5. **Next-action candidates** — to feed the HiQS ranking, supply a `candidates=` provider on the `Collector` (a function `bundle → list[candidate dict]`, each Attested with `source`/`evidence`/`why`). `_operator_candidates()` walks the registry, so no ranker edit is needed. A source participates in `ask()` automatically once it is in the ranked bundle — `ask()` reads the whole ranking via `_gather_hiqs_context()`.
6. **Prompt section** — the HiQS section in `_build_prompt()` already renders every ranked source; add a bespoke `_build_prompt()` block only for context that is NOT a ranked next-action.
7. **CLI + MCP** — add thin wrappers in `src/rebalance/cli/*` and `src/rebalance/mcp/tools/*` if the source needs direct user-facing operations beyond `refresh_index()`.
8. **Scheduled refresh** — ensure `included_in_all` and any explicit scheduler usage match the source's intended unattended behavior.
9. **Tests** — add `tests/test_<source>.py` that stubs the outbound call (patch `urlopen` for HTTP, filesystem for local sources). Verify insert / unchanged / update semantics.

No changes needed to the query layer, LLM synthesis, or MCP transport.

---

## Storage Layer

Single SQLite file resolved by `src/rebalance/paths.py::resolve_database_path()`. Default canonical location is `~/Library/Application Support/rebalance-os/rebalance.db` on macOS (or `$XDG_DATA_HOME/rebalance-os/rebalance.db` on Linux); `REBALANCE_DB` env var, an `--database` flag, or a user-config override all win against the canonical path when set. sqlite-vec extension loaded for vector operations.

### Write discipline (one writer per table)

The single most important invariant for a new maintainer to preserve:

- **Reads are unrestricted.** Anything may open `db_connection()` and `SELECT`. The "Tables by Domain" list below names the *writer* for each table — that ownership is about **writes**, not reads.
- **One writer per table.** Each table is written by exactly one module (e.g. `github_activity` ← `github_scan.py`, `sleuth_reminders` ← `sleuth_reminders.py`, `semantic_documents` ← the `semantic` stage only). Do not add a second writer; extend the owning collector instead.
- **Writes go through the orchestrator.** New ingestion/refresh writes register as a `Collector` in `index_ops.py` and run under `refresh_index()` — not as a fresh leaf that opens `db_connection()` and upserts on its own.
- **Known, accepted exceptions (direct `db_connection()` writers outside `refresh_index`).** A few interactive/operator commands write directly *by design* — they are human-in-the-loop mutations, not unattended ingest: `rebalance github-sync-artifacts` (`cli/github.py::github_sync_artifacts()`) and the `rebalance apple-reminders` write path (`cli/apple_reminders.py`). Most other direct `db_connection()` calls from `cli/*` (`onboard`, `config-doctor`, `raw`, `dashboard-render`) are **reads**, which are fine. If you add a new direct *writer*, document it here and say why it can't go through the registry.

### Tables by Domain

```
Project Registry (writer: registry.py::sync_db(), the single low-level upsert)
  project_registry          — canonical project metadata. Rows are either curated
                               (write_semantics="confirmation_gated", written only
                               via the onboarding confirm_projects()/confirm_and_write()
                               path — see lifecycle.py) or machine_owned (never
                               clobbers a curated row of the same name). Two
                               machine_owned producers currently call sync_db():
                               project_inference.py's activity/calendar inference
                               (generated_by "activity_inference_v1") and GH-124's
                               commit-threshold auto-promotion (generated_by
                               "commit_threshold_v1", wired into _refresh_github()
                               in index_ops.py, immediately after the watchlist
                               guard). _is_inference_owned() recognizes both markers.

GitHub activity (writer: github_scan.py)
  github_activity            — per-repo event counts, keyed by (login, repo, scan_date)

GitHub artifacts (writer: github_knowledge.py; schema in `ingest/db/`)
  github_repo_meta           — repo-level metadata (default branch, issue/project support)
  github_branches            — local branch inventory for promotion/release inference
  github_labels              — label dictionary per repo
  github_milestones          — open/closed milestones with due dates
  github_releases            — published tags/releases
  github_items               — issues and PRs (unified table, item_type discriminates)
  github_comments            — issue/PR/review comments
  github_commits             — PR commit history
  github_check_runs          — CI check results per head_sha
  github_links               — explicit and inferred issue↔PR cross-references
  github_documents           — per-artifact embeddable document rows
  github_embeddings          — sqlite-vec virtual table for artifact embeddings
  github_embedding_meta      — model name + dim for the GitHub corpus

Unified Semantic Index (single writer: the `semantic` collector stage in index_ops.py)
  semantic_documents         — canonical cross-source document rows (vault chunks +
                               GitHub issues/PRs/comments/commits, Gmail
                               messages, and registry-provider sources such as
                               Figma comments). Written exclusively by
                               _refresh_semantic_only() via
                               semantic_index.py::backfill_semantic_documents().
                               Consumed by semantic_query() and the LLM context layer.
  semantic_embeddings        — sqlite-vec virtual table, float[1024], keyed by
                               semantic_documents.id. Unified ANN search target.
  semantic_embedding_meta    — model name, dimension, embedder_version, last_embed_at

Vault Ingestion (writer: note_ingester.py)
  vault_files                — one row per .md file, with content_hash for delta detection
  chunks                     — heading-based chunks, FK to vault_files (CASCADE delete)
  keywords                   — TF-IDF top-K per chunk, FK to chunks (CASCADE delete)
  links                      — wikilinks and embeds, FK to vault_files (CASCADE delete)

Embeddings (writer: embedder.py)
  embeddings                 — sqlite-vec virtual table, float[1024], keyed by chunk_id
  embedding_meta             — model name, dimension, last embed timestamp

Email (writer: gmail.py)
  email_messages             — message metadata + snippet, keyed by Gmail message_id.
                               Upsert-only rolling window (newest matching messages);
                               also projected into semantic_documents.

Google Calendar (writer: calendar.py)
  calendar_events            — event id, summary, start/end, location, attendees, description
                               Keyed by Google event ID (INSERT OR REPLACE). Default sync window
                               is 30 days back + 7 days forward (365-day backfill available via
                               the CLI). No automatic deletion; manual cleanup if pruning is needed.

Sleuth reminders (writer: sleuth_reminders.py)
  sleuth_reminders           — one row per Slack reminder, keyed by reminder_id (TEXT PK).
                               Upsert with diff-based insert/update/unchanged counts;
                               first_seen_at preserved across syncs. Rows are never
                               deleted — state transitions (scheduled → posted → completed)
                               are mirrored as UPDATEs.

Figma (writer: figma.py)
  figma_comments             — comment rows keyed by Figma comment key, synced from
                               an explicit file-key allow-list. Also projected into
                               semantic_documents via the registry-provider path.

Device-local inventories / derived jobs
  ask_self_indexes           — per-device inventory of ask_self indexes found on disk
  focus5_repo_signals        — cached per-repo Focus 5 signals for the current device
  focus5_roster              — persisted top-5 Focus 5 roster snapshot
```

### Sync semantics per source

Every source is incremental, but the meaning of "incremental" depends on what the upstream API supports. The three patterns from [Sync model](#sync-model-in-plain-english) map cleanly onto the table below:

- **Vault notes** — *hash delta.* SHA-256 of raw file bytes stored in `vault_files.content_hash`. On re-ingest, unchanged-content files have their `last_modified` refreshed if the on-disk mtime moved forward (a "touch") but skip all parsing and embedding work — surfaced as `touched_files` in the ingest result. Changed-content files are deleted (CASCADE clears chunks/keywords/links) and re-inserted.
- **GitHub activity** — *window refetch.* Keyed by `(login, repo_full_name, scan_date)` with `ON CONFLICT REPLACE`. Each scan re-pulls the user's last ~30 days of events and overwrites *today's* row only; older days are left alone.
- **GitHub artifacts** — *hash/ID delta with window.* Keyed by `(repo_full_name, item_type, number)` for items; comments/commits/checks keyed by GitHub ID. `ON CONFLICT REPLACE` on every sync, with a `since_days` lookback to skip artifacts that haven't been touched in that window.
- **Embeddings** — *hash delta.* Chunks (vault) or documents (GitHub corpus) without a corresponding embeddings row get embedded. A model-version change recorded in `embedding_meta` / `github_embedding_meta` triggers a full re-embed of that corpus.
- **Calendar** — *window refetch.* Keyed by Google event ID with `INSERT OR REPLACE`. Re-sync overwrites existing events and adds new ones within the requested window (default 30d back / 7d forward; 365d on demand for backfill). No auto-deletion — events removed upstream stay in the local DB until manually pruned.
- **Sleuth reminders** — *full refetch + column-diff.* Keyed by `reminder_id`. Column-level diff against the stored row decides insert/update/unchanged; `first_seen_at` is set on insert and never overwritten; `last_seen_at` and `last_synced_at` refresh on every sync. Missing reminders are NOT deleted — terminal states (`completed`, `canceled`) remain as history.
- **Email (Gmail)** — *window refetch, count-bounded.* Keyed by Gmail `message_id` with upsert. Each run pulls the newest 100 messages matching the configured filter (default `in:inbox`, override via `gmail_query_filter` in `temp/rbos.config`). Phase 1 stores metadata + Gmail snippet only — no full body, no historical backfill, no auto-delete. See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).

---

## Query Layer

All consumers read from the same SQLite file. The query layer is source-agnostic.

**Read-side ownership model (Phase 3, Option C):**

| Surface | Role | Owner |
|---|---|---|
| `semantic_query()` MCP tool | Unified raw retrieval primitive | `semantic_index.query()` — owns source vocabulary, freshness, hybrid RRF |
| `chat_with_data()` | Citations-first interactive retrieval | `chat.py` — owns scope aliases (`work`/`code`/`all`), citation shaping; delegates retrieval to `semantic_index` |
| `ask()` | Broad mixed-context synthesis/orchestration | `querier.py` — owns project/calendar/temporal framing; not the canonical retrieval primitive |

```
SQLite @ $REBALANCE_DB
   │
   ├──▶ semantic_index.query()     ── unified raw retrieval primitive
   │    (MCP: semantic_query)          source vocab + hybrid RRF
   │         │
   │         ├──▶ chat_with_data() ── citations-first presentation layer
   │         │    (dashboard /api/chat)  scope aliases, citation shaping
   │         │
   │         └──▶ ask() (partial)  ── contributes to synthesis context
   │
   ├──▶ querier.py::ask()          ── broad orchestrator: gathers project,
   │    (MCP: ask, CLI: ask)           calendar, temporal + semantic signals;
   │                                   synthesizes via local Qwen3 (optional)
   │
   ├──▶ daily_report.py /          ── per-day / per-week calendar rollups
   │    weekly_report.py              with project classification
   │
   ├──▶ github_scan.py             ── per-project commit/PR/issue counts
   │    ::get_github_balance()        (surfaced as the github_balance MCP tool)
   │
   ├──▶ github_readiness.py /      ── release-state inference + issue↔PR
   │    github_reconciliation.py       close candidates
   │
   └──▶ mcp/server.py              ── exposes all of the above as MCP tools
                                       to Claude Code, Claude Desktop, etc.
```

`querier.py` is the synthesis orchestrator (not the retrieval primitive). A single `ask()` call:

1. **Gathers context** from all sources in parallel-ready functions:
   - `_gather_project_context()` — registry entries + repos map
   - `_gather_github_context()` — per-project activity summary (from `github_activity`)
   - `_gather_github_semantic_context()` — semantic recall over the GitHub corpus (`github_documents` + `github_embeddings`)
   - `_gather_vault_context()` — semantic search (embed query → ANN)
   - `_gather_vault_activity()` — recently modified files
   - `_gather_calendar_context()` — upcoming + recent events from `calendar_events`
   - `_gather_temporal_context()` — day-of-week / weekend / holiday framing for the prompt
   - `_gather_hiqs_context()` — the persisted **HiQS** ranked verdict (see below). A cheap
     cached read (`load_ranked_next_actions()`); it never recomputes. This is how Sleuth,
     Gmail, and Figma reach `ask()`: they are already in the one ranked bundle, so `ask()`
     surfaces them via the shared ranking rather than a per-source gatherer.

2. **Assembles a prompt** with all context formatted into labeled sections — including a
   `## HiQS — ranked next actions` section carrying each action's receipts. The ranking is
   also returned first-class on `QueryResult.hiqs`.

3. **Synthesizes** via local Qwen3 LLM (mlx-lm). Returns both synthesis and raw context.

### The Next Actions engine ("what to do next")

A distinct read-side subsystem in [src/rebalance/ingest/next_actions.py](src/rebalance/ingest/next_actions.py) — structurally one of the larger clusters in the codebase. It is **HiQS**: the single, unified work-signal pipeline — **one bundle spanning all six sources (GitHub, vault, Calendar, Sleuth/Slack, Gmail, Figma), one ranked verdict, read by every surface**. `ask()` and the dashboard's what's-next view read the *same* persisted ranking, so they cannot drift. It also drives the fixed vault file `Dashboards/What To Do Next.md`.

Pipeline (real symbols):

1. **`assemble_day_bundle()`** gathers the operator's own day signal across all six sources into an `OperatorBundle`, plus teammate deltas (`_gather_teammate_delta()`). Candidates are built by **`_operator_candidates()`, which WALKS the collector registry** — each source owns its candidate shape via the `candidates=` provider on its `Collector` (the same registry seam as `semantic_docs=`). A new work signal reaches the ranked verdict by registering a collector, never by editing this dispatch (GUIDING-PRINCIPLES Principle 3).
2. **`build_rank_prompt()`** formats the candidates; **`rank_next_actions()`** synthesizes the ranking. **Primary path = Gemini** (`get_gemini_api_key()` → `gemini-2.5-flash`); a deterministic local fallback (Qwen) keeps it working offline. `_parse_ranked_synthesis()` rejects placeholder echoes.
3. Output is a **`RankedNextActions`** (list of `RankedAction`), **persisted** to a cache table via `persist_ranked_next_actions()` and read back by `load_ranked_next_actions()`.
4. **`render_next_actions_markdown()`** writes the ranked list to the fixed vault file (single-writer, generated).
5. **Consumers:** the `web.py` what's-next route (`whatsnext_page()`) is the single WRITER (its `?refresh` path ranks + persists); `ask()` is a READER that exposes the persisted ranking as the first-class `QueryResult.hiqs` field. Neither re-ranks inline, so the two surfaces are structurally incapable of drifting.

### Two-Layer LLM Architecture

```
User question
  │
  ▼
ask() tool ──▶ Local Qwen3-0.6B (Layer 1)
  │              - Sees all raw context
  │              - Fast first-pass synthesis
  │              - Runs on-device via MLX
  │
  ▼
Returns to host agent (Layer 2)
  │              - Claude, Copilot, Gemini, etc.
  │              - Reviews synthesis + raw context
  │              - Fact-checks against raw data
  │              - Adapts, refines, presents to user
  │
  ▼
User sees final answer
```

**Why two layers?** The local model is fast and private — it never sends vault content to the cloud. But it's small (0.6B) and makes mistakes. The host agent is larger, smarter, and can fact-check against the raw context that's returned alongside the synthesis. The user gets speed + accuracy + privacy.

**`skip_synthesis=True`** bypasses Layer 1 entirely and returns raw context only. Use this when the host agent is capable enough to do its own synthesis (e.g., Claude).

---

## Invocation Modes

Four ways the pipeline runs:

1. **Interactive CLI** — `rebalance <subcommand>` via the Typer package under `src/rebalance/cli/`. Ad-hoc and one-shot workflows (`calendar-create-event`, `github-release-readiness`, `sleuth-sync --json`, `profile-sync`, `raw`, etc.). `rebalance` invoked with no arguments launches the live dashboard (mode 4). `rebalance raw [--minutes N] [--watch S] [--json]` is a calibration probe: 1 GitHub API request per invocation, classifies recent events as captured / pending / unwatched against the local pipeline state, used to verify that commits/PRs/issues are making it into rebalanceOS.

2. **Unattended scheduled syncs** — a launchd fleet of ten jobs. [SCHEDULER.md](SCHEDULER.md) is the policy table (single source of truth for labels, cadences, scopes, prerequisites, and outputs; enforced by `tests/test_scheduler_policy.py`). The six data/render jobs, conceptually:

   - **Daily all-scope sync** ([scripts/daily_sync.sh](scripts/daily_sync.sh) / [scripts/com.rebalance-os.daily-sync.plist.template](scripts/com.rebalance-os.daily-sync.plist.template)) at 06:30 local time, plus on boot/login if 06:30 was missed. Calls `refresh_index()` with no scope (the **default recipe**): all raw sources (`vault`, `github`, `calendar`, `sleuth`, `email`) followed by the derived/projection/export stages (`code`, `semantic`, `sync`). Note: `scope=["all"]` is *not* the same as the default recipe — after Phase 1b, `all` expands to raw sources only; the default no-scope path runs the full recipe including follow-on stages. Opt-in scopes (`figma`, `focus5`, `ask_self`) are never included automatically. Per-scope failures are captured in `errors` rather than aborting the run.
   - **Hourly obsidian vault embeddings refresh** ([scripts/obsidian_vault_embeddings.sh](scripts/obsidian_vault_embeddings.sh) / [scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template](scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template)) at HH:15 from 06:15 to 23:15. Calls `refresh_index(scope=["vault", "semantic"])` — keeps notes edited mid-day visible in **both** the dashboard/pulse (vault ingest) and **semantic search** (semantic projection stage). Vault ingest with no changes is ~0.02s; the lightweight BGE-Small (384-dim, ~20MB) semantic stage embeds rows where content changed in milliseconds.
   - **Hourly pulse publish** ([scripts/pulse_sync.sh](scripts/pulse_sync.sh) / [scripts/com.rebalance-os.pulse-sync.plist.template](scripts/com.rebalance-os.pulse-sync.plist.template)) on the hour, 06:00 to 23:00. Renders the operator pulse markdown and pushes it to the configured private repo, but only when the rendered content actually changed since the previous run.
   - **30-minute pulse-web refresh** ([scripts/pulse_web_sync.sh](scripts/pulse_web_sync.sh) / [scripts/com.rebalance-os.pulse-web-sync.plist.template](scripts/com.rebalance-os.pulse-web-sync.plist.template)) every 30 minutes from 06:00 to 23:30. Calls [scripts/pulse_web.py](scripts/pulse_web.py) to regenerate the local `web/pulse.html` mirror of the dashboard. Atomic via tmp+replace (a crashed run leaves the previous HTML intact). No network, no git push — separate from the markdown→private-repo flow above.
   - **Hourly GitHub sync** ([scripts/github_sync.sh](scripts/github_sync.sh) / [scripts/com.rebalance-os.github-sync.plist.template](scripts/com.rebalance-os.github-sync.plist.template)) — a narrower github-only refresh independent of the daily full sync, for environments that want fresher GitHub data without paying the full multi-source cost.
   - **Pulse server (long-running, not scheduled)** ([scripts/pulse_server.sh](scripts/pulse_server.sh) / [scripts/com.rebalance-os.pulse-server.plist.template](scripts/com.rebalance-os.pulse-server.plist.template)) — a FastAPI/uvicorn server on `127.0.0.1:8767` with `RunAtLoad` + `KeepAlive` (autostart at login, restart on crash, `ThrottleInterval=30s`). Adds an interactive layer (real Refresh button + filter) on top of the static `web/pulse.html` the pulse-web job regenerates, **and is the always-on JSON backend for the macOS Focus 5 Float app** ([macOS/Apps/Focus5Float](macOS/Apps/Focus5Float)) — it serves `/focus-5.json` (roster), `/focus-5/goals`, and `/focus-5/note` so the app works without a separate `rebalance serve` on `:8787`. Loopback bind is enforced in [scripts/pulse_server.py](scripts/pulse_server.py). Unlike the five scheduled jobs above, it runs continuously rather than firing on a calendar interval.

     **Drift gotcha (has bitten the Focus 5 app twice):** [scripts/pulse_server.py](scripts/pulse_server.py) does *not* mount `rebalance.web`'s app — it hand-re-declares a chosen *subset* of its routes by importing the renderers. Two consequences: (1) a route added to `web.py` is invisible on `:8767` until a matching wrapper is added to `pulse_server.py` (this is how `/focus-5.json` was missed); (2) because it's a `KeepAlive` daemon, any route change requires `launchctl kickstart -k gui/$UID/com.rebalance-os.pulse-server` to take effect — a long-running process keeps serving its old route table otherwise (this is how a freshly-added `/focus-5/goals` still 404'd).

   The remaining four jobs (health-check hourly, health-check-triage 3×/day, pulse-warning-watch every 15 min, obsidian-rollover at midnight) plus **daily-synthesis** at 18:20 are operational/maintenance agents — see [SCHEDULER.md](SCHEDULER.md). The **daily-synthesis** job ([utils/daily_synthesis.sh](utils/daily_synthesis.sh) / [scripts/com.rebalance-os.daily-synthesis.plist.template](scripts/com.rebalance-os.daily-synthesis.plist.template), GH-74) does two syntheses in one process, in order: first a Gemini daily-activity summary from the structured `collect_pulse_snapshot()` output, then a Gemini synthesis of multi-device git commit logs aggregated via `experimental/git-pulse/view.sh --today`. Each lands in its own idempotent sentinel-bracketed block at the bottom of the vault's `0. Today's Notes.md`, pulse block first. (It replaces two formerly separate jobs, obsidian-daily-sync at 18:20 and git-pulse-daily-synthesis at 18:30, which existed as two launchd jobs only so the second could fire after the first — see `utils/daily_synthesis.py`'s module docstring.) Both syntheses use Gemini-or-skip logic (no Qwen fallback) and the merged job carries one late-run guard to prevent colliding with the 00:00 rollover.

   Wrapper scripts source [scripts/lib/scheduler_common.sh](scripts/lib/scheduler_common.sh) for env bootstrap (repo root, venv python, `PYTHONPATH`), per-day logs under `temp/logs/`, job-lifecycle events into `auth_activity.jsonl`, and log retention. Installers source [scripts/lib/install_common.sh](scripts/lib/install_common.sh) for one normalized flow: always-unload, render the `.plist.template` (`{{REBALANCE_DIR}}`, `{{PYTHON}}`, `{{HOME}}`), `plutil -lint`, load, poll-verify registration. The rendered plists in `~/Library/LaunchAgents/` are gitignored — the templates are the only checked-in form, so a clone on any machine installs cleanly with no per-user editing.

3. **MCP tool handlers** — [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py) registers the tools; [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) remains as the backward-compatibility shim for older launch commands. Host agents (Claude Code / Claude Desktop) call these on demand. `REBALANCE_DB` env var resolves the shared DB path.

4. **Live dashboard** — [scripts/dashboard.py](scripts/dashboard.py) is a Rich Live monitor that polls the local SQLite every 2 seconds (cheap; no network) and runs `refresh_index(scope=["github"])` in a background thread every 10 minutes so the underlying data actually changes. Launch via `rebalance` (no args) or `rebalance dashboard`. Press `r` to trigger an immediate GitHub refresh, `q` (or Ctrl+C) to quit. Theming and cadence are env-var controlled (`PULSE_INVERSE`, `PULSE_TICK`, `PULSE_AUTO_MIN`, `REBALANCE_TZ`). The dashboard is intentionally read-only against the same DB the MCP server and the launchd jobs write to.

---

## MCP Tool Surface

Tools are registered in [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py)::`create_server()`. [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) is a backward-compatibility shim so older launch commands still work. All tools share the same `database_path` resolved at server startup from `REBALANCE_DB`.

| Category | Tool | Purpose |
|----------|------|---------|
| Query | `ask` | Natural language query across all sources (with optional local LLM synthesis) |
| Query | `search_vault` | Vault keyword search (TF-IDF) |
| Query | `github_balance` | Per-project GitHub activity summary |
| Query | `github_release_readiness` | Infer milestone/release readiness from the local GitHub corpus |
| Query | `github_close_candidates` | Suggest open issues that likely map to merged PRs |
| Query | `semantic_query` | Unified vector search across indexed sources (single ranked result set; filter with `sources`) |
| Diagnostics | `index_status` | Snapshot of every source + semantic index freshness (read-only) |
| Diagnostics | `refresh_index` | Orchestrated refresh of the local knowledge base (single entry point) |
| Diagnostics | `list_watched_repos` | Show merged set of repos being monitored (project registry ∪ activity − ignored) |
| Diagnostics | `diagnose_repo` | Walk the watched-repos + sync funnel for a single repo (optionally a `sha` or `pr`) and explain coverage + freshness gaps; opt-in `live=True` distinguishes "we never synced" from "PAT can't see it" |
| Registry | `list_projects` | Query project registry |
| Onboarding | `onboarding_status` | Check setup completion |
| Onboarding | `setup_github_token` | Validate and store GitHub PAT |
| Onboarding | `run_preflight` | Discover project candidates (read-only) |
| Onboarding | `confirm_projects` | Write registry and sync |
| Onboarding | `ingest_gmail_messages` | Agent-pushed Gmail ingest path for installs using `gmail_ingest_method=mcp` |
| Calendar | `create_calendar_event` | Create a Google Calendar event via local OAuth |
| Calendar | `review_timesheet` | Surface unclassified calendar events that need a project decision |
| Calendar | `classify_event` | Persist an include/exclude/project classification for an event |
| Calendar | `snap_calendar_edges` | Detect and (optionally) fix slightly overlapping events |
| Sync | `sleuth_sync_reminders` | Pull Slack reminders from the Sleuth Web API and upsert to SQLite |
| Sync | `publish_pulse` | Render today+yesterday activity to markdown and push to private pulse repo |
| Hygiene | `audit_modules` | Run [scripts/audit_modules.py](scripts/audit_modules.py) and return the structured JSON result. Verifies that ingest collectors / render modules / scheduled-job infrastructure are documented in ARCHITECTURE.md and CHANGELOG.md, and that recent commits' file changes appear in the latest CHANGELOG version section. Supports `init=True` to snapshot the baseline lockfile and `include_uncommitted=True` for a pre-commit working-tree preview |

Tool specs (params, returns, dependencies): see [MCP.md](MCP.md).

---

## Module Map

```
src/rebalance/
  __init__.py              — package version
  __main__.py              — CLI entry point
  cli/                     — Typer command package split by domain
  mcp/                     — FastMCP server + tool modules
  mcp_server.py            — backward-compatibility shim to rebalance.mcp.server
  paths.py                 — centralized path resolver. `resolve_database_path()` and
                              `resolve_secret_path()` walk a layered chain (explicit
                              flag → env var → canonical app-data path → user
                              config → cwd walk-up for project marker). Single
                              source of truth for "where is the DB / secrets dir?"
                              `resolve_project_root(Path(__file__))` (walk-up) is the
                              stable repo-root resolver used throughout the codebase —
                              replaces all `parents[N]` hacks. `resolve_oauth_token_path(service)`
                              returns the canonical launchd-reachable token path for
                              Google OAuth services. Configure user defaults via
                              `rebalance config set-default-database` and `set-secrets-dir`.
  web.py                   — FastAPI local dashboard/web surfaces (`/`, `/focus-5`, `/auth-log`, etc.)
  ingest/health_log.py     — doctor check TRANSITIONS into the unified system log (GH-101)
  doctor.py                — installation health checks; backs `rebalance doctor`
  ingest/
    config.py              — secrets storage (temp/rbos.config)
    registry.py            — project registry sync (Markdown ↔ YAML ↔ SQLite);
                              read_registry (pure read) vs load_registry (write-path)
    preflight.py           — onboarding discovery (read-only, provenance-stamped)
                              + confirmation — the only curated registry write path
    lifecycle.py           — Phase 5/6 lifecycle contract: setup stage map with
                              done/now/next/blocked/skipped statuses, executor
                              hints, and remediation (backs onboarding_status and
                              the /welcome skill), plus the project-lifecycle
                              ownership table (write semantics per stage —
                              discovery read_only, confirmation gated, inference
                              machine-owned, prioritization read-time overlay)
    local_repos.py         — local checkout discovery (Phase 6.1): scan
                              local_repo_roots for git checkouts, GitHub identity
                              from origin, unpushed-commit counts; feeds
                              provenance=local-scan candidates + the doctor's
                              unpushed-work check
    github_scan.py         — GitHub Events API collector + per-project balance query
    github_knowledge.py    — per-repo artifact sync (issues/PRs/comments/commits/checks) + embedding
    github_watch.py        — watched/external repo reconciliation and repo-watch logic
    github_readiness.py    — release-readiness inference over the local GitHub corpus (read-only)
    github_reconciliation.py — issue ↔ PR close-candidate inference (read-only)
    db/                    — shared DB connection, schema, migrations, sqlite-vec loading
    md_parser.py           — pure markdown parsing (frontmatter, wikilinks, tags, chunking)
    note_ingester.py       — vault walker, delta detection, TF-IDF keywords
    embedder.py            — mlx-embeddings batch embed + ANN query
    semantic_index.py      — unified semantic index: backfill, embed, and query across
                              vault + GitHub + email, plus registry-provider sources
                              such as Figma (semantic_documents / semantic_embeddings)
    index_ops.py           — single entry point for refresh_index() and index_status();
                              orchestrates the full ingest pipeline so agents don't
                              need to know individual CLI command ordering
    calendar.py            — Google Calendar API collector + SQLite persistence
    calendar_config.py     — OAuth token storage, classification rules, review-decision persistence
    calendar_helpers.py    — duration/math utilities consumed by calendar tools
    calendar_snap.py       — edge-snapping logic for slightly overlapping calendar events
    sleuth_reminders.py    — Sleuth Web API collector (Bearer auth, urllib) + upsert
    gmail.py               — Gmail collector / MCP push-ingest write path into email_messages
    figma.py               — Figma comments collector + registry-provider semantic_docs
    ask_self_scan.py       — device-local ask_self index inventory collector
    focus5_scan.py         — Focus 5 repo-signal scan + roster builder
    slack_users.py         — Slack user-id → friendly-name lookup, file-mtime cached;
                              feeds the dashboard sleuth panel and the pulse markdown
    diagnose.py            — repo-level diagnostic that walks the watched-repos +
                              sync funnel for one repo (optionally sha/PR) — backs
                              the diagnose_repo MCP tool
    profile_sync.py        — daily-sync log parser that surfaces per-repo GitHub
                              timings; backs the rebalance profile-sync subcommand
    pulse.py               — pulse markdown renderer; backs publish_pulse MCP tool
    agent_tags.py          — source-tagging for pulse rows (claude-cloud, codex-cloud,
                              lovable, local-vscode, human)
    project_classifier.py  — calendar event → project matcher for timesheet reports
    project_inference.py   — project inference from note titles / calendar summaries
    note_builder.py        — dashboard markdown renderer / write-back for the vault note
    audit.py               — structured audit logging (append_audit_entry)
    querier.py             — multi-source context gathering + local LLM synthesis

scripts/                   — Operator entry points (not part of the importable package)
  dashboard.py             — Rich Live terminal dashboard (mode 4 above)
  pulse_web.py             — render module: regenerates web/pulse.html (the local
                              browser mirror of the dashboard) from the same SQLite
                              knowledge base; atomic via tmp+replace; supports --watch
  _bootstrap.py            — single sys.path shim for directly-run scripts (src/ + scripts/)
  lib/scheduler_common.sh  — shared launchd job runtime: env bootstrap, dated logs,
                              job-lifecycle events, retention (sourced by *_sync.sh)
  lib/install_common.sh    — shared installer flow: always-unload, render template,
                              plutil -lint, load, poll-verify (sourced by install_*.sh)
  daily_sync.sh            — daily_sync launchd entry (mode 2)
  vault_sync.sh            — hourly vault-only launchd entry (mode 2)
  pulse_sync.sh            — hourly pulse-publish (markdown→private repo) launchd entry (mode 2)
  pulse_web_sync.sh        — 30-minute pulse-web (web/pulse.html) launchd entry (mode 2)
  github_sync.sh           — github-only launchd entry (mode 2)
  install_*.sh             — one installer per launchd job (see SCHEDULER.md for the
                              job ↔ installer table; all delegate to lib/install_common.sh)
  setup_calendar_oauth.py  — interactive OAuth consent flow for Google Calendar
  build_extension.py       — native extension builder
  ask-self-ingest.sh       — self-ingest shell wrapper (portable mode, requires ASK_SELF_PATH)
  ask-self-query.sh        — self-query shell wrapper (portable mode, requires ASK_SELF_PATH)
  audit_modules.py         — repository hygiene audit (Approach A): verifies ingest
                              collectors / render modules / scheduled-job infrastructure
                              are documented in ARCHITECTURE.md + CHANGELOG.md; supports a
                              baseline lockfile (audit_modules.lock), recent-commit coverage
                              against the live CHANGELOG version section, and a pre-commit
                              working-tree preview (--include-uncommitted). JSON output for
                              orchestrating agents; also exposed as the audit_modules MCP tool
```

---

## License

Copyright 2025-2026 Hypercart DBA Neochrome, Inc.

rebalance is dual-licensed, matching the rest of the HiQS suite. **AGPL-3.0-only** is the
default and covers nearly every use — see [`LICENSE`](LICENSE). A commercial license is
available for use that AGPL-3.0 does not fit; see [`LICENSE-COMMERCIAL.md`](LICENSE-COMMERCIAL.md).


## Opt-in fleet Pulse delivery (GH-282)

Rebalance producers → device-owned files/exact local commits → existing Git Pulse collector →
private Git remote → each Mac's checkout/SQLite replica → combined human-readable views.
No Mac is a permanent hub. `git_ops.fleet_settings` validates the configured collector identity,
checkout and sync subdirectory. Generated live pulse, daily synthesis and digests use
`devices/<id>/`; calendar/email keep `sync/<source>/<id>.json`. Historical shared files are retained
for rollback and no longer written in fleet mode. `read_latest_snapshot` chooses validated payloads
on read; `pulse.fleet_view` derives delivered pages and is returned by fleet publishing through the
existing CLI/MCP result. These are readers of existing data, not new stores or writer daemons.

CLIO's capture UUID is independent of the friendly collector ID. Its canonical helper exports only
its owner snapshot to `devices/<UUID>/clio.jsonl`; the collector validates it before atomic publication.
Reconcile imports committed blobs into private SQLite without re-exporting foreign origins. Existing
semantic indexing, publishers and readonly XYZ ledger integrations retain their contracts. The same
Obsidian filename/header and five-minute renderer remain, backed by full history on every installed
Mac. Live fleet qualification remains tracked in the canonical GH-282 plan.
# SOP — Standard Operating Procedure

Do not store any credentials or secrets in this file, other repo files, or any PII in public facing GH issues. The same rule covers machine-specific absolute paths (e.g. a deploy runtime folder's real location) — keep those in your own gitignored `temp/RUNTIME.md`, never in a tracked file. See the pattern in `AGENTS.md` § "Deploy runtime folder".

This document codifies how work in this repo gets **evidenced**. It is written for
whoever picks up the next task, human or model, and it is binding on both.

---

## 1. The rule

> **Verified beats plausible. A claim whose evidence is unpublished is an assertion.**

If you state that something was measured — in a GitHub issue, a PR body, a commit
message, `ROADMAP.md`, a code comment, or a reply to the operator — the measurement
must be retained in [`TESTS-RESULTS/`](TESTS-RESULTS) where a reader can check it
without access to your machine.

This exists because it has already failed here. A retrieval change was tested on 5
queries with no ground truth, the result looked negative, the improvement was
reverted, and the conclusion was reported as settled. It was noise. Re-run properly
(39 queries, hand-established targets, paired significance test) the same change won
decisively — 14 improved, 0 regressed, p=0.0137 — and the earlier call had been
suppressing a real fix for weeks. See
[`TESTS-RESULTS/2026-08-20+GH-81/`](TESTS-RESULTS/2026-08-20+GH-81).

The lesson is not "test more." It is: **a small unverifiable test is worse than no
test**, because it manufactures false confidence and then gets cited.

## 2. When a campaign is required

Run one — and publish it — before any of these:

- **Choosing or replacing a model, library, or algorithm** where the claim is that one performs better than another.
- **Reverting or rejecting a change on empirical grounds.** "I tried it, it didn't help" is a claim and needs the same evidence as "I tried it, it helped." This is the specific failure above.
- **Any performance, retrieval-quality, or accuracy number** that will appear in an issue, PR, or doc.
- **Declaring a system healthy or a defect fixed** where the proof is behavioural rather than a passing unit test.

Not required for: ordinary code changes covered by the test suite, refactors with no
behavioural claim, or documentation.

**If it is not worth a campaign, it is not worth an empirical claim.** Say "not
measured" instead. That is a legitimate and useful thing to write.

## 3. How to run one

### 3.1 Write the protocol first, and freeze it

Before generating a single number, write down: the question, what is being compared,
the dataset, the metrics, and — critically — **the decision rule**: what result would
lead to which action, including the results that would embarrass the current design.

Put it in `PROJECT/2-WORKING/`. A decision rule written after seeing results is not a
decision rule; it is a rationalisation.

### 3.2 Establish ground truth by hand

For retrieval, ranking, or classification work, the correct answer must be determined
by a person **reading the artifact** — not by another model, and not by the system
under test. Discard any item whose correct answer cannot be established; do not guess
it. Record how many you discarded.

Watch for near-duplicates. If several items would legitimately satisfy the same query,
single-target scoring is invalid and will silently penalise every system equally
while looking like a real measurement.

### 3.3 Get the protocol reviewed before running it

Use `/relay-xyz` (or an equivalent independent review) on the **protocol**, not just
the results. Review after the fact can only rationalise; review before can still
change the experiment.

On GH-81 it changed the experiment twice, and one of those changes is why the
headline finding was detectable at all — the original significance rule would have
returned "no measurable difference, keep the incumbent" almost regardless of the
data. Transcripts: [`qa/`](TESTS-RESULTS/2026-08-20+GH-81/qa).

### 3.4 Include a dumb baseline

Always score the boring option — keyword search, the previous version, a constant, a
coin flip. Without it you cannot tell "our system is good" from "this task is easy."
On GH-81 the shipped configuration scored **below plain SQLite full-text search**,
which is not a fact any amount of comparing sophisticated options to each other would
have surfaced.

### 3.5 Use a paired test when systems answer the same inputs

Comparing independent per-system confidence intervals throws away the pairing and
buries real effects under between-item difficulty. Use a paired test (Wilcoxon
signed-rank for bounded/tied metrics), correct for multiple comparisons (Holm), and
report **effect size alongside p** — a significant tiny effect is a real and
reportable outcome.

Report "no significant difference" plainly when that is the answer. It is a result.

### 3.6 Prove the instrument constrains

Before trusting a new test, **make it fail on purpose.** Revert the fix and confirm
the test goes red. A test that passes against broken code measures nothing, and a
green suite full of them is worse than no suite because it is trusted.

### 3.7 Publish

Follow [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md): campaign folder named
`YYYY-MM-DD+GH-<issue>`, `SUMMARY.md`, the primitive `.jsonl`, the scripts as run,
the QA transcripts verbatim, the raw console output.

Every aggregate in the summary must be recomputable from the primitive records. If it
isn't, the primitive is incomplete or the number is unsupported.

## 4. Reporting

### 4.1 Threats to validity are mandatory

Every `SUMMARY.md` ends with what would make the result wrong: sample size, sampling
bias, lack of blinding, deviations from protocol, what was *not* measured. Write them
even when — especially when — the result came out the way you hoped.

State deviations explicitly. On GH-81, one model ran at a reduced context window
because the full one exhausted GPU memory; that is recorded, along with the check
showing it did not explain the outcome.

### 4.2 Retract loudly

If a campaign overturns an earlier published conclusion, **say so in the same place
the original was published**, link both, and state what was wrong with the first
attempt. Do not quietly supersede it. Someone is relying on the old claim.

### 4.3 Do not overstate scope

Say what was measured, not what it implies. GH-81 measured the vector retriever in
isolation, while production fuses vector and lexical search — so "no model beat
keyword search" was a component-level result and would have been badly misleading
stated as a system-level one. That correction is in the summary because it was caught
before publication; catching it after would have meant a retraction under §4.2.

## 5. Naming things precisely

Ambiguous names cost real time and cause real errors. When identifying a model,
library, or version, use the **full identifier**, and verify it against the artifact
rather than repeating it from memory or a doc.

- Not "BGE small" → **`BAAI/bge-small-en-v1.5`**
- Not "the embedding model" → the full repo ID and dimension

Model families use several independent axes at once — family, size tier, language,
and release version — and collapsing any of them creates questions like "is this the
small one or the v1.5 one?" when the answer is *both*. See
[`docs/EMBEDDING-MODELS.md`](docs/EMBEDDING-MODELS.md) for this repo's naming
conventions and the current model's exact identity.

Verify from ground truth: the code constant, the recorded run metadata, and the
downloaded artifact should agree. Where they disagree, say which one governs.

## 6. The same thing collected twice is a defect, not a rounding error

> **One real-world entity must contribute to a metric exactly once. If an alias, a rename,
> a mirror, a fork, or a casing variant causes it to be counted twice, that is a defect —
> catch it, fix the read path, and remove the duplicate rows from the store.**

This is the source of truth for the rule. `AGENTS.md` and `GUIDING-PRINCIPLES.md` point here.

### Why it has its own section

A GitHub org rename put the same repository in `github_activity` under two spellings on the
same `scan_date`. Every read path that aggregated those rows **summed** them, so one day's
48 commits and 13 PRs were reported as 86 and 26. Nothing failed, no error was raised, and
the number was simply wrong in every ranking built on it — `top_active_repos`, the
`github_balance` MCP tool, Focus 5, the dashboard, the morning brief.

The test written to catch exactly this inserted the duplicate row with **every metric set to
zero**, so summing it changed nothing and the test passed. It could never have failed. That
is the part worth remembering: the duplicate was known about, a guard was written for it, and
the guard was inert.

### The rule, concretely

The three controls are **detect, reconcile, repair**. All three are required and none substitutes
for another: detection is the only proactive step, reconciliation is what stops a wrong number
being published, and repair is what protects every consumer that does not use the canonical read
path. They are a set, not a sequence — repair the store before or after fixing reads, but do both.

1. **Read the schema to decide the semantics — then do not expect it to enforce them.** If a table
   carries a snapshot — `UNIQUE(...) ON CONFLICT REPLACE` is the tell — then **one row wins**
   (latest `scanned_at`), and summing across aliases is wrong. If rows are genuinely disjoint
   increments, summing is right. The schema tells you which, and that is all it does: a uniqueness
   key built on a **mutable** identifier does not prevent duplicates, it *creates* them. In
   `github_activity` the key includes `repo_full_name`, so an org rename produced a new key, both
   spellings coexisted, and the constraint never fired. That is the whole origin of this defect.
2. **Reconcile at read.** Every aggregate over an entity that can have aliases maps to a canonical
   identity *before* grouping, never after, and never sums across aliases of one entity.
3. **Repair the store too.** Reconciling reads leaves wrong rows in the database for any consumer
   that does not use the canonical path — MCP tools, dashboards, exports. Re-key the stale rows to
   the canonical identity and drop superseded snapshots.
4. **Order matters when de-duplicating.** On a table declared `ON CONFLICT REPLACE`, renaming
   a row onto an existing key **silently destroys the row already there**. Delete the
   superseded rows *first*, then rename. Back up before either.
5. **Never let a de-dup test assert on zeros.** The duplicate fixture must carry the same
   non-zero values as the row it duplicates, and the test must be witnessed failing before the
   fix. A de-dup test that has never gone red is not evidence.
6. **Purge the metric, not just the source.** A number already published from doubled data is
   wrong and gets cited. Correct it, or say plainly that it was not recomputed.

### What this applies to

Any identity with more than one spelling: renamed GitHub orgs and repos, mirrors, forks,
casing variants, email aliases, Slack user IDs versus display names, project aliases in
`project_priority_rules`, and vault note paths that moved. It is not a GitHub-specific rule.

### Enforcement

`tests/test_alias_dedup_invariant.py` pins the invariant with synthetic fixtures and no
dependency on any operator's configuration or org names. It is a deterministic suite test, not
a check against live data.

---

**Related:** [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md) (structure and
conventions) · [`AGENTS.md`](AGENTS.md) (working agreements) ·
[`ROUTER.md`](ROUTER.md) (prior-art checks before building)

## 7. A merge is not a deploy

> **Scheduled jobs run from the runtime folder, not from the branch you merged. Until
> someone pulls, the fix does not exist.**

The fleet (`launchd`) is pinned to one checkout — the path in
`~/.config/rebalance/runtime-root`, shown as `Target root` by `scripts/stack.sh status`
— and that checkout is updated deliberately, by hand, with

```
git -C "$(cat ~/.config/rebalance/runtime-root)" pull --ff-only origin development
```

This exists because it has already failed here. On 2026-09-04 eight PRs merged to
`development` in one day, including the digest filter (#163) and the compressor-gate
fix (#171). The runtime had last been pulled on 2026-09-02. Both 13:05 and 17:05
digests went to Slack still leading with the repo #163 removes, and
`obsidian-vault-embeddings` kept failing on the gate #171 relaxes — 51 commits of
merged, CI-green, verifiably working code, none of it running. Nothing reported the
gap; it was found by reading the digest by hand.

**The rule, concretely**

- After merging to `development`, run `bash scripts/stack.sh drift`. It prints how many
  commits the runtime trails and the exact pull command. Exit 1 means behind.
- `stack.sh status` prints the same line at the bottom, so the check rides along with
  the tool ROUTER.md already names as ground truth.
- The `.githooks/post-merge` hook prints it after every `git pull` in your dev
  checkout. Enable once per clone: `git config core.hooksPath .githooks`. It is a
  reminder, never a gate — it cannot fail a merge.
- A deploy is done when `stack.sh drift` says `up to date`, not when the PR says
  `Merged`. Say which in the PR or issue if it matters — "merged" and "deployed" are
  different claims (§ 5).

**Enforcement.** `tests/test_runtime_drift.py` pins the check with two throwaway
repositories and no dependency on any operator's machine — including that it still
measures the runtime when run from inside a git hook, where `GIT_DIR` points elsewhere.

## 8. Which GitHub repos get monitored

> **Authorship monitors a repo. Participation does not. There is no watchlist file.**

Settled on 2026-09-06 under GH-158. The monitored set is recomputed from scratch on
every refresh by `get_watched_repos()` in `src/rebalance/ingest/index_ops.py`:

```
watched = (project ∪ external ∪ activity ∪ pushed) − ignored
```

**A repo is monitored when any ONE of these holds:**

1. **You listed it.** It is in `repos:` on an active project in the project registry.
   This is the only manual list, and it never ages out.
2. **You flagged it external.** A project marked `external: true` is monitored for
   *everyone's* activity, not just yours. Never ages out.
3. **You authored in it recently** — a commit, a push, or a pull request opened or
   merged. One event is enough. "Recently" means the repo appeared in a GitHub scan
   run in the last 14 days; each scan aggregates a 30-day event window, so a repo can
   stay eligible up to roughly 44 days after your last contribution. Expiry is by scan
   date, not contribution date.
4. **Someone pushed to it in the last 14 days** and you can see it, per GitHub's own
   pushed-repos list. This path is *not* authorship-checked: a collaborator's push to a
   private org repo you have access to monitors it too. It exists because the events
   feed drops collaborator pushes and caps at 300 events. If that catches a repo you do
   not want, ignore it (below); tightening this path is a separate decision.

**These do NOT monitor a repo:** starring or watching it, forking it (your first push
to the fork does), opening an issue, commenting on an issue, or reviewing a pull
request. Those are participation, and monitoring a stranger's repo because you left a
comment ingests its entire history and reports other people's work as yours
(`PARKED/2026-09-03-digest-repo-contamination.md`). Editing a project board is not in
GitHub's events feed at all and is not a signal.

**A repo stops being monitored when:**

- it is explicitly ignored — `rebalance config add-github-ignored-repo <owner/repo>`.
  Ignore always wins, over every rule above; or
- it ages out — if activity or a push was its only reason to be monitored, it leaves
  the set silently once no scan in the last 14 days has carried it (see rule 3 for why
  that is later than 14 days after your last commit). There is no other drop mechanism,
  and none is planned. Note this does not drop a repo that has been promoted to a
  project or listed in `repos:` — those stay until you remove or ignore them.

**A repo becomes a project on its own** once 3 or more commits to it (all-time in
collected data, threshold configurable) are attributed to you or to a configured
cloud-agent author (`CLOUD_AGENT_AUTHORS` in `pulse.py`). The promoted row is
machine-owned and never overwrites a curated project of the same name, and from then
on the repo is monitored through the registry, so it no longer ages out. See
"Auto-promotion" in `AGENTS.md`.

**Enforcement.** `tests/test_watched_repos.py::test_participation_only_does_not_auto_watch_repo`
pins that a repo with only issues, comments and reviews stays out while a repo with a
single pull request comes in.


## GH-282 — fleet delivery deployment and lessons

Fleet mode reuses the existing collector, common publication lock and schedules. It does not
select a central Mac. Every participating Mac owns its generated paths and full-history SQLite
replica; remote delivery is eventual on the existing Git Pulse cadence. The Obsidian note is a
combined human-readable projection and is never the capture/control plane.

1. Verify canonical collector identity before opting in: configured `device_id` must be present,
   lower-case and safe, with no pending legacy migration. Inventory local writers, including manual
   CLI/MCP callers, and verify the private checkout is clean and its pending commits are accounted for.
2. Back up the declared runtime revision, configs, copied collector executable, canonical CLIO
   helper, private DB (SQLite backup API), original note and personal header. Verify hashes and DB
   integrity. Keep machine paths and original private content in ignored local deployment receipts.
3. Fast-forward the stable runtime to landed `development`. Update the already installed collector
   copy if it is not a symlink. Keep launchd labels and intervals unchanged; refresh existing long-running
   runtime processes as needed. Do not activate 3-Eyes or disabled jobs as part of this deployment.
4. In collector config set `fleet_mode=true`, the existing canonical `device_id`, and
   `fleet_sync_subdir` matching Rebalance's `sync_subdir`. Set Rebalance `pulse_fleet_enabled=true`
   and `pulse_device_id` to that same ID. Python validates literal collector settings on every publish.
   Fleet mode overrides caller `push=True` and `PULSE_PUSH`; a successful local commit is `queued`,
   never labelled remotely pushed. Shared historical files/pointers are retained but not updated.
5. For CLIO, install the separately reviewed canonical helper, configure its fleet inventory, and set
   explicit `clio_store_path`, `clio_database`, `clio_owner_uuid` in collector config. Export only
   `devices/<CLIO-UUID>/clio.jsonl`; imported origins stay in private SQLite, outside all staged paths.
   The pre-existing `snapshots/` relay remains separate. Never derive a CLIO UUID from a hostname.
6. Run actual local rendering, collector delivery and canonical reconcile; verify upstream objects,
   DB integrity/history preservation, header and the same note path. A fake fixture is useful for
   contract proof but does not qualify an actual offline/rejoin or all-Mac pilot. Other Macs remain
   disabled until their individual installation/source-coverage and archive-capacity checks pass.
7. Rollback disables Python fleet mode and restores the backed-up collector/config/runtime only
   once the private checkout is clean and no fleet commits are unpushed. Otherwise keep the new
   collector and preserved pending history until reconciled; never reset, stash or discard it.

The collector staggers once before its inherited lock. Network operations have a 900-second total
budget and per-call 120-second default timeout, with up to five extra seconds for termination;
local scanning/export overhead adds to lock time. Busy producers skip with 75 and retry on their
existing schedule. They cannot record an attempt while another process holds the lock; age of the
last delivered status remains the signal. Failed network delivery cannot report its failure remotely
until a later delivery succeeds. Fleet health adds bounded local Git reads to the legacy pure-YAML
reader; missing or unverifiable upstream evidence is conservatively not publishing. Experimental
health-check reuses that canonical reader when installed, and otherwise warns for opted-in devices.

Lessons: a merged PR is not a deployed runtime; a copied collector is a second deployment surface;
Python hostname IDs and collector IDs were different; an inherited-lock re-exec must not repeat the
stagger inside the lock. Empty repository inventories must work under macOS Bash 3.2. Preserve
pending commits and use exact owner paths; a heartbeat alone never attests application output.

Fleet render aging uses a named 10-hour bound: 7 hours of scheduled overnight pause, one hour
for fall-back DST, the producer's half-hour budget, one collector interval and half-hour network/
stagger grace. Explicit failed attempts and queued output are visible immediately; a silently
stopped renderer can take that long to age out. Doctor/health detail distinguishes queued, failed
(exit N), unavailable proof and old delivered output. A CLIO export/validation fault deliberately
stops that Mac's collector before a new heartbeat; preserve the previous snapshot, inspect the
backup/DB and cumulative guard, then rerun the existing collector after repair.

A successful local render waiting for the next collector delivery intentionally reports a temporary
doctor WARN (`queued, awaiting collector`). Warning-level health triage may report it during that
window. Observe the installed collector phase across three real intervals before changing alert
policy; this warning does not mean the render failed or its queued commit was lost.

Studio activation lessons: bootstrap all known preserved CLIO origins once with explicit origin
selection, then configure normal exports for the local owner only. Imported records must never
be echoed by routine exports. The first upgraded collector heartbeat advertises fleet mode; an
old unmarked heartbeat still uses legacy health until that delivery. Verify queue-to-delivered
health after this first check-in, not before it. Test missing/mismatched settings as well as valid
configuration: a refusal must return a structured error or doctor configuration failure, with no
Git writes. Briefly unload only loaded local delivery jobs, then restore the identical plists.
Keep capture and same-note export running, and verify preserved record payloads as well as counts.

### CLIO fleet consumer qualification

The canonical CLIO SQLite remains authoritative; the existing configured compatibility export contains full history across known origins. Verify the resolved source before adding a second reader. Raw history totals differ from filtered consumer totals: reconcile eligible projection keys and canonical source references, including multiple origins sharing one filtered prompt. JSONL records are separated by LF, not Unicode line separators. Preserve existing consumer keys and attach provenance additively. Use the existing semantic maintenance facade for selected, nonembedding projection; neither an empty result nor a guard skip proves consumer readiness. Keep scheduled memory deferral separate from delivery failure and never relax the whole stack to obtain a green receipt.

Studio follow-through (0.97.2): source and package metadata can disagree in an editable install; confirm both after deployment. Restart only existing owned long-running consumers so they import the landed code. A manual named-source refresh proves the local consumer, not the guarded schedule. Read-only XYZ facts may be useful while explicitly partial; record errors and unchanged ledger bytes without repairing unrelated history.

1. Verify a clean runtime and retain a verified SQLite backup plus the affected local configuration before activation.
2. Fast-forward the runtime to the tested, independently reviewed landing; refresh its editable package metadata without changing dependencies.
3. Restart existing long-running consumers only; preserve the note identity, installed job plists and exporter/collector cadences.
4. Preview and run the existing named CLIO refresh and selected nonembedding semantic maintenance facade. Reconcile eligible keys and every origin reference, and compare prior consumer IDs and prompt payloads to the backup.
5. Verify Daily citations, same-note/header preservation and delivered transport. For the optional XYZ seam, use existing explicit roots and prove the ledger is unchanged; retain the partial flag.
6. Observe normal guarded jobs before declaring scheduled consumer readiness. On rollback, restore the previous approved runtime and package metadata; restore only the changed config keys. Additive provenance columns are compatible with the previous reader. Use the verified consumer backup only for an observed data regression, with consumer writers paused; never rewind canonical CLIO history to undo a projection change.

exec
/bin/zsh -lc "git diff origin/development..HEAD -- . ':"'!TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md'"'
cat /Users/noelsaw/.codex/skills/review-code/SKILL.md" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
 succeeded in 2925ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-WILvQzS8' (errno=Operation not permitted)
2026-10-03 00:16:13.445 xcodebuild[49132:320148178]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:13.806 xcodebuild[49132:320148076] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-uwamx4xX' (errno=Operation not permitted)
2026-10-03 00:16:14.578 xcodebuild[50322:320150197]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:14.846 xcodebuild[50322:320150132] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/AGENTS.md b/AGENTS.md
index 3ae7d4b..1000b36 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -11,7 +11,7 @@
 
 This repo **is** an MCP server. Every refresh and query path is exposed through MCP tools — do not scan the codebase for `rebalance ...` CLI commands or write ad-hoc shell pipelines. Reach for the tools first.
 
-**"Find my recent work" queries.** When the user asks to find, summarize, or locate recent work/activity (what they've been doing, which project touched X recently, etc.), use `ask()`, `get_next_actions()`, `github_balance()`, `peek_source()`, or `publish_pulse()` — not Spotlight (`mdfind`) or ad-hoc filesystem search. The MCP's SQLite index is purpose-built for this and stays current via `refresh_index`. Reserve Spotlight/`find` for pure disk-location questions the registry doesn't track (e.g. "where did this repo get moved to on disk").
+**"Find my recent work" queries.** When the user asks to find, summarize, or locate recent work/activity (what they've been doing, which project touched X recently, etc.), use `ask()`, `get_next_actions()`, `hiqs_work_activity()` (alias: `github_balance()`), `peek_source()`, or `publish_pulse()` — not Spotlight (`mdfind`) or ad-hoc filesystem search. The MCP's SQLite index is purpose-built for this and stays current via `refresh_index`. Reserve Spotlight/`find` for pure disk-location questions the registry doesn't track (e.g. "where did this repo get moved to on disk").
 
 > ### 🧭 Start here — the central orchestrator (the data-plane spine)
 >
@@ -42,7 +42,7 @@ This repo **is** an MCP server. Every refresh and query path is exposed through
 3. **Discover projects:** Call `run_preflight(vault_path)`. Present results using friendly labels: "Most active" = `most_likely_active_projects` (last 14 days), "Semi-active" = `semi_active_projects` (15–30 days), "Dormant" = `dormant_projects` (31+ days), "Vault only" = `potential_projects`. If `github_error` is set, inform the user that GitHub discovery failed. Ask which to keep, remove, or merge. For each kept project, collect: short summary (2–3 sentences) and priority tier (1–5).
 4. **Confirm:** Call `confirm_projects(projects, vault_path)`. Each project dict **must** include `status: "active"`. Minimum shape: `{name, status: "active", summary, repos: [], priority_tier: int, tags: []}`.
 5. **Verify:** Call `list_projects()` to confirm projects are queryable.
-6. **Initial refresh:** Call `refresh_index(scope=["all"])` to populate the SQLite knowledge base. Use `dry_run=True` first for a preview. After it completes, `github_balance()` will return per-project commit/PR/issue counts.
+6. **Initial refresh:** Call `refresh_index(scope=["all"])` to populate the SQLite knowledge base. Use `dry_run=True` first for a preview. After it completes, `hiqs_work_activity()` will return per-project HiQS work activity counts.
 
 **Onboarding & project tools:**
 
@@ -53,7 +53,7 @@ This repo **is** an MCP server. Every refresh and query path is exposed through
 | `run_preflight(vault_path)` | Discover project candidates (read-only) |
 | `confirm_projects(projects, vault_path)` | Write registry and sync to DB |
 | `list_projects(status?)` | Query projects (default: active) |
-| `github_balance(since_days?)` | GitHub activity per project (requires prior refresh) |
+| `hiqs_work_activity(since_days?)` | HiQS work activity per project (deprecated alias: `github_balance`; requires prior refresh) |
 
 **Targeted retrieval and synthesis:**
 
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 63d6947..fdd694a 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -10,6 +10,12 @@
 > **not** reintroduce an `[Unreleased]` block — add to (or roll work into) the
 > current dated version instead. See AGENTS.md → "Versioning & Changelog".
 
+## [0.98.1] - 2026-10-03
+
+### Changed
+
+- The per-project work-activity signal is now canonically named HiQS work activity (HiQS = High Quality Signals): a new `hiqs_work_activity` MCP tool joins `get_hiqs_work_activity()` as the canonical namespace, while `github_balance` and `get_github_balance` remain as deprecated aliases with identical behavior. Operator-facing labels updated; the storage table and output contract are unchanged for downstream consumers.
+
 ## [0.98.0] - 2026-10-02
 
 ### Added
diff --git a/MCP.md b/MCP.md
index c79da47..9f2b798 100644
--- a/MCP.md
+++ b/MCP.md
@@ -65,9 +65,11 @@ Returns projects from the `project_registry` table.
 
 ---
 
-### `github_balance`
+### `hiqs_work_activity`
 
-Shows GitHub commit/PR/issue activity per project over a rolling window.
+Shows HiQS work activity (commit/PR/issue) per project over a rolling window.
+HiQS = High Quality Signals. `github_balance` remains as a deprecated alias of
+this tool (GH-316): same implementation, identical response shape.
 
 **Prerequisite:** run `rebalance github-scan` via CLI first to populate the `github_activity` table. See PROJECT.md — Step 6 for setup.
 
@@ -426,7 +428,7 @@ A human-readable reference for all running MCP servers on this machine. Store at
 rebalance   python -m rebalance.mcp_server   REBALANCE_DB=/absolute/path/to/rebalance.db
 ```
 
-Live tools: `ask`, `list_projects`, `github_balance`, `query_notes`, `query_github_context`, `github_release_readiness`, `github_close_candidates`, `search_vault`, `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges`, `sleuth_sync_reminders`, `onboarding_status`, `setup_github_token`, `run_preflight`, `confirm_projects`
+Live tools: `ask`, `list_projects`, `hiqs_work_activity` (alias: `github_balance`), `query_notes`, `query_github_context`, `github_release_readiness`, `github_close_candidates`, `search_vault`, `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges`, `sleuth_sync_reminders`, `onboarding_status`, `setup_github_token`, `run_preflight`, `confirm_projects`
 Planned: `weekly_rebalance`, `project_attention`, `review_unattributed_attention`, `classify_attention_item`, `todays_agenda`, `morning_brief`
 
 ---
diff --git a/PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md b/PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md
new file mode 100644
index 0000000..94cf7f6
--- /dev/null
+++ b/PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md
@@ -0,0 +1,95 @@
+---
+gh_issue: 316
+source: https://github.com/HiQS-Labs/rebalanceOS/issues/316
+title: "Rename the work-activity signal to \"HiQS work activity\" (labels + namespace) with a backwards-compatibility adapter"
+status: In progress — plan QA approved (round 1 corrections applied); implementation done, final QA pending
+created: 2026-10-03
+updated: 2026-10-03
+owner: Noel (start-task)
+goal: Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project work-activity signal, with a backwards-compatibility adapter so no existing consumer breaks.
+doc_type: project
+branch: feat/hiqs-work-activity-naming
+effort: 2
+complexity: 2
+risk: 1
+phases: 1
+---
+
+# HiQS work activity — canonical naming with a compatibility adapter
+
+## Status
+
+| What was just completed | What's next |
+|---|---|
+| Plan QA round 1 (CHANGES) adjudicated: all three shoulds accepted; adapter approved as designed. Implementation complete — Python + MCP adapter, labels, docs, parity test (red-first), 0.98.1. | Full gate once, final Codex QA on the diff, then PR. |
+
+Rating: **rated 55/15/50/55**.
+- **Priority 55:** user-directed; aligns code vocabulary with marketing (HiQS = High Quality Signals); newer work (#315) already adopts the term organically.
+- **Severity 15:** naming-consistency debt, no defect or data consequence.
+- **Appeal 50:** neutral; the operator didn't set a score.
+- **Effort 55:** mechanical but broad — many small string surfaces plus two alias seams.
+
+## Phase 0 — Prior art review
+
+- `src/rebalance/mcp/tools/projects.py:26` — FastMCP tool `github_balance`, registered via `projects.register(mcp, db)` (`mcp/server.py:15`). **Extend:** add the canonical `hiqs_work_activity` tool beside it; keep the old name as a deprecated alias calling the same implementation.
+- `src/rebalance/ingest/github_scan.py:741` — `get_github_balance()`, the public ingest-layer API. **Rename to `get_hiqs_work_activity()` and keep `get_github_balance` as a module-level alias** (zero callers break).
+- `src/rebalance/ingest/db/queries.py` — `fetch_github_balance` + table `github_activity`. **Unchanged:** internal transport names, guarded by `test_queries_mirror_invariance.py:264` and the read-layer ratchet; renaming would be a schema/migration concern with zero operator value (AGENTS.md: function over transport — internals keep transport names).
+- `src/rebalance/ingest/querier.py:287` — `"## GitHub Activity (last 7 days)"` header in the gathered context (surfaces in dashboard/pulse output). **Relabel.**
+- `src/rebalance/cli/query.py:118` — `"\n--- GitHub Activity ---"`. **Relabel.**
+- `src/rebalance/cli/github.py:64,72` — `github-scan` help strings. **Relabel** ("Scan HiQS work activity (GitHub) …").
+- `src/rebalance/cli/onboard.py:124` — discovery string. **Relabel.**
+- `README.md` / `AGENTS.md` — signal-presenting mentions (`github_balance` rows). **Relabel** where they name the signal; keep "GitHub activity" where it names the raw ingested data source (ingestion vs signal distinction, stated below).
+- MCP test pattern: `tests/test_mcp_probe.py`. **Extend** with an alias-parity check (both tool names resolve; identical output for the same DB).
+- Nearest prior work: #315 (already says "HiQS activity"), #313 (rename family), #124 (org-rename precedent).
+
+## Requirements
+
+1. **Canonical name:** `hiqs_work_activity` (MCP tool), `get_hiqs_work_activity()` (Python), label "HiQS work activity" (operator-facing strings).
+2. **Backwards-compatibility adapter (required):** `github_balance` MCP tool remains registered and functional, its docstring marking it the deprecated alias of `hiqs_work_activity`; `get_github_balance` remains as an alias of the canonical function. Both tools return byte-identical shapes for the same inputs.
+3. **Contract freeze:** table `github_activity`, SQL reader `fetch_github_balance`, and all output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by #300 / Needle-fork#79.
+4. **Label rule:** strings that present the *signal* say "HiQS work activity"; strings that describe *ingesting the raw GitHub data source* stay literal ("GitHub activity"). This keeps the diff honest instead of blind-replacing.
+
+## Smallest surface (ordered)
+
+1. `ingest/github_scan.py` — rename `get_github_balance` → `get_hiqs_work_activity` (+ docstring), add `get_github_balance = get_hiqs_work_activity` alias line with a deprecation note.
+2. `mcp/tools/projects.py` — add `hiqs_work_activity` tool (canonical docstring); reduce `github_balance` to a deprecated alias calling the same function.
+3. `ingest/querier.py:287` + `cli/query.py:118` + `cli/github.py:64,72` + `cli/onboard.py:124` — relabel to "HiQS work activity".
+4. `README.md`, `AGENTS.md` — relabel signal-presenting mentions of `github_balance` / "GitHub activity".
+5. `tests/test_mcp_probe.py` (or a focused new test file following its pattern) — alias parity: both tool names registered; same DB → identical rows; `get_github_balance is get_hiqs_work_activity` alias assertion.
+6. Version bump 0.98.0 → 0.98.1 + CHANGELOG entry.
+
+## Non-goals
+
+- No table rename, no schema migration, no JSON key changes, no `agent_tags` value changes, no SOP §8 contract changes, no close-loop (#308) renaming.
+
+## Risks and rollback
+
+- **Consumer drift:** external MCP clients referencing `github_balance` keep working (alias) — the only risk is them never migrating; acceptable, the alias docstring steers them.
+- **Over-replacement:** blind string replacement could corrupt the ingestion-vs-signal distinction; mitigated by the label rule above and surgical per-file edits.
+- **Rollback:** purely additive aliases + label strings; revert the PR.
+
+## Tests and gate
+
+- Focused: alias parity test + `tests/test_mcp_probe.py` + `tests/test_queries_mirror_invariance.py`.
+- Gate once on the final commit: `pytest tests/`, `utils/pdda/pdda.sh run`, `check_script_inventory.py --check`, `check_read_layer.py`.
+
+## Acceptance
+
+- Both MCP tool names live with identical shapes; `get_github_balance` alias intact.
+- No signal-presenting operator string says bare "GitHub activity"; storage and JSON keys unchanged.
+- Full suite + ratchets green; issue #316 acceptance boxes checkable.
+
+## Codex plan QA log
+
+**Round 1** (Codex `gpt-6-astra` via consult.sh, read-only worktree, 2026-10-03): verdict **CHANGES — approve after these small plan corrections; retain the two alias seams** (verbatim recommendation).
+
+| # | Finding | Disposition |
+|---|---|---|
+| 1 | [Should] Plan violated its own ingestion-vs-signal rule: `cli/github.py:72` scan wording and `cli/onboard.py:124` discovery wording must stay literal; only the MCP tool reference at `cli/github.py:64` changes. | **Accepted.** Both strings stay literal; only the tool reference updated. |
+| 2 | [Should] Frozen-key list was incomplete — output also carries `repos_linked` and `is_idle` (`queries.py:405`); parity test must assert a populated row with the exact nine-key set, not alias-vs-alias equality. | **Accepted.** `FROZEN_OUTPUT_KEYS` (9 keys) asserted in the test; reviewer's claim verified firsthand at `queries.py:405-410`. |
+| 3 | [Should] Add `MCP.md:68` + tool list `:429`; classify the dashboard "Recent GitHub Activity" (`note_builder.py:374,419`) which is an org rollup from `fetch_org_activity`, a different signal. | **Accepted.** MCP.md updated with canonical name + compat note. Dashboard org view: **Disposition: Retain (out of scope — different signal)**, consistent with the ingestion-vs-signal rule; recorded here. |
+| 4-5 | [Pass] Adapter boundaries sufficient; no ratchet conflict. | Noted. |
+| 6 | [Pass/Nit] 0.98.1 PATCH agreed; label the fourth rating axis "effort cheapness". | Applied in the rating note. |
+| 7 | [Nit] Frontmatter status contradicted the status table. | Fixed (this revision). |
+
+Round 2 not required: the reviewer's recommendation pre-approved the corrections; no scope, architecture, or risk changed.
diff --git a/README.md b/README.md
index 513eae1..7083825 100644
--- a/README.md
+++ b/README.md
@@ -173,7 +173,7 @@ Data sources
                                      ▼
                            MCP server — src/rebalance/mcp/
                            25 tools across 7 domains:
-                             Projects  list_projects · github_balance
+                             Projects  list_projects · hiqs_work_activity
                              Onboarding  onboarding_status · setup_github_token
                                          run_preflight · confirm_projects
                                          ingest_gmail_messages
diff --git a/ROADMAP.md b/ROADMAP.md
index ff1abc5..4f71187 100644
--- a/ROADMAP.md
+++ b/ROADMAP.md
@@ -37,6 +37,7 @@ goal: >
 - **CLIO journey replay** ([#230](https://github.com/HiQS-Labs/rebalanceOS/issues/230)) — private spike reviewed and ready for review in #231; human usefulness remains a release decision; [plan](PROJECT/2-WORKING/GH-230-CLIO-JOURNEY-SPIKE.md).
 
 ### In progress
+- **HiQS work activity naming with a backwards-compatibility adapter** ([#316](https://github.com/HiQS-Labs/rebalanceOS/issues/316)) — active one-phase plan: canonical `hiqs_work_activity` MCP tool + `get_hiqs_work_activity()` with `github_balance` kept as a deprecated alias; labels relabeled; storage table and JSON keys unchanged. rated 55/15/50/55 → [GH-316-HIQS-WORK-ACTIVITY-NAMING.md](PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md)
 - **Close-the-loop flags from the local GitHub corpus** ([#307](https://github.com/HiQS-Labs/rebalanceOS/issues/307)) — active one-phase plan: one deterministic per-repo reader plus `github-close-loop` CLI (stale PR, forgotten draft, needs refinement, closed without delivery, started-not-shipped) reusing the resolved readiness reader, feeding #300 and the triple-arm work. rated 65/35/50/75 → [GH-307-CLOSE-LOOP-FLAGS.md](PROJECT/2-WORKING/GH-307-CLOSE-LOOP-FLAGS.md)
 - **Fleet Pulse delivery** ([#282](https://github.com/HiQS-Labs/rebalanceOS/issues/282)) — Phase 1 merged; device-owned output, sole collector delivery and local rollout active; four-Mac/seven-day qualification remains. [Plan](PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md).
 - **One install path — per-job installers folded into `stack.sh`** ([#255](https://github.com/HiQS-Labs/rebalanceOS/issues/255)) — GH-241 follow-up. Phase 1 merged 2026-09-23 via PR #256: `stack.sh up` and the 13 per-job installers had drifted apart; the installers are deleted and one install flow remains. Open: macOS proof via GH-211, and Phase 2. rated 70/65/55/60 → [GH-255-ONE-INSTALL-PATH.md](PROJECT/2-WORKING/GH-255-ONE-INSTALL-PATH.md)
diff --git a/TESTS-RESULTS/2026-10-03+GH-316/SUMMARY.md b/TESTS-RESULTS/2026-10-03+GH-316/SUMMARY.md
new file mode 100644
index 0000000..844c8c6
--- /dev/null
+++ b/TESTS-RESULTS/2026-10-03+GH-316/SUMMARY.md
@@ -0,0 +1,5 @@
+# GH-316 — QA evidence
+
+Not a measurement campaign: this folder retains the plan-consult transcript
+(qa/plan-consult-r1.md, verbatim, fenced) for the naming/adapter change.
+Verdict and per-finding dispositions live in the working doc's QA log.
diff --git a/manifest.json b/manifest.json
index 1f64cbe..f3ba84f 100644
--- a/manifest.json
+++ b/manifest.json
@@ -2,7 +2,7 @@
   "mcpb_version": "0.1",
   "name": "rebalance-os",
   "display_name": "rebalance OS",
-  "version": "0.98.0",
+  "version": "0.98.1",
   "description": "Your workday OS \u2014 surfaces what matters, flags project imbalances, and answers questions about your own work using your Obsidian vault, GitHub activity, and Google Calendar. All local, all on your data.",
   "long_description": "rebalance OS ingests your Obsidian vault, GitHub activity, and Google Calendar into a local SQLite database, then lets you ask natural language questions about your own work. It flags over-investment in low-priority projects, surfaces neglected high-priority work, and assembles context for meetings \u2014 all running locally on Apple Silicon via MLX.",
   "author": {
diff --git a/pyproject.toml b/pyproject.toml
index a103d0b..7ce74b0 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -4,7 +4,7 @@ build-backend = "setuptools.build_meta"
 
 [project]
 name = "rebalance-os"
-version = "0.98.0"
+version = "0.98.1"
 description = "Local-first workday operating system with MCP tools and Obsidian ingest"
 readme = "README.md"
 requires-python = ">=3.12"
diff --git a/src/rebalance/__init__.py b/src/rebalance/__init__.py
index a9eab93..c455637 100644
--- a/src/rebalance/__init__.py
+++ b/src/rebalance/__init__.py
@@ -28,7 +28,7 @@ import logging
 import os
 
 __all__ = ["__version__"]
-__version__ = "0.98.0"
+__version__ = "0.98.1"
 
 
 def _configure_logging() -> None:
diff --git a/src/rebalance/cli/github.py b/src/rebalance/cli/github.py
index 69f6193..cc575de 100644
--- a/src/rebalance/cli/github.py
+++ b/src/rebalance/cli/github.py
@@ -61,7 +61,7 @@ def github_scan(
     days: int = typer.Option(30, help="Number of days to look back (supports 30-day A/B/C band classification)"),
     database: Path | None = DBOption(),
 ) -> None:
-    """Fetch GitHub activity and persist to database for use by github_balance MCP tool."""
+    """Fetch GitHub activity and persist to database for use by the hiqs_work_activity MCP tool."""
     from rebalance.ingest.github_scan import scan_and_store_github_activity
 
     try:
diff --git a/src/rebalance/cli/query.py b/src/rebalance/cli/query.py
index fa415eb..af66bae 100644
--- a/src/rebalance/cli/query.py
+++ b/src/rebalance/cli/query.py
@@ -115,7 +115,7 @@ def ask_cmd(
         typer.echo(f"\n--- Raw context ({result.elapsed_seconds}s) ---\n")
 
     if result.github_context:
-        typer.echo("\n--- GitHub Activity ---")
+        typer.echo("\n--- HiQS Work Activity ---")
         for g in result.github_context:
             if g.get("is_idle"):
                 typer.echo(f"  {g['project_name']:25s}  IDLE")
diff --git a/src/rebalance/ingest/github_scan.py b/src/rebalance/ingest/github_scan.py
index bdb4838..5350d10 100644
--- a/src/rebalance/ingest/github_scan.py
+++ b/src/rebalance/ingest/github_scan.py
@@ -738,13 +738,13 @@ def filter_ignored_repo_activity(result: GitHubScanResult, ignored_repos: list[s
 # ---------------------------------------------------------------------------
 
 
-def get_github_balance(
+def get_hiqs_work_activity(
     database_path: Path,
     project_repos: dict[str, list[str]],
     since_days: int = 14,
 ) -> list[dict[str, Any]]:
     """
-    Return GitHub activity summary per project using the project→repos mapping.
+    Return the HiQS work activity summary per project (canonical name, GH-316).
 
     Args:
         database_path:  Path to the SQLite database.
@@ -752,8 +752,10 @@ def get_github_balance(
         since_days:     How many days back to aggregate.
 
     Returns:
-        List of dicts with project_name, total_commits, prs_opened, prs_merged,
-        issues_opened, last_active_at, repos_touched.
+        List of dicts with project_name, repos_linked, repos_touched,
+        total_commits, prs_opened, prs_merged, issues_opened, last_active_at,
+        is_idle. This output contract is frozen — external consumers
+        (storyline experiment, Needle-fork adapter) read it as-is.
     """
     if not database_path.exists():
         return []
@@ -764,6 +766,11 @@ def get_github_balance(
         return fetch_github_balance(conn, project_repos, since_days=since_days)
 
 
+# Backwards-compatibility adapter (GH-316): github_balance is the deprecated
+# name of the HiQS work activity signal; kept so existing callers never break.
+get_github_balance = get_hiqs_work_activity
+
+
 # ---------------------------------------------------------------------------
 # Preflight discovery — GitHub repositories
 # ---------------------------------------------------------------------------
diff --git a/src/rebalance/ingest/querier.py b/src/rebalance/ingest/querier.py
index 3be3038..3a2b37d 100644
--- a/src/rebalance/ingest/querier.py
+++ b/src/rebalance/ingest/querier.py
@@ -196,11 +196,11 @@ def _gather_github_context(
     project_repos: dict[str, list[str]],
     since_days: int = 7,
 ) -> list[dict[str, Any]]:
-    """Per-project GitHub activity summary."""
-    from rebalance.ingest.github_scan import get_github_balance
+    """Per-project HiQS work activity summary."""
+    from rebalance.ingest.github_scan import get_hiqs_work_activity
 
     try:
-        return get_github_balance(
+        return get_hiqs_work_activity(
             database_path=database_path,
             project_repos=project_repos,
             since_days=since_days,
@@ -284,7 +284,7 @@ def _build_prompt(
 
     # GitHub activity
     if github_context:
-        lines = ["## GitHub Activity (last 7 days)"]
+        lines = ["## HiQS Work Activity (last 7 days)"]
         for g in github_context:
             if g.get("is_idle"):
                 lines.append(f"- {g['project_name']}: IDLE (no activity)")
diff --git a/src/rebalance/mcp/tools/projects.py b/src/rebalance/mcp/tools/projects.py
index 37205c1..881ee7d 100644
--- a/src/rebalance/mcp/tools/projects.py
+++ b/src/rebalance/mcp/tools/projects.py
@@ -5,7 +5,7 @@ from typing import Any
 
 from mcp.server.fastmcp import FastMCP
 
-from rebalance.ingest.github_scan import get_github_balance
+from rebalance.ingest.github_scan import get_hiqs_work_activity
 from rebalance.ingest.registry import get_projects
 
 
@@ -23,17 +23,28 @@ def register(mcp: FastMCP, database_path: Path) -> None:
         return get_projects(database_path, status=normalized or None)
 
     @mcp.tool()
-    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
+    def hiqs_work_activity(since_days: int = 30) -> list[dict[str, Any]]:
         """
-        Show GitHub activity balance across active projects.
+        Show HiQS work activity balance across active projects (canonical name).
 
-        Returns one row per project with commit/PR/issue counts over the last
-        `since_days` days.  Projects with no GitHub activity are flagged as
-        idle (is_idle=true).  Requires a prior `rebalance github-scan` run.
+        HiQS = High Quality Signals. Returns one row per project with
+        commit/PR/issue counts over the last `since_days` days.  Projects with
+        no HiQS work activity are flagged as idle (is_idle=true).  Requires a
+        prior `rebalance github-scan` run.
         """
         project_repos = _project_repos_map(database_path)
-        return get_github_balance(
+        return get_hiqs_work_activity(
             database_path=database_path,
             project_repos=project_repos,
             since_days=since_days,
         )
+
+    @mcp.tool()
+    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
+        """
+        Deprecated alias of `hiqs_work_activity` (GH-316).
+
+        Same implementation and identical response shape; use the canonical
+        `hiqs_work_activity` tool going forward.
+        """
+        return hiqs_work_activity(since_days=since_days)
diff --git a/tests/test_hiqs_work_activity_alias.py b/tests/test_hiqs_work_activity_alias.py
new file mode 100644
index 0000000..7303c44
--- /dev/null
+++ b/tests/test_hiqs_work_activity_alias.py
@@ -0,0 +1,83 @@
+"""GH-316: `hiqs_work_activity` is canonical; `github_balance` stays as a deprecated alias.
+
+Both MCP tool names must resolve through the real FastMCP server and return
+identical, fully-populated rows — and the frozen output contract (all nine
+keys) must not drift while the naming changes.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import json
+import tempfile
+import unittest
+from pathlib import Path
+
+from rebalance.ingest.db import (
+    db_connection,
+    ensure_github_schema,
+    ensure_project_schema,
+    ensure_schema,
+)
+from rebalance.ingest.github_scan import get_github_balance, get_hiqs_work_activity
+from rebalance.mcp.server import create_server
+
+FROZEN_OUTPUT_KEYS = {
+    "project_name",
+    "repos_linked",
+    "repos_touched",
+    "total_commits",
+    "prs_opened",
+    "prs_merged",
+    "issues_opened",
+    "last_active_at",
+    "is_idle",
+}
+
+
+def _call(server, name: str, args: dict):
+    """Invoke an MCP tool; FastMCP emits one JSON text block per list item."""
+    content, _ = asyncio.run(server.call_tool(name, args))
+    return [json.loads(block.text) for block in content]
+
+
+class HiqsWorkActivityAliasTests(unittest.TestCase):
+    def setUp(self) -> None:
+        self._tmp = tempfile.TemporaryDirectory()
+        self.addCleanup(self._tmp.cleanup)
+        self.db = Path(self._tmp.name) / "rebalance.db"
+        with db_connection(self.db, ensure_schema) as conn:
+            ensure_project_schema(conn)
+            ensure_github_schema(conn)
+            conn.execute(
+                "INSERT INTO project_registry (name, status, repos_json, tags_json, custom_fields_json)"
+                " VALUES ('Alpha', 'active', '[\"a/one\"]', '[]', '{}')"
+            )
+            conn.execute(
+                "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,"
+                " prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)"
+                " VALUES ('me', 'a/one', '2026-10-01', 7, 2, 3, 1, 0, 0, 0,"
+                " '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')"
+            )
+            conn.commit()
+
+    def test_python_alias_is_the_canonical_function(self) -> None:
+        self.assertIs(get_github_balance, get_hiqs_work_activity)
+
+    def test_both_mcp_tool_names_return_identical_populated_rows(self) -> None:
+        server = create_server(self.db)
+        canonical = _call(server, "hiqs_work_activity", {"since_days": 30})
+        alias = _call(server, "github_balance", {"since_days": 30})
+        self.assertEqual(canonical, alias)
+        self.assertEqual(len(canonical), 1)
+        row = canonical[0]
+        self.assertEqual(set(row), FROZEN_OUTPUT_KEYS)
+        self.assertEqual(row["project_name"], "Alpha")
+        self.assertEqual(row["total_commits"], 7)
+        self.assertEqual(row["prs_merged"], 1)
+        self.assertFalse(row["is_idle"])
+        self.assertEqual(row["repos_touched"], ["a/one"])
+
+
+if __name__ == "__main__":
+    unittest.main()
---
name: review-code
description: >-
  Meticulous code and pull request review ladder using /recon and /debug-mantra to test out each
  fix and feature against live ground truth. Supports PR targets under review-PR / --pr <PR#>.
  Loops through /workhorse and /unstuck ladders to autonomously resolve reversible adaptations and
  pivots without stopping for operator permission, driving verified forward movement.
metadata:
  argument-hint: "[diff, branch, file, or --pr <PR#>]"
---

# /review-code (and /review-pr) — Meticulous Ground-Truth Code & PR Review Ladder

`/review-code` is an empirical code and pull request review discipline that treats every proposed
change as a claim requiring firsthand verification. Rather than passively reading a diff and commenting
on style or plausible appearance, `/review-code` actively maps the system's blast radius, tests
fixes and features against live execution, and uses autonomous problem-resolution ladders to drive
forward movement.

It coordinates four specialized disciplines into a cohesive review workflow:
1. **[`/recon`](../../1-hourly/recon/SKILL.md)**: Seam and blast-radius mapping across callers, data
   flows, public contracts, and operational failure paths before forming an opinion.
2. **[`/debug-mantra`](../../1-hourly/debug-mantra/SKILL.md)**: Meticulous ground-truth testing.
   Falsifies symptom-fix patches, executes mutation tests to watch assertions go red, and verifies
   feature acceptance criteria with negative controls and measured evidence.
3. **[`/workhorse`](../workhorse/SKILL.md)**: Governed defect resolution ladder. Triages review
   findings into an atomic priority queue (`[Blocker]`, `[Should]`, `[Nit]`, `[Pass]`) and enforces
   least-mechanism architecture ([`/ponytail`](../../1-hourly/ponytail/SKILL.md)), governance compliance,
   and preservation invariants.
4. **[`/unstuck`](../../1-hourly/unstuck/SKILL.md)**: Autonomous forward movement and anti-hesitation
   engine. Classifies adaptations on the Reversibility Scale (`Easy` vs `Costly` vs `One-way door`):
   **autonomously adapts and tests `Easy` reversible pivots without stopping to prompt the operator**,
   freezes cogs, and applies foundational unblocking moves.

---

## Recite this — verbatim, as the first thing in your first response

> **Review-Code Discipline:**
> 1. **Ingest target & map blast radius (Phase 1 /recon).** Ingest the diff or PR (`review-PR`), map callers, state mutations, contracts, failure paths, and audit adherence to centralized helpers and zero parallel subsystems (DRY).
> 2. **Meticulously test fixes & features (Phase 2 /debug-mantra).** Test every fix against root cause (falsify symptom patches; mutate guards to watch them fail) and verify feature acceptance criteria with measured ground truth and negative controls.
> 3. **Autonomous resolution & anti-hesitation (Phase 3 /workhorse + /unstuck).** If pivots or adaptations are needed, classify reversibility (`Easy`/`Costly`/`One-way door`): autonomously adapt and test `Easy` changes without operator round-trips; freeze cogs and execute foundational unblocking moves.
> 4. **Grade & synthesize verified findings (Phase 4).** Categorize findings (`[Blocker]`, `[Should]`, `[Nit]`, `[Pass]`) with exact `file:line` citations, emit the actionable checklist, and deliver the verdict twice: post the report to the GitHub PR/issue via `gh` **and** render it on-screen with the verified comment URL. Never one without the other.
>
> **Overall Goal:** Every fix and feature verified against live behavior rather than plausible appearance, with reversible issues resolved autonomously and review conclusions grounded in runnable proof.

Then begin work. When `/review-code` (or `/review-pr`) is the active orchestrating skill, this recital
precedes subordinate skill invocations; subordinate skills ([`/recon`](../../1-hourly/recon/SKILL.md),
[`/debug-mantra`](../../1-hourly/debug-mantra/SKILL.md), etc.) are then loaded for their mechanics
without conflicting recitals.

---

## The 5-Phase Review Ladder

```text
Phase 0: Target Intake & Scope Resolution  ──► Local diff/branch vs GitHub PR (`review-PR`); isolate refs & context
                 │
                 ▼
Phase 1: Seam & Blast Radius Recon (/recon)──► Map callers (Lane A), state (Lane B), contracts (Lane C), tests (Lane D), DRY (Lane E)
                 │
                 ▼
Phase 2: Meticulous Ground-Truth Testing   ──► Fixes: Repro -> trace fail path -> mutate-to-red (falsify)
         (/debug-mantra)                   ──► Features: Measured ground truth -> falsify criteria -> negative controls
                 │
                 ▼
Phase 3: Autonomous Pivot & Resolution     ──► Classify reversibility: Easy (autonomous forward move) vs Costly vs One-way
         (/workhorse + /unstuck)           ──► Self-invoke /unstuck on hesitation tripwires; apply /ponytail root-cause fix
                 │
                 ▼
Phase 4: Graded Findings & PR Actionability──► [Blocker] / [Should] / [Nit] / [Pass] with mandatory file:line citations;
                                               report posted to the GH PR/issue AND rendered on-screen with the verified comment URL
```

---

## Phase 0: Target Intake & Scope Resolution

Resolve the exact target under review. Two primary entry modes are supported:

### Mode A: Local Code Review (`/review-code`)
Used for uncommitted working tree changes, staged diffs, branch diffs against upstream, or targeted files:
```bash
# Review uncommitted changes against HEAD
git diff HEAD

# Review current branch against development baseline
git diff origin/development...HEAD

# Stat changes to size the review blast radius
git diff --stat origin/development...HEAD
```

### Mode B: GitHub Pull Request Review (`review-PR` / `/review-code --pr <PR#>`)
Triggered via `review-PR`, `/review-pr <PR#>`, or `/review-code --pr <PR#>`:
```bash
# Inspect PR metadata, base branch, head branch, author, and description
gh pr view <PR#> --json number,title,body,baseRefName,headRefName,headRefOid,author,state

# Fetch the raw unified diff for the PR
gh pr diff <PR#>

# Inspect linked issues (Fixes #..., Closes #..., GH-...) and project documentation
grep -E "(Fixes|Closes|Resolves) #[0-9]+" <<< "$(gh pr view <PR#> --json body -q .body)"

# Check hosted CI check run statuses
gh pr checks <PR#>
```

**Scope Invariant:**
- Identify the target branch: ensure the PR targets the active WIP branch (`development`), not `main` (per orchestrator rails).
- Size the diff: a targeted bug fix should typically be focused (< 500 lines); large architectural diffs require all 5 recon lanes.

---

## Phase 1: Seam & Blast Radius Recon ([`/recon`](../../1-hourly/recon/SKILL.md))

A diff read in isolation is plausible fiction. Code review requires knowing what callers, state,
contracts, and failure modes are touched by the modification.

Run the five recon lanes across the touched symbols:

| Lane | Focus | Review Inquiry & Verification |
|---|---|---|
| **Lane A. Entry & Call Paths** | Callers & Dispatch | Trace callers of all modified functions. Did call signatures, parameter defaults, or return types change? Are callers in other modules updated? Check CLI shims, hook registries, plugin dispatch, and event handlers. |
| **Lane B. State & Data Flow** | Readers & Writers | What state is mutated? Verify the single-writer invariant. Are SQLite locks, file descriptors, transactions, or cache layers handled? Does this introduce competing write paths or dirty reads? |
| **Lane C. Contracts & Boundaries** | APIs & Protocols | Do changes alter public APIs, CLI flags, JSON schemas, environment variables, or error codes? Check consumers across sibling modules or external repositories. |
| **Lane D. Build, Failure & Tests** | Errors & Coverage | How does this code fail? Trace timeouts, process exits, broken pipes, signal handling (`SIGINT`/`SIGTERM`), and missing input files. What existing test suites cover this seam? |
| **Lane E. Centralized Helpers & DRY** | Helpers & Anti-Reinvention | Does this change reinvent functionality that already exists in centralized helpers (e.g. `utils/py/`, canonical CLI shims, standard libraries)? Does it construct a parallel subsystem instead of extending existing modules (violating `GUIDING-PRINCIPLES.md` North Star)? Check for copy-pasted blocks or duplicate helper definitions across the diff. |

### Lane E: Centralized Helpers & Anti-Redundancy (DRY) Audit

The North Star (`GUIDING-PRINCIPLES.md`) requires: *durable, reversible, DRY; extend what exists rather than forking a parallel system.*
A diff that works but reinvents existing wheels introduces long-term tech debt, bugs, performance overhead, and maintenance drag.

Reviewers must audit three anti-redundancy checks:
1. **Centralized Helper Adherence:**
   - Did the diff implement custom logic (e.g. subprocess execution, lock management, path/root resolution, JSON parsing, git mutation guards, or date formatting) where a canonical helper already exists in `utils/py/`, `src/`, or shared runtime modules?
   - Bypassing an established helper in favor of an ad-hoc inline solution is a `[Blocker]`.
2. **Parallel Subsystem / Reinvention Trap:**
   - Does the change build parallel shadow machinery instead of extending established subsystems (e.g. custom telemetry logging instead of `.tick` events, custom runner loops instead of the existing driver)?
   - Standing up a parallel subsystem is an architectural violation and a mandatory `[Blocker]`.
3. **Intra-Diff & Cross-Module Duplication (DRY):**
   - Are there duplicated helper functions or copy-pasted logic across multiple files in the PR?
   - Code duplication that can be extracted cleanly into an existing shared utility is a `[Should]`.

**Graph & Source Lookup:**
- Prefer MCP graph tools (`search_graph`, `trace_path`, `get_code_snippet`) when available to locate callers and dependencies in one call.
- Fall back to targeted ripgrep / file inspection when MCP tools are unavailable.
- **The One Rule:** Every caller cited in the review must exist at `file:line`. Anything unread or unverified is recorded under **Unknowns**, never assumed safe.

---

## Phase 2: Meticulous Ground-Truth Testing ([`/debug-mantra`](../../1-hourly/debug-mantra/SKILL.md))

Verified beats plausible. Reviewers must not merely read code; they must test the behavior of
fixes and features against live reality.

### 1. Testing Fixes (Root Cause vs. Symptom-Fix Trap)

When reviewing a bug fix, apply the four debug mantras rigorously:

1. **Mantra 1 — Reproduce reliably:**
   - Verify there is an automated regression test reproducing the original defect.
   - If the regression test is missing, write one or require it before approving, unless the repo
     forbids new tests (XYZ-forge: `AGENTS.md` *No new tests*, GH-831). There, require the existing suite that
     covers it, or a recorded manual repro.
2. **Mantra 2 — Trace the fail path:**
   - Trace from the crash or incorrect output back to the root cause origin.
   - **The Symptom-Fix Trap:** Actively scrutinize whether the fix merely patches symptoms at the
     crash site (e.g. adding `try/except: pass`, defaulting a `None`, coercing types, adding loose
     regexes, or using `|| true`) while leaving the corrupt state producer intact upstream.
     *The crash site is where the invariant was checked; the bug is where it was broken.*
     A fix that masks the crash without preventing the bad state is a `[Blocker]`.
3. **Mantra 3 — Falsify the fix (The Mutation Test):**
   - **"A check that cannot fail is not a check."**
   - Mutate the fix in a disposable environment:
     - Invert the condition (`if not valid` → `if valid`).
     - Comment out the guard or remove the correction.
     - Transpose arguments or return dummy values.
   - Run the test suite: **Did the test turn RED?**
   - If the test still passes when the fix is broken, the test is decorative and reports confidence
     it never earned. This is a mandatory `[Blocker]`.
   - In a repo that forbids new tests (XYZ-forge: `AGENTS.md` *No new tests*, GH-831), where no existing suite
     covers the fix, a manual red control recorded under `TESTS-RESULTS/` satisfies this mantra. It mutates
     the fix and records the failing result.
4. **Mantra 4 — Cross-reference breadcrumbs:**
   - Walk recent `CHANGELOG.md` entries and git history. Does this fix repeat a previously failed
     pattern or reopen a settled architectural decision?

### 2. Testing Features (Acceptance Criteria & Boundary Invariants)

When reviewing a new feature or enhancement:

1. **Measured Ground Truth at Review Time:**
   - Execute the feature's entry points directly. Do not rely on claimed execution logs.
   - Verify outputs, return codes, and side-effects match specifications.
2. **Falsify Acceptance Criteria:**
   - **"An empty input passes every check."** Verify that empty strings, missing files, or zero-byte
     inputs fail loudly rather than passing vacuously through unhandled command substitutions or
     permissive wildcards.
   - Size-check extracted artifacts before asserting correctness over them.
3. **Negative Controls & Boundary Stress:**
   - Test invalid CLI arguments, malformed configuration files, and nonexistent paths.
   - Test concurrency and lock contention (e.g. parallel runs of `./validate.sh` or concurrent database access).
   - Test idempotency: does running the feature twice in succession produce identical, safe results without duplicate records or side effects?

---

## Phase 3: Autonomous Pivot & Resolution Loop ([`/workhorse`](../workhorse/SKILL.md) + [`/unstuck`](../../1-hourly/unstuck/SKILL.md))

When review or ground-truth testing surfaces failures, gaps, or necessary adaptations, the agent
must avoid constant round-trips to the operator for routine adjustments.

### 1. The Reversibility Decision Matrix

Classify every necessary adaptation or pivot on the repository's shared scale:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REVERSIBILITY CLASSIFICATION                          │
├─────────────────┬──────────────────────────────────┬────────────────────────┤
│ Classification  │ Scope & Characteristics          │ Action & Protocol      │
├─────────────────┼──────────────────────────────────┼────────────────────────┤
│ EASY            │ - Local test assertion fixes     │ AUTONOMOUSLY EXECUTE   │
│                 │ - Edge-case input handling       │ - Do NOT ask operator  │
│                 │ - Defensive parameter checks     │ - Implement & test     │
│                 │ - Fixing a typo or broken regex  │ - Record in ledger     │
│                 │ - /ponytail least-mechanism diff │ - Drive forward move   │
│                 │ - Negative tests, if repo allows │                        │
├─────────────────┼──────────────────────────────────┼────────────────────────┤
│ COSTLY          │ - Re-architecting shared schema  │ PREPARE ROLLBACK & ASK │
│                 │ - Breaking public API contracts  │ - Formulate 2 options  │
│                 │ - Introducing new dependencies   │ - Prove rollback path  │
│                 │ - Major coordination changes     │ - Await confirmation   │
├─────────────────┼──────────────────────────────────┼────────────────────────┤
│ ONE-WAY DOOR    │ - External resource deletion     │ HARD STOP & CONFIRM    │
│                 │ - Publishing secrets / tokens    │ - Name permanent loss  │
│                 │ - Destructive database drops     │ - Require operator OK  │
│                 │ - Upstream force-pushes          │                        │
└─────────────────┴──────────────────────────────────┴────────────────────────┘
```

**Autonomous Action Rail:**
If a change is classified **`Easy`** and directly resolves a review blocker or test failure to allow
forward movement, **execute the adaptation immediately**. Do not stop, narrate hesitation, or prompt
the operator for permission. Document the pivot cleanly in the final report.

### 2. The Unstuck Anti-Hesitation Engine ([`/unstuck`](../../1-hourly/unstuck/SKILL.md))

Self-invoke the [`/unstuck`](../../1-hourly/unstuck/SKILL.md) interrupt when encountering any of the
four autonomous tripwires:
1. **Two-Turn No-Milestone Tripwire:** Catching yourself asking "Should I test X?" or "Would you like
   me to review Y?" across two turns without advancing the review. *Stop asking; execute the test.*
2. **Tool Exit Code Inertia:** A test or command fails during review verification (e.g. exit code 1 or 2),
   and the agent halts or asks what to do. *Trace the failure with `/debug-mantra`, apply the `Easy`
   foundational fix, and re-run.*
3. **Passive Narration Detection:** Typing phrases like "Waiting for...", "Now I will see...", or "Let
   me know how to proceed" while an in-flight review is pending. *Freeze the cogs and act.*
4. **False Completion Detection:** About to report "LGTM" or "Approved" when acceptance tests were
   skipped, unmutated, or unverified. *Reject completion until evidence is collected.*

**The Five Unstuck Rungs during Review:**
- *Rung 1: Freeze the cogs.* Do not invent new review frameworks, extra wrappers, or meta-analysis.
- *Rung 2: Re-anchor the finish line.* State the observable deliverable: "Verified review report with
  runnable test receipts emitted."
- *Rung 3: Test the blocker.* Is the finding a genuine goal blocker, required correctness/safety,
  or merely polish/cog? (Park polish; queue blockers).
- *Rung 4: Choose one foundational action.* Apply the **No Bandages / No Painkillers Law**: do not
  silence type checks (`@ts-ignore`, `# noqa`), suppress asserts, or bypass gates. Apply the cleanest
  foundational fix.
- *Rung 5: Act once, verify movement, and re-drive.* Execute the move, check that the milestone
  advanced, and resume.

### 3. The Workhorse Defect Resolution Ladder ([`/workhorse`](../workhorse/SKILL.md))

When the review process requires remediating discovered defects:
- **Rung 0: Triage:** Deconstruct all issues into an atomic priority queue (`[Blocker]` → `[Should]` → `[Nit]`).
- **Rung 1: Ground Truth:** Capture raw repros and trace fail paths.
- **Rung 2: Least Mechanism ([`/ponytail`](../../1-hourly/ponytail/SKILL.md)):** Use the standard library
  first, extend existing modules, and produce the shortest working diff. Zero code sprawl.
- **Rung 3: Governance Gate:** Check compliance with `AGENTS.md`, `SOP.md`, `GUIDING-PRINCIPLES.md`,
  and frozen twin guards (`test/gh308-frozen-twin-guard.sh`).
- **Rung 5: Preservation Gate:** Prove preservation invariants before applying any destructive edit.
- **Rung 6: Semantic Verification:** Re-run test suites and verify observable outputs.

---

## Phase 4: Graded Findings & PR Actionability

Structure review findings into four standard citation-backed categories. Every finding must cite
exact `file:line` or symbol references.

### 1. Finding Categories

- 🛑 **`[Blocker]`**: Correctness defects, regressions, security/credential leaks, data loss hazards,
  untested error states, symptom patches hiding root causes, tests that pass on broken code,
  **reinventing a parallel subsystem when an established canonical mechanism exists (North Star violation),
  or bypassing established centralized helpers in favor of ad-hoc implementations.**
  *Requires resolution before merge/approval.*
- ⚠️ **`[Should]`**: Architectural gaps, missing test coverage / negative controls, non-optimal complexity,
  missing error logging, unhandled edge cases, **or non-DRY duplicate logic / redundant utility functions.**
  *Strongly recommended improvements.* In a repo that forbids new tests (XYZ-forge: `AGENTS.md` *No new tests*, GH-831), a
  missing-coverage finding asks for an existing suite or a recorded manual check, and a new test file in
  the diff is itself a `[Should]`.
- 💡 **`[Nit]`**: Style, documentation, variable naming, minor comment cleanups. *Non-blocking suggestions.*
- ✅ **`[Pass]`**: Confirmed correct execution paths with firsthand citations, verified test results,
  and passing mutation checks.

### 2. Structured Review Report Schema

Every `/review-code` report follows this structure:

```markdown
## 🛡️ Code Review Report: <Target / PR Title>

**Verdict:** `Approved` | `Changes Requested` | `Comment`
**Target:** `<Branch / Commit / PR #>` | **Diff Size:** `N lines (+A / -B)`
**Review Mode:** `Ground-Truth Verified (/recon + /debug-mantra)`

| Category | Count | Status |
|:---|:---:|:---|
| 🛑 `[Blocker]` | 0 | All clear |
| ⚠️ `[Should]`  | 1 | Action recommended |
| 💡 `[Nit]`     | 2 | Optional polish |
| ✅ `[Pass]`    | 8 | Verified firsthand |

---

### 🗺️ Recon Map & Blast Radius
- **Entry Points & Callers:** `src/entry.py:42`, `utils/cli.py:105` (all callers verified).
- **State & Data Invariants:** Single-writer verified; SQLite lock budget respected.
- **Contracts & Boundaries:** Public API backward-compatible; no breaking schema drift.
- **Centralized Helpers & DRY:** Canonical helpers used; zero parallel subsystems or reinvention detected.

---

### 🔬 Meticulous Testing & Verification Evidence
- **Ground Truth Repro:** Verified regression test `test/gh123_regression.py` fails without fix.
- **Mutation Falsification:** Mutated guard at `src/core.py:88`; verified test went **RED** (exit code 1).
- **Negative Controls:** Tested empty input and invalid flags; verified appropriate errors.
- **Reversible Adaptations Executed:** [Detail any `Easy` autonomous fixes applied during review].

---

### 📋 Detailed Findings & Actionable Checklist

#### 🛑 Blockers
- [ ] `src/auth.py:112` — Token comparison uses non-constant-time equality. `[Blocker]`
- [ ] `src/utils.py:45` — Reinvented git lock parsing instead of calling centralized helper `utils/py/rtl.py`. `[Blocker]`

#### ⚠️ Should Address
- [ ] `src/worker.py:45` — Missing negative control test for timeout event. `[Should]`

#### 💡 Nits & Minor Polish
- [ ] `src/utils.py:15` — Clarify docstring regarding return type. `[Nit]`

#### ✅ Verified Passes
- `src/core.py:88` — Thread-safe atomic update verified with concurrent worker test. `[Pass]`
```

### 3. Verdict Delivery: Post to GitHub AND Render On-Screen (mandatory — both, every run)

The review ships twice from the same bytes: once into the chat session, once into the GitHub target.
Posting is not an alternative to the on-screen report, is not optional, and is not gated on operator
approval — a review comment is reversible (it can be edited or deleted), so it is pre-authorized
here. Never pause to ask.

1. **Write the report to a file first.** Emit the full Phase 4 report as clean GitHub-flavored
   markdown to `temp/review-<PR#|issue#>-<YYYYMMDD-HHMM>.md` (create `temp/` if missing; never the
   repo root). The on-screen report and the posted comment must carry the same content.
2. **Post it without asking, with `--body-file`** (never `--body` — shell quoting silently mangles
   multi-line markdown):
   - PR target: `gh pr comment <PR#> --body-file <report.md>`
   - Issue target: `gh issue comment <N> --body-file <report.md>`
   Do not default to `gh pr review --request-changes` / `--approve`: branch protection may reject
   self-approval and a requested-changes gate blocks the merge; a plain comment always succeeds.
3. **Verify the post landed.** `gh pr comment` prints the comment URL on success — capture it. If no
   URL was captured, re-check via `gh pr view <PR#> --json comments` and confirm the report's
   heading line is present. An uncaptured URL is an unverified post.
4. **Render on-screen and close the loop.** Print the full report in the chat session, then the
   verification line `Posted: <comment-url>`. If posting failed, print the full report, the exact
   `gh` error, and `NOT POSTED: <reason>` — a failed post is reported, never silently skipped.
5. **Resolve the target before writing the report.** PR mode (`--pr <PR#>`) posts to that PR.
   Local-diff mode (`/review-code` without `--pr`): resolve the branch's open PR with
   `gh pr view --json number,url -q .number`, or use an explicit `--issue <N>` if given. If neither
   resolves, that is the only sanctioned skip — state `NO GH TARGET — report on-screen only` on
   screen and stop there. Nothing else may skip the post.

- **Linked Issue Checklists:** If the PR closes issues (`Fixes #123`), verify that all requirements
  in the linked issue or PDDA tracking document (`PROJECT/1-INBOX/` or `PROJECT/2-WORKING/`) are
  satisfied and reflected in the checklist before posting.

---

## Operating Rules & Safety Rails

1. **Lead with the line that survives skimming:** State the verdict, critical blocker count, and
   reversibility assessment in the very first sentence.
2. **Verified beats plausible:** Do not praise code or declare it "clean" without running tests,
   inspecting raw artifacts, or tracing execution paths. An unverified claim is an unknown.
3. **A check that cannot fail is not a check:** Always verify that assertions actually guard what they
   claim by witnessing them fail under mutation.
4. **An empty input passes every check:** Guard against vacuous passes by asserting extracted data
   volume and non-empty artifacts before evaluating results.
5. **Throwaway Full-Clone Isolation (GH-564 rail):** Never run mutation-heavy gates or destructive test
   suites in a primary clone whose state matters or in a linked worktree. Use a disposable full clone
   in `/tmp/` when running suites that touch git remotes, configs, or refs.
6. **Preserve working tree state (GH-527 rail):** Never use `git reset --hard`, `git checkout -- <path>`,
   or tree-wide `git stash` to clean up review experiments.
7. **Frozen Bash twins (GH-308 rail):** Ensure no modifications are made to legacy `.sh` twins under
   `utils/` or `relay-automation/`; all Tier-A runtime logic lives in Python under `utils/py/`.
8. **Builder/Orchestrator Role Split (GH-221 rail):** Claude is the orchestrator and reviewer.
   Autonomous adaptations are restricted to `Easy` reversible fixes and review assertions; do not
   drive headless full-system marathon builds without authorized builder lanes.
9. **The verdict ships twice (pre-authorized):** posting the Phase 4 report to the GitHub PR/issue
   is reversible and pre-authorized — do not pause for operator approval, and do not end a review
   with the report only on-screen when a GitHub target exists. The one sanctioned skip is
   `NO GH TARGET`, stated on screen.

codex
Graph tools are unavailable, so I’m tracing the adapter and its consumers directly in source. The snapshot has four commits above `origin/development`, rather than the five stated in the brief; I’ll anchor the review to HEAD `61c431f`.

exec
/bin/zsh -lc "git diff origin/development..HEAD -- src tests pyproject.toml manifest.json
nl -ba tests/test_hiqs_work_activity_alias.py
nl -ba src/rebalance/mcp/tools/projects.py
nl -ba src/rebalance/ingest/github_scan.py | sed -n '730,795p'
rg -n 'get_github_balance|get_hiqs_work_activity|github_balance|HiQS work activity|GitHub Activity' src/rebalance tests/test_mcp_probe.py
nl -ba src/rebalance/ingest/db/queries.py | sed -n '340,420p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
 succeeded in 2924ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-RuY21ziH' (errno=Operation not permitted)
2026-10-03 00:16:28.505 xcodebuild[65786:320176298]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:28.830 xcodebuild[65786:320176205] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-8LQDht8j' (errno=Operation not permitted)
2026-10-03 00:16:29.554 xcodebuild[67360:320178676]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:16:29.836 xcodebuild[67360:320178575] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/manifest.json b/manifest.json
index 1f64cbe..f3ba84f 100644
--- a/manifest.json
+++ b/manifest.json
@@ -2,7 +2,7 @@
   "mcpb_version": "0.1",
   "name": "rebalance-os",
   "display_name": "rebalance OS",
-  "version": "0.98.0",
+  "version": "0.98.1",
   "description": "Your workday OS \u2014 surfaces what matters, flags project imbalances, and answers questions about your own work using your Obsidian vault, GitHub activity, and Google Calendar. All local, all on your data.",
   "long_description": "rebalance OS ingests your Obsidian vault, GitHub activity, and Google Calendar into a local SQLite database, then lets you ask natural language questions about your own work. It flags over-investment in low-priority projects, surfaces neglected high-priority work, and assembles context for meetings \u2014 all running locally on Apple Silicon via MLX.",
   "author": {
diff --git a/pyproject.toml b/pyproject.toml
index a103d0b..7ce74b0 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -4,7 +4,7 @@ build-backend = "setuptools.build_meta"
 
 [project]
 name = "rebalance-os"
-version = "0.98.0"
+version = "0.98.1"
 description = "Local-first workday operating system with MCP tools and Obsidian ingest"
 readme = "README.md"
 requires-python = ">=3.12"
diff --git a/src/rebalance/__init__.py b/src/rebalance/__init__.py
index a9eab93..c455637 100644
--- a/src/rebalance/__init__.py
+++ b/src/rebalance/__init__.py
@@ -28,7 +28,7 @@ import logging
 import os
 
 __all__ = ["__version__"]
-__version__ = "0.98.0"
+__version__ = "0.98.1"
 
 
 def _configure_logging() -> None:
diff --git a/src/rebalance/cli/github.py b/src/rebalance/cli/github.py
index 69f6193..cc575de 100644
--- a/src/rebalance/cli/github.py
+++ b/src/rebalance/cli/github.py
@@ -61,7 +61,7 @@ def github_scan(
     days: int = typer.Option(30, help="Number of days to look back (supports 30-day A/B/C band classification)"),
     database: Path | None = DBOption(),
 ) -> None:
-    """Fetch GitHub activity and persist to database for use by github_balance MCP tool."""
+    """Fetch GitHub activity and persist to database for use by the hiqs_work_activity MCP tool."""
     from rebalance.ingest.github_scan import scan_and_store_github_activity
 
     try:
diff --git a/src/rebalance/cli/query.py b/src/rebalance/cli/query.py
index fa415eb..af66bae 100644
--- a/src/rebalance/cli/query.py
+++ b/src/rebalance/cli/query.py
@@ -115,7 +115,7 @@ def ask_cmd(
         typer.echo(f"\n--- Raw context ({result.elapsed_seconds}s) ---\n")
 
     if result.github_context:
-        typer.echo("\n--- GitHub Activity ---")
+        typer.echo("\n--- HiQS Work Activity ---")
         for g in result.github_context:
             if g.get("is_idle"):
                 typer.echo(f"  {g['project_name']:25s}  IDLE")
diff --git a/src/rebalance/ingest/github_scan.py b/src/rebalance/ingest/github_scan.py
index bdb4838..5350d10 100644
--- a/src/rebalance/ingest/github_scan.py
+++ b/src/rebalance/ingest/github_scan.py
@@ -738,13 +738,13 @@ def filter_ignored_repo_activity(result: GitHubScanResult, ignored_repos: list[s
 # ---------------------------------------------------------------------------
 
 
-def get_github_balance(
+def get_hiqs_work_activity(
     database_path: Path,
     project_repos: dict[str, list[str]],
     since_days: int = 14,
 ) -> list[dict[str, Any]]:
     """
-    Return GitHub activity summary per project using the project→repos mapping.
+    Return the HiQS work activity summary per project (canonical name, GH-316).
 
     Args:
         database_path:  Path to the SQLite database.
@@ -752,8 +752,10 @@ def get_github_balance(
         since_days:     How many days back to aggregate.
 
     Returns:
-        List of dicts with project_name, total_commits, prs_opened, prs_merged,
-        issues_opened, last_active_at, repos_touched.
+        List of dicts with project_name, repos_linked, repos_touched,
+        total_commits, prs_opened, prs_merged, issues_opened, last_active_at,
+        is_idle. This output contract is frozen — external consumers
+        (storyline experiment, Needle-fork adapter) read it as-is.
     """
     if not database_path.exists():
         return []
@@ -764,6 +766,11 @@ def get_github_balance(
         return fetch_github_balance(conn, project_repos, since_days=since_days)
 
 
+# Backwards-compatibility adapter (GH-316): github_balance is the deprecated
+# name of the HiQS work activity signal; kept so existing callers never break.
+get_github_balance = get_hiqs_work_activity
+
+
 # ---------------------------------------------------------------------------
 # Preflight discovery — GitHub repositories
 # ---------------------------------------------------------------------------
diff --git a/src/rebalance/ingest/querier.py b/src/rebalance/ingest/querier.py
index 3be3038..3a2b37d 100644
--- a/src/rebalance/ingest/querier.py
+++ b/src/rebalance/ingest/querier.py
@@ -196,11 +196,11 @@ def _gather_github_context(
     project_repos: dict[str, list[str]],
     since_days: int = 7,
 ) -> list[dict[str, Any]]:
-    """Per-project GitHub activity summary."""
-    from rebalance.ingest.github_scan import get_github_balance
+    """Per-project HiQS work activity summary."""
+    from rebalance.ingest.github_scan import get_hiqs_work_activity
 
     try:
-        return get_github_balance(
+        return get_hiqs_work_activity(
             database_path=database_path,
             project_repos=project_repos,
             since_days=since_days,
@@ -284,7 +284,7 @@ def _build_prompt(
 
     # GitHub activity
     if github_context:
-        lines = ["## GitHub Activity (last 7 days)"]
+        lines = ["## HiQS Work Activity (last 7 days)"]
         for g in github_context:
             if g.get("is_idle"):
                 lines.append(f"- {g['project_name']}: IDLE (no activity)")
diff --git a/src/rebalance/mcp/tools/projects.py b/src/rebalance/mcp/tools/projects.py
index 37205c1..881ee7d 100644
--- a/src/rebalance/mcp/tools/projects.py
+++ b/src/rebalance/mcp/tools/projects.py
@@ -5,7 +5,7 @@ from typing import Any
 
 from mcp.server.fastmcp import FastMCP
 
-from rebalance.ingest.github_scan import get_github_balance
+from rebalance.ingest.github_scan import get_hiqs_work_activity
 from rebalance.ingest.registry import get_projects
 
 
@@ -23,17 +23,28 @@ def register(mcp: FastMCP, database_path: Path) -> None:
         return get_projects(database_path, status=normalized or None)
 
     @mcp.tool()
-    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
+    def hiqs_work_activity(since_days: int = 30) -> list[dict[str, Any]]:
         """
-        Show GitHub activity balance across active projects.
+        Show HiQS work activity balance across active projects (canonical name).
 
-        Returns one row per project with commit/PR/issue counts over the last
-        `since_days` days.  Projects with no GitHub activity are flagged as
-        idle (is_idle=true).  Requires a prior `rebalance github-scan` run.
+        HiQS = High Quality Signals. Returns one row per project with
+        commit/PR/issue counts over the last `since_days` days.  Projects with
+        no HiQS work activity are flagged as idle (is_idle=true).  Requires a
+        prior `rebalance github-scan` run.
         """
         project_repos = _project_repos_map(database_path)
-        return get_github_balance(
+        return get_hiqs_work_activity(
             database_path=database_path,
             project_repos=project_repos,
             since_days=since_days,
         )
+
+    @mcp.tool()
+    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
+        """
+        Deprecated alias of `hiqs_work_activity` (GH-316).
+
+        Same implementation and identical response shape; use the canonical
+        `hiqs_work_activity` tool going forward.
+        """
+        return hiqs_work_activity(since_days=since_days)
diff --git a/tests/test_hiqs_work_activity_alias.py b/tests/test_hiqs_work_activity_alias.py
new file mode 100644
index 0000000..7303c44
--- /dev/null
+++ b/tests/test_hiqs_work_activity_alias.py
@@ -0,0 +1,83 @@
+"""GH-316: `hiqs_work_activity` is canonical; `github_balance` stays as a deprecated alias.
+
+Both MCP tool names must resolve through the real FastMCP server and return
+identical, fully-populated rows — and the frozen output contract (all nine
+keys) must not drift while the naming changes.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import json
+import tempfile
+import unittest
+from pathlib import Path
+
+from rebalance.ingest.db import (
+    db_connection,
+    ensure_github_schema,
+    ensure_project_schema,
+    ensure_schema,
+)
+from rebalance.ingest.github_scan import get_github_balance, get_hiqs_work_activity
+from rebalance.mcp.server import create_server
+
+FROZEN_OUTPUT_KEYS = {
+    "project_name",
+    "repos_linked",
+    "repos_touched",
+    "total_commits",
+    "prs_opened",
+    "prs_merged",
+    "issues_opened",
+    "last_active_at",
+    "is_idle",
+}
+
+
+def _call(server, name: str, args: dict):
+    """Invoke an MCP tool; FastMCP emits one JSON text block per list item."""
+    content, _ = asyncio.run(server.call_tool(name, args))
+    return [json.loads(block.text) for block in content]
+
+
+class HiqsWorkActivityAliasTests(unittest.TestCase):
+    def setUp(self) -> None:
+        self._tmp = tempfile.TemporaryDirectory()
+        self.addCleanup(self._tmp.cleanup)
+        self.db = Path(self._tmp.name) / "rebalance.db"
+        with db_connection(self.db, ensure_schema) as conn:
+            ensure_project_schema(conn)
+            ensure_github_schema(conn)
+            conn.execute(
+                "INSERT INTO project_registry (name, status, repos_json, tags_json, custom_fields_json)"
+                " VALUES ('Alpha', 'active', '[\"a/one\"]', '[]', '{}')"
+            )
+            conn.execute(
+                "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,"
+                " prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)"
+                " VALUES ('me', 'a/one', '2026-10-01', 7, 2, 3, 1, 0, 0, 0,"
+                " '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')"
+            )
+            conn.commit()
+
+    def test_python_alias_is_the_canonical_function(self) -> None:
+        self.assertIs(get_github_balance, get_hiqs_work_activity)
+
+    def test_both_mcp_tool_names_return_identical_populated_rows(self) -> None:
+        server = create_server(self.db)
+        canonical = _call(server, "hiqs_work_activity", {"since_days": 30})
+        alias = _call(server, "github_balance", {"since_days": 30})
+        self.assertEqual(canonical, alias)
+        self.assertEqual(len(canonical), 1)
+        row = canonical[0]
+        self.assertEqual(set(row), FROZEN_OUTPUT_KEYS)
+        self.assertEqual(row["project_name"], "Alpha")
+        self.assertEqual(row["total_commits"], 7)
+        self.assertEqual(row["prs_merged"], 1)
+        self.assertFalse(row["is_idle"])
+        self.assertEqual(row["repos_touched"], ["a/one"])
+
+
+if __name__ == "__main__":
+    unittest.main()
     1	"""GH-316: `hiqs_work_activity` is canonical; `github_balance` stays as a deprecated alias.
     2	
     3	Both MCP tool names must resolve through the real FastMCP server and return
     4	identical, fully-populated rows — and the frozen output contract (all nine
     5	keys) must not drift while the naming changes.
     6	"""
     7	
     8	from __future__ import annotations
     9	
    10	import asyncio
    11	import json
    12	import tempfile
    13	import unittest
    14	from pathlib import Path
    15	
    16	from rebalance.ingest.db import (
    17	    db_connection,
    18	    ensure_github_schema,
    19	    ensure_project_schema,
    20	    ensure_schema,
    21	)
    22	from rebalance.ingest.github_scan import get_github_balance, get_hiqs_work_activity
    23	from rebalance.mcp.server import create_server
    24	
    25	FROZEN_OUTPUT_KEYS = {
    26	    "project_name",
    27	    "repos_linked",
    28	    "repos_touched",
    29	    "total_commits",
    30	    "prs_opened",
    31	    "prs_merged",
    32	    "issues_opened",
    33	    "last_active_at",
    34	    "is_idle",
    35	}
    36	
    37	
    38	def _call(server, name: str, args: dict):
    39	    """Invoke an MCP tool; FastMCP emits one JSON text block per list item."""
    40	    content, _ = asyncio.run(server.call_tool(name, args))
    41	    return [json.loads(block.text) for block in content]
    42	
    43	
    44	class HiqsWorkActivityAliasTests(unittest.TestCase):
    45	    def setUp(self) -> None:
    46	        self._tmp = tempfile.TemporaryDirectory()
    47	        self.addCleanup(self._tmp.cleanup)
    48	        self.db = Path(self._tmp.name) / "rebalance.db"
    49	        with db_connection(self.db, ensure_schema) as conn:
    50	            ensure_project_schema(conn)
    51	            ensure_github_schema(conn)
    52	            conn.execute(
    53	                "INSERT INTO project_registry (name, status, repos_json, tags_json, custom_fields_json)"
    54	                " VALUES ('Alpha', 'active', '[\"a/one\"]', '[]', '{}')"
    55	            )
    56	            conn.execute(
    57	                "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,"
    58	                " prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)"
    59	                " VALUES ('me', 'a/one', '2026-10-01', 7, 2, 3, 1, 0, 0, 0,"
    60	                " '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')"
    61	            )
    62	            conn.commit()
    63	
    64	    def test_python_alias_is_the_canonical_function(self) -> None:
    65	        self.assertIs(get_github_balance, get_hiqs_work_activity)
    66	
    67	    def test_both_mcp_tool_names_return_identical_populated_rows(self) -> None:
    68	        server = create_server(self.db)
    69	        canonical = _call(server, "hiqs_work_activity", {"since_days": 30})
    70	        alias = _call(server, "github_balance", {"since_days": 30})
    71	        self.assertEqual(canonical, alias)
    72	        self.assertEqual(len(canonical), 1)
    73	        row = canonical[0]
    74	        self.assertEqual(set(row), FROZEN_OUTPUT_KEYS)
    75	        self.assertEqual(row["project_name"], "Alpha")
    76	        self.assertEqual(row["total_commits"], 7)
    77	        self.assertEqual(row["prs_merged"], 1)
    78	        self.assertFalse(row["is_idle"])
    79	        self.assertEqual(row["repos_touched"], ["a/one"])
    80	
    81	
    82	if __name__ == "__main__":
    83	    unittest.main()
     1	from __future__ import annotations
     2	
     3	from pathlib import Path
     4	from typing import Any
     5	
     6	from mcp.server.fastmcp import FastMCP
     7	
     8	from rebalance.ingest.github_scan import get_hiqs_work_activity
     9	from rebalance.ingest.registry import get_projects
    10	
    11	
    12	def _project_repos_map(database_path: Path) -> dict[str, list[str]]:
    13	    """Return {project_name: [repo, ...]} for all active projects."""
    14	    projects = get_projects(database_path, status="active")
    15	    return {p["name"]: p.get("repos") or [] for p in projects}
    16	
    17	
    18	def register(mcp: FastMCP, database_path: Path) -> None:
    19	    @mcp.tool()
    20	    def list_projects(status: str = "active") -> list[dict[str, Any]]:
    21	        """List projects from the local project_registry table."""
    22	        normalized = status.strip().lower() if status else ""
    23	        return get_projects(database_path, status=normalized or None)
    24	
    25	    @mcp.tool()
    26	    def hiqs_work_activity(since_days: int = 30) -> list[dict[str, Any]]:
    27	        """
    28	        Show HiQS work activity balance across active projects (canonical name).
    29	
    30	        HiQS = High Quality Signals. Returns one row per project with
    31	        commit/PR/issue counts over the last `since_days` days.  Projects with
    32	        no HiQS work activity are flagged as idle (is_idle=true).  Requires a
    33	        prior `rebalance github-scan` run.
    34	        """
    35	        project_repos = _project_repos_map(database_path)
    36	        return get_hiqs_work_activity(
    37	            database_path=database_path,
    38	            project_repos=project_repos,
    39	            since_days=since_days,
    40	        )
    41	
    42	    @mcp.tool()
    43	    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
    44	        """
    45	        Deprecated alias of `hiqs_work_activity` (GH-316).
    46	
    47	        Same implementation and identical response shape; use the canonical
    48	        `hiqs_work_activity` tool going forward.
    49	        """
    50	        return hiqs_work_activity(since_days=since_days)
   730	        kept[repo_full_name] = activity
   731	
   732	    result.repo_activity = kept
   733	    return sorted(skipped)
   734	
   735	
   736	# ---------------------------------------------------------------------------
   737	# Balance query — used by MCP tool
   738	# ---------------------------------------------------------------------------
   739	
   740	
   741	def get_hiqs_work_activity(
   742	    database_path: Path,
   743	    project_repos: dict[str, list[str]],
   744	    since_days: int = 14,
   745	) -> list[dict[str, Any]]:
   746	    """
   747	    Return the HiQS work activity summary per project (canonical name, GH-316).
   748	
   749	    Args:
   750	        database_path:  Path to the SQLite database.
   751	        project_repos:  {project_name: [repo_full_name, ...]} mapping.
   752	        since_days:     How many days back to aggregate.
   753	
   754	    Returns:
   755	        List of dicts with project_name, repos_linked, repos_touched,
   756	        total_commits, prs_opened, prs_merged, issues_opened, last_active_at,
   757	        is_idle. This output contract is frozen — external consumers
   758	        (storyline experiment, Needle-fork adapter) read it as-is.
   759	    """
   760	    if not database_path.exists():
   761	        return []
   762	
   763	    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_github_balance
   764	
   765	    with db_connection(database_path, ensure_github_schema) as conn:
   766	        return fetch_github_balance(conn, project_repos, since_days=since_days)
   767	
   768	
   769	# Backwards-compatibility adapter (GH-316): github_balance is the deprecated
   770	# name of the HiQS work activity signal; kept so existing callers never break.
   771	get_github_balance = get_hiqs_work_activity
   772	
   773	
   774	# ---------------------------------------------------------------------------
   775	# Preflight discovery — GitHub repositories
   776	# ---------------------------------------------------------------------------
   777	
   778	
   779	@dataclass
   780	class RepoCandidate:
   781	    """A repository discovered from recent GitHub activity."""
   782	
   783	    repo_full_name: str
   784	    last_active_at: str | None
   785	    activity_score: int  # Total events in scan window
   786	    commit_count: int
   787	    bands: list[str] = field(default_factory=list)  # e.g. ["A", "B", "C"]
   788	
   789	
   790	def discover_repos_from_activity(
   791	    token: str,
   792	    days: int = 30,
   793	) -> list[RepoCandidate]:
   794	    """
   795	    Scan GitHub activity for the past N days and return discovered repositories
src/rebalance/ingest/note_builder.py:374:        "- [Recent GitHub Activity](#recent-github-activity)",
src/rebalance/ingest/note_builder.py:419:    lines.extend(["", "## Recent GitHub Activity"])
src/rebalance/mcp/tools/projects.py:8:from rebalance.ingest.github_scan import get_hiqs_work_activity
src/rebalance/mcp/tools/projects.py:28:        Show HiQS work activity balance across active projects (canonical name).
src/rebalance/mcp/tools/projects.py:32:        no HiQS work activity are flagged as idle (is_idle=true).  Requires a
src/rebalance/mcp/tools/projects.py:36:        return get_hiqs_work_activity(
src/rebalance/mcp/tools/projects.py:43:    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
src/rebalance/ingest/db/schema.py:308:    """Daily per-repo/login activity rollups (powers ``github_balance``)."""
src/rebalance/ingest/db/queries.py:336:def fetch_github_balance(
src/rebalance/ingest/db/queries.py:1436:    "fetch_github_balance",
src/rebalance/ingest/db/__init__.py:32:    fetch_github_balance,
src/rebalance/ingest/db/__init__.py:70:    "fetch_github_balance",
src/rebalance/ingest/github_scan.py:741:def get_hiqs_work_activity(
src/rebalance/ingest/github_scan.py:747:    Return the HiQS work activity summary per project (canonical name, GH-316).
src/rebalance/ingest/github_scan.py:763:    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_github_balance
src/rebalance/ingest/github_scan.py:766:        return fetch_github_balance(conn, project_repos, since_days=since_days)
src/rebalance/ingest/github_scan.py:769:# Backwards-compatibility adapter (GH-316): github_balance is the deprecated
src/rebalance/ingest/github_scan.py:770:# name of the HiQS work activity signal; kept so existing callers never break.
src/rebalance/ingest/github_scan.py:771:get_github_balance = get_hiqs_work_activity
src/rebalance/ingest/querier.py:199:    """Per-project HiQS work activity summary."""
src/rebalance/ingest/querier.py:200:    from rebalance.ingest.github_scan import get_hiqs_work_activity
src/rebalance/ingest/querier.py:203:        return get_hiqs_work_activity(
   340	) -> list[dict[str, Any]]:
   341	    """Return GitHub activity balance per project using canonical repo identity.
   342	
   343	    Collapses mirror-org spellings into one canonical entity and reconciles
   344	    snapshot rows latest-scan-wins (SOP §6), so projects listing either or both
   345	    spellings of a repo get complete, undoubled stats.
   346	    """
   347	    since_date = (now_utc() - timedelta(days=since_days)).strftime(
   348	        "%Y-%m-%d"
   349	    )  # READ-LAYER-OK: P1 read layer destination for since_cutoff (GH-150)
   350	    alias_map = _get_alias_map()
   351	
   352	    canonical_stats: dict[str, dict[str, Any]] = {}
   353	    for row in _latest_activity_snapshots(conn, since_date, alias_map):
   354	        canon_key = _canonical_lower(row["repo_full_name"], alias_map)
   355	        if canon_key not in canonical_stats:
   356	            canonical_stats[canon_key] = {
   357	                "commits": 0,
   358	                "pushes": 0,
   359	                "prs_opened": 0,
   360	                "prs_merged": 0,
   361	                "issues_opened": 0,
   362	                "issue_comments": 0,
   363	                "reviews": 0,
   364	                "last_active_at": None,
   365	            }
   366	        cs = canonical_stats[canon_key]
   367	        cs["commits"] += row["commits"] or 0
   368	        cs["pushes"] += row["pushes"] or 0
   369	        cs["prs_opened"] += row["prs_opened"] or 0
   370	        cs["prs_merged"] += row["prs_merged"] or 0
   371	        cs["issues_opened"] += row["issues_opened"] or 0
   372	        cs["issue_comments"] += row["issue_comments"] or 0
   373	        cs["reviews"] += row["reviews"] or 0
   374	        la = row["last_active_at"]
   375	        if la and (cs["last_active_at"] is None or la > cs["last_active_at"]):
   376	            cs["last_active_at"] = la
   377	
   378	    results: list[dict[str, Any]] = []
   379	    for project_name, repos in project_repos.items():
   380	        total_commits = 0
   381	        total_prs_opened = 0
   382	        total_prs_merged = 0
   383	        total_issues = 0
   384	        repos_touched: list[str] = []
   385	        last_active: str | None = None
   386	
   387	        seen_canon_repos: set[str] = set()
   388	        for repo in repos:
   389	            canon_repo = _canonical_lower(repo, alias_map)
   390	            if canon_repo in seen_canon_repos:
   391	                continue
   392	            seen_canon_repos.add(canon_repo)
   393	            stats = canonical_stats.get(canon_repo)
   394	            if not stats:
   395	                continue
   396	            repos_touched.append(repo)
   397	            total_commits += stats.get("commits") or 0
   398	            total_prs_opened += stats.get("prs_opened") or 0
   399	            total_prs_merged += stats.get("prs_merged") or 0
   400	            total_issues += stats.get("issues_opened") or 0
   401	            la = stats.get("last_active_at")
   402	            if la and (last_active is None or la > last_active):
   403	                last_active = la
   404	
   405	        results.append(
   406	            {
   407	                "project_name": project_name,
   408	                "repos_linked": repos,
   409	                "repos_touched": repos_touched,
   410	                "total_commits": total_commits,
   411	                "prs_opened": total_prs_opened,
   412	                "prs_merged": total_prs_merged,
   413	                "issues_opened": total_issues,
   414	                "last_active_at": last_active,
   415	                "is_idle": len(repos_touched) == 0,
   416	            }
   417	        )
   418	
   419	    results.sort(key=lambda x: (x["is_idle"], -(len(x["repos_touched"]))), reverse=False)
   420	    return results

exec
/bin/zsh -lc "rg -n 'freeze|now_utc|autouse|datetime' tests/conftest.py
rg -n 'get_github_balance|github_balance' --glob '*.py' --glob '*.json' --glob '*.toml'
nl -ba src/rebalance/mcp/server.py | head -65
nl -ba tests/conftest.py | head -200
nl -ba TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md | head -28
nl -ba src/rebalance/cli/github.py | sed -n '60,78p'
rg -n 'fetch_org_activity' src/rebalance/ingest/note_builder.py
cat SOP.md | head -140" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
 succeeded in 0ms:
131:@pytest.fixture(autouse=True)
145:@pytest.fixture(autouse=True)
170:@pytest.fixture(autouse=True, scope="session")
195:@pytest.fixture(autouse=True, scope="session")
manifest.json:78:      "name": "github_balance",
src/rebalance/mcp/tools/projects.py:43:    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
src/rebalance/ingest/db/schema.py:308:    """Daily per-repo/login activity rollups (powers ``github_balance``)."""
src/rebalance/ingest/db/queries.py:336:def fetch_github_balance(
src/rebalance/ingest/db/queries.py:1436:    "fetch_github_balance",
src/rebalance/ingest/db/__init__.py:32:    fetch_github_balance,
src/rebalance/ingest/db/__init__.py:70:    "fetch_github_balance",
src/rebalance/ingest/github_scan.py:763:    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_github_balance
src/rebalance/ingest/github_scan.py:766:        return fetch_github_balance(conn, project_repos, since_days=since_days)
src/rebalance/ingest/github_scan.py:769:# Backwards-compatibility adapter (GH-316): github_balance is the deprecated
src/rebalance/ingest/github_scan.py:771:get_github_balance = get_hiqs_work_activity
tests/test_hiqs_work_activity_alias.py:1:"""GH-316: `hiqs_work_activity` is canonical; `github_balance` stays as a deprecated alias.
tests/test_hiqs_work_activity_alias.py:22:from rebalance.ingest.github_scan import get_github_balance, get_hiqs_work_activity
tests/test_hiqs_work_activity_alias.py:65:        self.assertIs(get_github_balance, get_hiqs_work_activity)
tests/test_hiqs_work_activity_alias.py:70:        alias = _call(server, "github_balance", {"since_days": 30})
tests/test_queries_mirror_invariance.py:264:        "fetch_github_balance": {
tests/test_queries_mirror_invariance.py:531:        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
tests/test_queries_mirror_invariance.py:565:        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
     1	from __future__ import annotations
     2	
     3	import logging
     4	from pathlib import Path
     5	
     6	from mcp.server.fastmcp import FastMCP
     7	
     8	from rebalance.mcp.tools import calendar, hygiene, index, onboarding, projects, retrieval, sleuth
     9	
    10	logger = logging.getLogger(__name__)
    11	
    12	
    13	def create_server(database_path: Path) -> FastMCP:
    14	    mcp = FastMCP("rebalance")
    15	    projects.register(mcp, database_path)
    16	    onboarding.register(mcp, database_path)
    17	    retrieval.register(mcp, database_path)
    18	    calendar.register(mcp, database_path)
    19	    index.register(mcp, database_path)
    20	    hygiene.register(mcp, database_path)
    21	    sleuth.register(mcp, database_path)
    22	    return mcp
    23	
    24	
    25	def main() -> None:
    26	    from rebalance.paths import DatabaseNotFoundError, canonical_database_path, resolve_database_path
    27	
    28	    try:
    29	        database_path = resolve_database_path()
    30	    except DatabaseNotFoundError:
    31	        # First run: no database exists yet. Create the canonical path so
    32	        # MCP-driven onboarding can proceed — the onboarding tools need
    33	        # the server to be running before any data exists.
    34	        from rebalance.ingest.db.connection import get_connection
    35	
    36	        database_path = canonical_database_path()
    37	        get_connection(database_path).close()
    38	        logger.info("Created empty database at %s", database_path)
    39	    server = create_server(database_path=database_path)
    40	    server.run()
    41	
    42	
    43	if __name__ == "__main__":
    44	    main()
     1	"""Shared pytest fixtures for the rebalance-OS test suite."""
     2	
     3	import importlib.machinery
     4	import os
     5	import sys
     6	import types
     7	
     8	import pytest
     9	
    10	from rebalance.lib.metal_probe import metal_available
    11	
    12	# GH-225: stand in for MLX when it is not installed, so the MLX tests can run anywhere.
    13	#
    14	# mlx is Apple-Silicon-only and CI runs ubuntu-latest, so `import mlx` there raises
    15	# ModuleNotFoundError — 2 failures and 6 fixture errors across tests/test_mlx_cache_cap.py
    16	# and tests/test_mlx_instrumentation.py. It is equally absent from a local venv built
    17	# without the `embeddings` extra, which is what `pip install -e ".[calendar,server]"` gives.
    18	#
    19	# Those tests do not need MLX to work. Every one of them replaces it with a MagicMock or a
    20	# hand-written double (MockMLXCore / MockMLXCoreForCap); the real `import mlx` exists only to
    21	# obtain the module OBJECT that patch.object() then rebinds. The two test NAMES that read like
    22	# they need a missing MLX -- test_degrades_safely_when_mlx_unavailable,
    23	# test_instrumentation_degrades_when_mlx_absent -- are about MLX's methods RAISING
    24	# (RuntimeError("no Metal device")) and about telemetry not becoming a new crash path. Neither
    25	# is about the package being uninstalled, so skipping them on CI would remove real coverage of
    26	# the degradation paths rather than deferring an environment problem.
    27	#
    28	# `core` is bound as an ATTRIBUTE of the parent, not merely registered in sys.modules. This is
    29	# load-bearing and is documented in test_mlx_instrumentation.py:13-17: `import mlx.core as mx`
    30	# resolves through getattr(mlx, "core"), so a sys.modules-only stub is ignored, real MLX gets
    31	# exercised, and the mock's counters silently stay at zero.
    32	#
    33	# Guarded by ImportError so a machine WITH MLX (this project's target platform) keeps testing
    34	# against the real package; the stub is a fallback, never an override.
    35	# Each stub carries a real `__spec__`. `types.ModuleType` leaves it None, and a
    36	# sys.modules entry with `__spec__ is None` makes `importlib.util.find_spec()`
    37	# raise `ValueError: mlx.__spec__ is None` rather than return None. Nothing
    38	# called find_spec on "mlx" until GH-81 put sentence-transformers in the CI
    39	# install: it pulls `transformers`, whose utils/generic.py runs
    40	# `is_mlx_available()` at import time, which is that exact call. The three
    41	# tests/test_embedder*.py tests died on it. With a spec present, transformers
    42	# proceeds to `importlib.metadata.version("mlx")`, gets PackageNotFoundError,
    43	# and correctly concludes MLX is absent — which is the truth on CI.
    44	try:  # pragma: no cover - depends on the host platform
    45	    import mlx  # noqa: F401
    46	    import mlx.core  # noqa: F401
    47	except ImportError:  # pragma: no cover - the CI / no-extras path
    48	    _mlx_stub = types.ModuleType("mlx")
    49	    _mlx_core_stub = types.ModuleType("mlx.core")
    50	    # submodule_search_locations marks "mlx" as a package, so "mlx.core" is a
    51	    # coherent submodule name rather than an attribute of a plain module.
    52	    _mlx_stub.__spec__ = importlib.machinery.ModuleSpec("mlx", loader=None, is_package=True)
    53	    _mlx_core_stub.__spec__ = importlib.machinery.ModuleSpec("mlx.core", loader=None)
    54	    _mlx_stub.core = _mlx_core_stub
    55	    sys.modules.setdefault("mlx", _mlx_stub)
    56	    sys.modules.setdefault("mlx.core", _mlx_core_stub)
    57	
    58	#: GH-178 quarantine. These failed at GH-124's own final commit (536de83,
    59	#: 2026-07-11) and were merged red — nothing caught it because CI did not run on
    60	#: `development` until GH-177. Verified to fail identically on macOS and on clean
    61	#: Ubuntu CI, so they are real product bugs, not environment artifacts.
    62	#:
    63	#: They are quarantined rather than deleted so CI regains signal NOW: a red run
    64	#: means *new* breakage instead of the same 10 forever, which is the state that
    65	#: trains people to ignore CI. This list must shrink to empty — every entry is a
    66	#: real defect in commit-threshold auto-promotion.
    67	#:
    68	#: DO NOT add to this list to make a red build green. Fix the test or the code.
    69	KNOWN_FAILING_GH178 = {
    70	    "tests/test_auto_promote.py::AutoPromoteTests::test_activity_commits_sum_across_scan_dates",
    71	    "tests/test_auto_promote.py::AutoPromoteTests::test_auto_promoted_row_survives_activity_inference_sync",
    72	    "tests/test_auto_promote.py::AutoPromoteTests::test_cloud_agent_commits_count_toward_threshold",
    73	    "tests/test_auto_promote.py::AutoPromoteTests::test_direct_push_commits_count_not_just_pr_commits",
    74	    "tests/test_auto_promote.py::AutoPromoteTests::test_idempotent_rerun_does_not_duplicate",
    75	    "tests/test_auto_promote.py::AutoPromoteTests::test_name_collision_disambiguates_instead_of_overwriting",
    76	    "tests/test_auto_promote.py::AutoPromoteTests::test_operator_push_and_bot_commits_combine",
    77	    "tests/test_auto_promote.py::AutoPromoteTests::test_promotes_repo_at_threshold",
    78	    "tests/test_auto_promote.py::AutoPromoteTests::test_promotion_fires_auth_log_alert",
    79	    "tests/test_project_inference.py::ProjectInferenceTests::test_infers_binoid_from_github_and_ltvera_from_calendar_only",
    80	}
    81	
    82	
    83	# GH-250 / GH-42: `metal_available()` (probes for a usable Metal device
    84	# OUT OF PROCESS, since MLX aborts rather than raising when none is reachable)
    85	# now lives in rebalance.lib.metal_probe so both this fixture and the
    86	# production embedder (src/rebalance/ingest/embedder.py) share one
    87	# implementation instead of drifting copies. See that module's docstring for
    88	# the full abort-vs-raise explanation.
    89	
    90	
    91	def pytest_configure(config):
    92	    config.addinivalue_line(
    93	        "markers",
    94	        "requires_metal: needs a real Metal device. Skipped when MLX cannot "
    95	        "create one — probed out-of-process because MLX aborts rather than "
    96	        "raising, which no in-test guard can catch (GH-250).",
    97	    )
    98	
    99	
   100	def pytest_collection_modifyitems(config, items):
   101	    """Mark the GH-178 quarantine xfail, non-strict; skip Metal-only tests.
   102	
   103	    Non-strict on purpose: if one starts passing the run stays green (XPASS) and
   104	    the entry is simply stale. Strict would turn someone else's unrelated fix
   105	    into a red build, which is the opposite of the point.
   106	    """
   107	    # Probe lazily: only pay for the subprocess if something actually asks.
   108	    metal_skip = None
   109	    for item in items:
   110	        if item.nodeid in KNOWN_FAILING_GH178:
   111	            item.add_marker(
   112	                pytest.mark.xfail(
   113	                    reason="GH-178: known-failing since GH-124 (536de83); quarantined by GH-177",
   114	                    strict=False,
   115	                )
   116	            )
   117	        if item.get_closest_marker("requires_metal") is not None:
   118	            if metal_skip is None:
   119	                metal_skip = (
   120	                    pytest.mark.skip(
   121	                        reason="no usable Metal device (probed out-of-process; "
   122	                        "MLX would abort this run rather than raise) — GH-250"
   123	                    )
   124	                    if not metal_available()
   125	                    else False
   126	                )
   127	            if metal_skip is not False:
   128	                item.add_marker(metal_skip)
   129	
   130	
   131	@pytest.fixture(autouse=True)
   132	def _disable_job_guard(monkeypatch):
   133	    """Turn off the GH-172 embedding guard for the whole suite.
   134	
   135	    The guard takes a real ``flock`` and starts a memory watchdog whose
   136	    ``preflight()`` REFUSES to start when the machine is low on available
   137	    memory. Left on, tests that call ``embed_pending``/``embed_chunks`` would
   138	    fail spuriously on a busy machine and serialise against any real ingest
   139	    running on the same box. Guard behaviour itself is covered explicitly in
   140	    ``tests/test_job_guard_wiring.py``, which re-enables it per-test.
   141	    """
   142	    monkeypatch.setenv("REBALANCE_JOB_GUARD", "0")
   143	
   144	
   145	@pytest.fixture(autouse=True)
   146	def _isolate_secret_store(tmp_path_factory):
   147	    """Redirect the out-of-repo secret store to a fresh tmp dir for EACH test.
   148	
   149	    The GitHub/Figma dual-store helpers (`config.py`) now write/read the
   150	    permission-enforced secret store at `~/.config/rebalance-os/secrets`. Without
   151	    isolation, suite runs pollute the operator's real secret dir and — because
   152	    secret files are last-write-wins (unlike the append-only auth log) — leak
   153	    values across tests. Per-test scope gives every test a clean store.
   154	    `secret_store.secret_store_root()` honors `REBALANCE_SECRET_STORE_DIR`; tests
   155	    that need a specific path override `secret_store.SECRET_STORE_DIR` (module
   156	    seam), which takes precedence.
   157	    """
   158	    store_dir = tmp_path_factory.mktemp("secret_store")
   159	    previous = os.environ.get("REBALANCE_SECRET_STORE_DIR")
   160	    os.environ["REBALANCE_SECRET_STORE_DIR"] = str(store_dir)
   161	    try:
   162	        yield
   163	    finally:
   164	        if previous is None:
   165	            os.environ.pop("REBALANCE_SECRET_STORE_DIR", None)
   166	        else:
   167	            os.environ["REBALANCE_SECRET_STORE_DIR"] = previous
   168	
   169	
   170	@pytest.fixture(autouse=True, scope="session")
   171	def _isolate_auth_log(tmp_path_factory):
   172	    """Redirect the unified auth-activity log to a throwaway tmp dir for the
   173	    whole test session.
   174	
   175	    Several code paths (gmail/calendar `_load_credentials`, the 403 scope probe,
   176	    etc.) call `auth_log` helpers that append to `temp/logs/auth_activity.jsonl`.
   177	    Without this, running the suite injects fake `token_missing` /
   178	    `scope_insufficient` events into the *real* log, which then shows up as false
   179	    failures in `rebalance doctor`. `auth_log._log_dir()` honors
   180	    `REBALANCE_AUTH_LOG_DIR`, so pointing it at a tmp dir keeps the suite from
   181	    touching the repo's log.
   182	    """
   183	    log_dir = tmp_path_factory.mktemp("auth_log")
   184	    previous = os.environ.get("REBALANCE_AUTH_LOG_DIR")
   185	    os.environ["REBALANCE_AUTH_LOG_DIR"] = str(log_dir)
   186	    try:
   187	        yield
   188	    finally:
   189	        if previous is None:
   190	            os.environ.pop("REBALANCE_AUTH_LOG_DIR", None)
   191	        else:
   192	            os.environ["REBALANCE_AUTH_LOG_DIR"] = previous
   193	
   194	
   195	@pytest.fixture(autouse=True, scope="session")
   196	def _disable_keyring():
   197	    """Route every keyring helper to its no-op path for the whole session.
   198	
   199	    `config.py` reads credentials with `keyring.get_password(KEYRING_SERVICE, key)`
   200	    (`KEYRING_SERVICE = "rebalance-os"`). On macOS that is the real login Keychain,
     1	# GH-316 plan consult — round 1 (verbatim)
     2	
     3	Codex gpt-6-astra via relay-automation/consult.sh, read-only worktree, 2026-10-03.
     4	Verdict: CHANGES — approve after the small plan corrections (all accepted; see the
     5	QA log in PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md). Committed verbatim
     6	inside a fenced block: the transcript's relative links belong to the advisor's
     7	throwaway worktree and must not be repointed (GH-88 rationale).
     8	
     9	## Prompt
    10	
    11	```
    12	# Plan review request — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter
    13	
    14	You are reviewing a PLAN (pre-implementation) for a small, operator-directed naming change in the rebalanceOS repo. Grade against the stated requirements and commensurate complexity — this is a labels-and-aliases change, not a schema migration; do not demand enterprise machinery.
    15	
    16	## Task (issue #316, abridged)
    17	
    18	Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project GitHub work-activity signal:
    19	
    20	1. REQUIRED backwards-compatibility adapter: MCP tool `github_balance` stays registered + functional (docstring marks it deprecated alias); new canonical MCP tool `hiqs_work_activity`; Python `get_hiqs_work_activity()` canonical with `get_github_balance` kept as alias.
    21	2. Contract freeze: SQLite table `github_activity`, SQL reader `fetch_github_balance`, and ALL output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by external experiments (issue #300, Needle-fork#79).
    22	3. Operator-facing strings presenting the SIGNAL relabel to "HiQS work activity"; strings describing ingestion of the raw GitHub data source stay literal.
    23	
    24	## Plan doc (review this)
    25	
    26	- `PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md` — includes Phase 0 prior-art with file:line cites, requirements, ordered smallest surface, non-goals, risks, test/gate.
    27	
    28	## Source paths to verify claims against
    60	    token: str = typer.Option(..., envvar="GITHUB_TOKEN", help="GitHub Personal Access Token"),
    61	    days: int = typer.Option(30, help="Number of days to look back (supports 30-day A/B/C band classification)"),
    62	    database: Path | None = DBOption(),
    63	) -> None:
    64	    """Fetch GitHub activity and persist to database for use by the hiqs_work_activity MCP tool."""
    65	    from rebalance.ingest.github_scan import scan_and_store_github_activity
    66	
    67	    try:
    68	        db_path = resolve_database_path(database)
    69	    except DatabaseNotFoundError as exc:
    70	        typer.echo(str(exc))
    71	        raise typer.Exit(2) from exc
    72	    typer.echo(f"Scanning GitHub activity for last {days} days...")
    73	    result, skipped_repos = scan_and_store_github_activity(db_path, token=token, since_days=days)
    74	    typer.echo(
    75	        f"Done: login={result.login}, events={result.total_events}, "
    76	        f"repos={len(result.repo_activity)}, skipped={len(skipped_repos)}, stored to {db_path}"
    77	    )
    78	
49:    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_org_activity
52:        return fetch_org_activity(conn, since_days=since_days, ignored_repos=get_github_ignored_repos())
# SOP — Standard Operating Procedure

Do not store any credentials or secrets in this file, other repo files, or any PII in public facing GH issues. The same rule covers machine-specific absolute paths (e.g. a deploy runtime folder's real location) — keep those in your own gitignored `temp/RUNTIME.md`, never in a tracked file. See the pattern in `AGENTS.md` § "Deploy runtime folder".

This document codifies how work in this repo gets **evidenced**. It is written for
whoever picks up the next task, human or model, and it is binding on both.

---

## 1. The rule

> **Verified beats plausible. A claim whose evidence is unpublished is an assertion.**

If you state that something was measured — in a GitHub issue, a PR body, a commit
message, `ROADMAP.md`, a code comment, or a reply to the operator — the measurement
must be retained in [`TESTS-RESULTS/`](TESTS-RESULTS) where a reader can check it
without access to your machine.

This exists because it has already failed here. A retrieval change was tested on 5
queries with no ground truth, the result looked negative, the improvement was
reverted, and the conclusion was reported as settled. It was noise. Re-run properly
(39 queries, hand-established targets, paired significance test) the same change won
decisively — 14 improved, 0 regressed, p=0.0137 — and the earlier call had been
suppressing a real fix for weeks. See
[`TESTS-RESULTS/2026-08-20+GH-81/`](TESTS-RESULTS/2026-08-20+GH-81).

The lesson is not "test more." It is: **a small unverifiable test is worse than no
test**, because it manufactures false confidence and then gets cited.

## 2. When a campaign is required

Run one — and publish it — before any of these:

- **Choosing or replacing a model, library, or algorithm** where the claim is that one performs better than another.
- **Reverting or rejecting a change on empirical grounds.** "I tried it, it didn't help" is a claim and needs the same evidence as "I tried it, it helped." This is the specific failure above.
- **Any performance, retrieval-quality, or accuracy number** that will appear in an issue, PR, or doc.
- **Declaring a system healthy or a defect fixed** where the proof is behavioural rather than a passing unit test.

Not required for: ordinary code changes covered by the test suite, refactors with no
behavioural claim, or documentation.

**If it is not worth a campaign, it is not worth an empirical claim.** Say "not
measured" instead. That is a legitimate and useful thing to write.

## 3. How to run one

### 3.1 Write the protocol first, and freeze it

Before generating a single number, write down: the question, what is being compared,
the dataset, the metrics, and — critically — **the decision rule**: what result would
lead to which action, including the results that would embarrass the current design.

Put it in `PROJECT/2-WORKING/`. A decision rule written after seeing results is not a
decision rule; it is a rationalisation.

### 3.2 Establish ground truth by hand

For retrieval, ranking, or classification work, the correct answer must be determined
by a person **reading the artifact** — not by another model, and not by the system
under test. Discard any item whose correct answer cannot be established; do not guess
it. Record how many you discarded.

Watch for near-duplicates. If several items would legitimately satisfy the same query,
single-target scoring is invalid and will silently penalise every system equally
while looking like a real measurement.

### 3.3 Get the protocol reviewed before running it

Use `/relay-xyz` (or an equivalent independent review) on the **protocol**, not just
the results. Review after the fact can only rationalise; review before can still
change the experiment.

On GH-81 it changed the experiment twice, and one of those changes is why the
headline finding was detectable at all — the original significance rule would have
returned "no measurable difference, keep the incumbent" almost regardless of the
data. Transcripts: [`qa/`](TESTS-RESULTS/2026-08-20+GH-81/qa).

### 3.4 Include a dumb baseline

Always score the boring option — keyword search, the previous version, a constant, a
coin flip. Without it you cannot tell "our system is good" from "this task is easy."
On GH-81 the shipped configuration scored **below plain SQLite full-text search**,
which is not a fact any amount of comparing sophisticated options to each other would
have surfaced.

### 3.5 Use a paired test when systems answer the same inputs

Comparing independent per-system confidence intervals throws away the pairing and
buries real effects under between-item difficulty. Use a paired test (Wilcoxon
signed-rank for bounded/tied metrics), correct for multiple comparisons (Holm), and
report **effect size alongside p** — a significant tiny effect is a real and
reportable outcome.

Report "no significant difference" plainly when that is the answer. It is a result.

### 3.6 Prove the instrument constrains

Before trusting a new test, **make it fail on purpose.** Revert the fix and confirm
the test goes red. A test that passes against broken code measures nothing, and a
green suite full of them is worse than no suite because it is trusted.

### 3.7 Publish

Follow [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md): campaign folder named
`YYYY-MM-DD+GH-<issue>`, `SUMMARY.md`, the primitive `.jsonl`, the scripts as run,
the QA transcripts verbatim, the raw console output.

Every aggregate in the summary must be recomputable from the primitive records. If it
isn't, the primitive is incomplete or the number is unsupported.

## 4. Reporting

### 4.1 Threats to validity are mandatory

Every `SUMMARY.md` ends with what would make the result wrong: sample size, sampling
bias, lack of blinding, deviations from protocol, what was *not* measured. Write them
even when — especially when — the result came out the way you hoped.

State deviations explicitly. On GH-81, one model ran at a reduced context window
because the full one exhausted GPU memory; that is recorded, along with the check
showing it did not explain the outcome.

### 4.2 Retract loudly

If a campaign overturns an earlier published conclusion, **say so in the same place
the original was published**, link both, and state what was wrong with the first
attempt. Do not quietly supersede it. Someone is relying on the old claim.

### 4.3 Do not overstate scope

Say what was measured, not what it implies. GH-81 measured the vector retriever in
isolation, while production fuses vector and lexical search — so "no model beat
keyword search" was a component-level result and would have been badly misleading
stated as a system-level one. That correction is in the summary because it was caught
before publication; catching it after would have meant a retraction under §4.2.

## 5. Naming things precisely

Ambiguous names cost real time and cause real errors. When identifying a model,
library, or version, use the **full identifier**, and verify it against the artifact

exec
/bin/zsh -lc "nl -ba manifest.json | sed -n '60,90p'
nl -ba src/rebalance/ingest/db/queries.py | sed -n '270,340p'
rg -n '/Users/|/private/|token|secret' TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md | head -25
command -v python3
ls -d .venv /opt/homebrew/bin/python* 2>/dev/null
sed -n '1,55p' /Users/noelsaw/.codex/skills/review-code/SKILL.md" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
 succeeded in 0ms:
    60	    },
    61	    {
    62	      "name": "search_vault",
    63	      "description": "Full-text keyword search over vault files via TF-IDF index"
    64	    },
    65	    {
    66	      "name": "semantic_query",
    67	      "description": "Vector search across the unified semantic index (vault chunks + GitHub corpus)"
    68	    },
    69	    {
    70	      "name": "get_next_actions",
    71	      "description": "Read the latest persisted 'what should we work on next' ranking without recomputing it"
    72	    },
    73	    {
    74	      "name": "list_projects",
    75	      "description": "List projects from the local project_registry table"
    76	    },
    77	    {
    78	      "name": "github_balance",
    79	      "description": "Show GitHub activity balance across active projects"
    80	    },
    81	    {
    82	      "name": "github_release_readiness",
    83	      "description": "Infer current milestone/release readiness from the local GitHub corpus"
    84	    },
    85	    {
    86	      "name": "github_close_candidates",
    87	      "description": "Suggest open issues that likely map to merged PRs and may be ready to close"
    88	    },
    89	    {
    90	      "name": "diagnose_repo",
   270	        optional = ",".join(
   271	            name if name in columns else f"NULL AS {name}" for name in ("labels_json", "state_reason", "title")
   272	        )
   273	        rows = []
   274	        for offset in range(0, len(spellings), 200):
   275	            if time.monotonic() >= deadline:
   276	                raise TimeoutError("native-read-deadline")
   277	            chunk = spellings[offset : offset + 200]
   278	            predicates = " OR ".join("(lower(repo_full_name)=? AND number=?)" for _ in chunk)
   279	            params = tuple(value for pair in chunk for value in pair)
   280	            selected = conn.execute(
   281	                f"SELECT repo_full_name,item_type,number,state,html_url,updated_at,fetched_at,created_at,{optional} "
   282	                f"FROM github_items WHERE item_type='issue' AND ({predicates}) LIMIT 2001",
   283	                params,
   284	            ).fetchall()
   285	            if len(selected) > 2000:
   286	                raise ValueError("native-row-cap")
   287	            rows.extend(selected)
   288	            if len(rows) > 2000:
   289	                raise ValueError("native-row-cap")
   290	        if time.monotonic() >= deadline:
   291	            raise TimeoutError("native-read-deadline")
   292	        # Status uses the newest *observation*, not an old item's update text.
   293	        # Keep existing general-query resolution semantics unchanged.
   294	        newest = {}
   295	        ranks = {}
   296	        for cached in rows:
   297	            key = (_canonical_lower(cached["repo_full_name"], aliases), cached["number"])
   298	            parsed = parse_iso(cached["fetched_at"], force_utc=False)
   299	            rank = parsed.timestamp() if parsed and parsed.tzinfo else float("-inf")
   300	            if key not in ranks or rank > ranks[key]:
   301	                ranks[key], newest[key] = rank, [cached]
   302	            elif rank == ranks[key]:
   303	                newest[key].append(cached)
   304	        conflicting = {
   305	            key
   306	            for key, copies in newest.items()
   307	            if len({(r["state"], r["labels_json"], r["state_reason"]) for r in copies}) > 1
   308	        }
   309	        reduced = [row for copies in newest.values() for row in copies]
   310	        resolved = {}
   311	        for (repo, _kind, number), row in _resolve_newest_items(reduced, aliases).items():
   312	            key = (repo, number)
   313	            if key not in wanted:
   314	                continue
   315	            row["native_conflict"] = key in conflicting
   316	            try:
   317	                url = urlsplit(row.get("html_url") or "")
   318	                parts = url.path.strip("/").split("/")
   319	                row["native_identity_valid"] = (
   320	                    url.scheme == "https"
   321	                    and url.netloc.lower() == "github.com"
   322	                    and not url.query
   323	                    and not url.fragment
   324	                    and len(parts) == 4
   325	                    and parts[2:] == ["issues", str(number)]
   326	                    and _canonical_lower("/".join(parts[:2]), aliases) == repo
   327	                )
   328	            except ValueError:
   329	                row["native_identity_valid"] = False
   330	            resolved[key] = row
   331	        return resolved
   332	    finally:
   333	        conn.set_progress_handler(None, 0)
   334	
   335	
   336	def fetch_github_balance(
   337	    conn: sqlite3.Connection,
   338	    project_repos: dict[str, list[str]],
   339	    since_days: int = 14,
   340	) -> list[dict[str, Any]]:
64:workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
119:/bin/zsh -lc 'cat /Users/noelsaw/.codex/skills/swe/SKILL.md; cat ARCHITECTURE.md; cat SOP.md; cat PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
460:| `_read_config()` / `_write_config()` | `ingest/config.py` | Layered config + secrets (`temp/rbos.config` + keyring/secret-store). |
477:| Config / secrets | `ingest/config.py` + `paths.py` | [Credentials](#credentials) |
546:Google Calendar ─────▶ calendar.py               OAuth token (keyring+JSON),  ──▶ calendar_events
642:| Calendar OAuth setup | scripts/setup_calendar_oauth.py | manual | OAuth flow | none | keyring/token | — |
643:| Gmail OAuth setup | scripts/setup_gmail_oauth.py | manual | OAuth flow | none | keyring/token | — |
673:| GitHub | OS keyring + out-of-repo secret store (`~/.config/rebalance-os/secrets`, `0600`) fallback; `gh` CLI as last-resort read fallback | PAT: classic `repo` scope, or fine-grained with All-repos read-only Contents/Metadata (public-only tokens hide private work); persisted to keyring + secret store for launchd reachability — no longer written to `temp/rbos.config` |
674:| Google Calendar | `google-calendar.env` (client credentials) via `resolve_secret_path()` + OAuth user-token in keyring with a JSON fallback at `~/.config/rebalance-os/secrets/google-calendar-oauth` (a legacy pickle migrates to JSON on read) | OAuth 2.0 user consent |
675:| Sleuth | OS keyring + secret store (`~/.config/rebalance-os/secrets/sleuth_web_api`); legacy `*.env` files still read for un-migrated devices | Bearer token, 64-hex |
676:| Gmail | Desktop OAuth token in keyring + JSON fallback at `~/.config/rebalance-os/secrets/google-gmail-oauth`, or MCP push-ingest mode | `gmail.readonly` desktop OAuth, or agent-pushed `ingest_gmail_messages` path when `gmail_ingest_method=mcp` |
677:| Figma | OS keyring + secret store for the PAT; `temp/rbos.config` holds only the (non-secret) file-key allow-list | Personal access token + explicit file selection |
680:Env-file paths resolve via [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_secret_path(name)` — the layered chain is `REBALANCE_SECRETS_DIR` env var → `secrets_dir` field in `~/.config/rebalance-os/config.json` (set via `rebalance config set-secrets-dir`) → `~/secrets/` legacy default. The domain CLI loaders (for example, [src/rebalance/cli/calendar.py](src/rebalance/cli/calendar.py) and [src/rebalance/cli/sleuth.py](src/rebalance/cli/sleuth.py)) use this resolver, so the repo is portable across operator home directories without hardcoded env-file paths. Env files should sit at mode 600. Env files are parsed manually (no `python-dotenv`). Nothing with a secret value is committed.
687:> descriptor, the optional `semantic_docs` provider, secrets/keyring, numbered
694:4. **Credentials** — if the source uses env-style secret files, resolve them through `resolve_secret_path()` and a small domain loader (see `cli/calendar.py` / `cli/sleuth.py`). Never hardcode secrets in repo files.
964:| Onboarding | `setup_github_token` | Validate and store GitHub PAT |
990:                              `resolve_secret_path()` walk a layered chain (explicit
993:                              source of truth for "where is the DB / secrets dir?"
996:                              replaces all `parents[N]` hacks. `resolve_oauth_token_path(service)`
997:                              returns the canonical launchd-reachable token path for
999:                              `rebalance config set-default-database` and `set-secrets-dir`.
1004:    config.py              — secrets storage (temp/rbos.config)
1037:    calendar_config.py     — OAuth token storage, classification rules, review-decision persistence
1121:Do not store any credentials or secrets in this file, other repo files, or any PII in public facing GH issues. The same rule covers machine-specific absolute paths (e.g. a deploy runtime folder's real location) — keep those in your own gitignored `temp/RUNTIME.md`, never in a tracked file. See the pattern in `AGENTS.md` § "Deploy runtime folder".
1598:/bin/zsh -lc "nl -ba PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md; nl -ba src/rebalance/mcp/tools/projects.py; sed -n '730,785p' src/rebalance/ingest/github_scan.py; rg -n 'GitHub [Aa]ctivity|github_balance|get_hiqs_work_activity|hiqs_work_activity' src tests README.md AGENTS.md MCP.md; cat tests/test_mcp_probe.py" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
/opt/homebrew/bin/python3
/opt/homebrew/bin/python3
/opt/homebrew/bin/python3-config
/opt/homebrew/bin/python3.11
/opt/homebrew/bin/python3.11-config
/opt/homebrew/bin/python3.12
/opt/homebrew/bin/python3.12-config
/opt/homebrew/bin/python3.13
/opt/homebrew/bin/python3.13-config
/opt/homebrew/bin/python3.14
/opt/homebrew/bin/python3.14-config
---
name: review-code
description: >-
  Meticulous code and pull request review ladder using /recon and /debug-mantra to test out each
  fix and feature against live ground truth. Supports PR targets under review-PR / --pr <PR#>.
  Loops through /workhorse and /unstuck ladders to autonomously resolve reversible adaptations and
  pivots without stopping for operator permission, driving verified forward movement.
metadata:
  argument-hint: "[diff, branch, file, or --pr <PR#>]"
---

# /review-code (and /review-pr) — Meticulous Ground-Truth Code & PR Review Ladder

`/review-code` is an empirical code and pull request review discipline that treats every proposed
change as a claim requiring firsthand verification. Rather than passively reading a diff and commenting
on style or plausible appearance, `/review-code` actively maps the system's blast radius, tests
fixes and features against live execution, and uses autonomous problem-resolution ladders to drive
forward movement.

It coordinates four specialized disciplines into a cohesive review workflow:
1. **[`/recon`](../../1-hourly/recon/SKILL.md)**: Seam and blast-radius mapping across callers, data
   flows, public contracts, and operational failure paths before forming an opinion.
2. **[`/debug-mantra`](../../1-hourly/debug-mantra/SKILL.md)**: Meticulous ground-truth testing.
   Falsifies symptom-fix patches, executes mutation tests to watch assertions go red, and verifies
   feature acceptance criteria with negative controls and measured evidence.
3. **[`/workhorse`](../workhorse/SKILL.md)**: Governed defect resolution ladder. Triages review
   findings into an atomic priority queue (`[Blocker]`, `[Should]`, `[Nit]`, `[Pass]`) and enforces
   least-mechanism architecture ([`/ponytail`](../../1-hourly/ponytail/SKILL.md)), governance compliance,
   and preservation invariants.
4. **[`/unstuck`](../../1-hourly/unstuck/SKILL.md)**: Autonomous forward movement and anti-hesitation
   engine. Classifies adaptations on the Reversibility Scale (`Easy` vs `Costly` vs `One-way door`):
   **autonomously adapts and tests `Easy` reversible pivots without stopping to prompt the operator**,
   freezes cogs, and applies foundational unblocking moves.

---

## Recite this — verbatim, as the first thing in your first response

> **Review-Code Discipline:**
> 1. **Ingest target & map blast radius (Phase 1 /recon).** Ingest the diff or PR (`review-PR`), map callers, state mutations, contracts, failure paths, and audit adherence to centralized helpers and zero parallel subsystems (DRY).
> 2. **Meticulously test fixes & features (Phase 2 /debug-mantra).** Test every fix against root cause (falsify symptom patches; mutate guards to watch them fail) and verify feature acceptance criteria with measured ground truth and negative controls.
> 3. **Autonomous resolution & anti-hesitation (Phase 3 /workhorse + /unstuck).** If pivots or adaptations are needed, classify reversibility (`Easy`/`Costly`/`One-way door`): autonomously adapt and test `Easy` changes without operator round-trips; freeze cogs and execute foundational unblocking moves.
> 4. **Grade & synthesize verified findings (Phase 4).** Categorize findings (`[Blocker]`, `[Should]`, `[Nit]`, `[Pass]`) with exact `file:line` citations, emit the actionable checklist, and deliver the verdict twice: post the report to the GitHub PR/issue via `gh` **and** render it on-screen with the verified comment URL. Never one without the other.
>
> **Overall Goal:** Every fix and feature verified against live behavior rather than plausible appearance, with reversible issues resolved autonomously and review conclusions grounded in runnable proof.

Then begin work. When `/review-code` (or `/review-pr`) is the active orchestrating skill, this recital
precedes subordinate skill invocations; subordinate skills ([`/recon`](../../1-hourly/recon/SKILL.md),
[`/debug-mantra`](../../1-hourly/debug-mantra/SKILL.md), etc.) are then loaded for their mechanics
without conflicting recitals.

---

## The 5-Phase Review Ladder


codex
The adapter code preserves both boundaries and the nine-key contract. I found two small corrections: the bundle manifest still presents the old signal name and omits the canonical tool, and the parity fixture’s fixed date will fall outside its 30-day window.

exec
/bin/zsh -lc "rg -n 'def _latest_activity_snapshots|scan_date >|scan_date >=' src/rebalance/ingest/db/queries.py
nl -ba MCP.md | sed -n '65,93p'
nl -ba PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md | sed -n '83,95p'
rg -n '"'^```|/Users/|/private/'"' TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md | head -18
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import importlib.util; print(\"mcp installed:\", importlib.util.find_spec(\"mcp\") is not None)'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
 succeeded in 0ms:
148:def _latest_activity_snapshots(
169:        WHERE scan_date >= ?
    65	
    66	---
    67	
    68	### `hiqs_work_activity`
    69	
    70	Shows HiQS work activity (commit/PR/issue) per project over a rolling window.
    71	HiQS = High Quality Signals. `github_balance` remains as a deprecated alias of
    72	this tool (GH-316): same implementation, identical response shape.
    73	
    74	**Prerequisite:** run `rebalance github-scan` via CLI first to populate the `github_activity` table. See PROJECT.md — Step 6 for setup.
    75	
    76	| Param | Type | Default | Description |
    77	|---|---|---|---|
    78	| `since_days` | `int` | `30` | Rolling window in calendar days |
    79	
    80	**Returns:** `list[{project_name, repos_linked, repos_touched, total_commits, prs_opened, prs_merged, issues_opened, last_active_at, is_idle}]`
    81	
    82	---
    83	
    84	### `ask`
    85	
    86	General-purpose natural language query across all data sources. Gathers context from vault embeddings, GitHub activity, project registry, calendar events, and recent vault modifications. Optionally synthesizes a first-pass answer via a local Qwen3 LLM.
    87	
    88	| Param | Type | Default | Description |
    89	|---|---|---|---|
    90	| `query` | `str` | *(required)* | Natural language question |
    91	| `since_days` | `int` | `7` | Rolling window for GitHub and vault activity |
    92	| `skip_synthesis` | `bool` | `false` | Return raw context only (faster, no model load) |
    93	
    83	
    84	**Round 1** (Codex `gpt-6-astra` via consult.sh, read-only worktree, 2026-10-03): verdict **CHANGES — approve after these small plan corrections; retain the two alias seams** (verbatim recommendation).
    85	
    86	| # | Finding | Disposition |
    87	|---|---|---|
    88	| 1 | [Should] Plan violated its own ingestion-vs-signal rule: `cli/github.py:72` scan wording and `cli/onboard.py:124` discovery wording must stay literal; only the MCP tool reference at `cli/github.py:64` changes. | **Accepted.** Both strings stay literal; only the tool reference updated. |
    89	| 2 | [Should] Frozen-key list was incomplete — output also carries `repos_linked` and `is_idle` (`queries.py:405`); parity test must assert a populated row with the exact nine-key set, not alias-vs-alias equality. | **Accepted.** `FROZEN_OUTPUT_KEYS` (9 keys) asserted in the test; reviewer's claim verified firsthand at `queries.py:405-410`. |
    90	| 3 | [Should] Add `MCP.md:68` + tool list `:429`; classify the dashboard "Recent GitHub Activity" (`note_builder.py:374,419`) which is an org rollup from `fetch_org_activity`, a different signal. | **Accepted.** MCP.md updated with canonical name + compat note. Dashboard org view: **Disposition: Retain (out of scope — different signal)**, consistent with the ingestion-vs-signal rule; recorded here. |
    91	| 4-5 | [Pass] Adapter boundaries sufficient; no ratchet conflict. | Noted. |
    92	| 6 | [Pass/Nit] 0.98.1 PATCH agreed; label the fourth rating axis "effort cheapness". | Applied in the rating note. |
    93	| 7 | [Nit] Frontmatter status contradicted the status table. | Fixed (this revision). |
    94	
    95	Round 2 not required: the reviewer's recommendation pre-approved the corrections; no scope, architecture, or risk changed.
11:```
49:```
53:```
64:workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
119:/bin/zsh -lc 'cat /Users/noelsaw/.codex/skills/swe/SKILL.md; cat ARCHITECTURE.md; cat SOP.md; cat PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
249:````markdown
286:````
393:```
412:```
521:```
567:```
720:```
802:```
830:```
856:```
893:```
911:```
982:```
mcp installed: False

codex
**CHANGES — the adapter is correct; fix two small omissions before approval.** Reviewed HEAD `61c431f` (four commits above `origin/development`, not five).

1. **[Should] Update the bundle’s tool metadata.** `manifest.json:78–79` still advertises only `github_balance` as “GitHub activity balance across active projects.” Add `hiqs_work_activity` with the canonical signal label and describe the retained entry as deprecated. Runtime registration works, but this operator-facing surface violates the naming requirement.

2. **[Should] Make the parity fixture independent of today’s date.** `tests/test_hiqs_work_activity_alias.py:59` inserts `2026-10-01`, while calls at lines 69–70 request 30 days. The reader uses the actual clock (`src/rebalance/ingest/db/queries.py:347`) and filters `scan_date >= cutoff` (line 169). From November 1 onward, the fixture becomes idle and the assertions fail without a regression. Patch the reader’s clock to a fixed date or generate current fixture dates.

3. **[Pass] Both compatibility boundaries preserve behavior.** The old MCP tool remains decorated, explicitly deprecated, and delegates with the same argument/default (`src/rebalance/mcp/tools/projects.py:42`). Python retains object identity through direct assignment (`src/rebalance/ingest/github_scan.py:771`). The canonical reader still calls unchanged `fetch_github_balance` (line 766); all nine keys remain intact (`src/rebalance/ingest/db/queries.py:405`). No broken consumer found in the inspected references.

4. **[Pass] The parity test meaningfully constrains the adapter.** It invokes both names through the actual server, compares populated results, asserts exact keys and nonzero values, and checks Python identity (`tests/test_hiqs_work_activity_alias.py:64–79`). It would catch missing registration, divergent responses, empty output, or key drift. Fixing the date makes this durable.

5. **[Pass] Scope is appropriately small.** No duplicate subsystem or schema change. Raw ingestion wording remains literal (`src/rebalance/cli/github.py:72`); the dashboard exception is recorded (`PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md:90`). The large transcript is intentional evidence retention (`TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:1–7`).

Validation limitation: source review only; this copy lacks the `mcp` dependency, so I did not independently rerun the reported tests.

**Recommendation:** Fix manifest metadata and the date-sensitive fixture, rerun focused checks, then approve.
tokens used
72,356
**CHANGES — the adapter is correct; fix two small omissions before approval.** Reviewed HEAD `61c431f` (four commits above `origin/development`, not five).

1. **[Should] Update the bundle’s tool metadata.** `manifest.json:78–79` still advertises only `github_balance` as “GitHub activity balance across active projects.” Add `hiqs_work_activity` with the canonical signal label and describe the retained entry as deprecated. Runtime registration works, but this operator-facing surface violates the naming requirement.

2. **[Should] Make the parity fixture independent of today’s date.** `tests/test_hiqs_work_activity_alias.py:59` inserts `2026-10-01`, while calls at lines 69–70 request 30 days. The reader uses the actual clock (`src/rebalance/ingest/db/queries.py:347`) and filters `scan_date >= cutoff` (line 169). From November 1 onward, the fixture becomes idle and the assertions fail without a regression. Patch the reader’s clock to a fixed date or generate current fixture dates.

3. **[Pass] Both compatibility boundaries preserve behavior.** The old MCP tool remains decorated, explicitly deprecated, and delegates with the same argument/default (`src/rebalance/mcp/tools/projects.py:42`). Python retains object identity through direct assignment (`src/rebalance/ingest/github_scan.py:771`). The canonical reader still calls unchanged `fetch_github_balance` (line 766); all nine keys remain intact (`src/rebalance/ingest/db/queries.py:405`). No broken consumer found in the inspected references.

4. **[Pass] The parity test meaningfully constrains the adapter.** It invokes both names through the actual server, compares populated results, asserts exact keys and nonzero values, and checks Python identity (`tests/test_hiqs_work_activity_alias.py:64–79`). It would catch missing registration, divergent responses, empty output, or key drift. Fixing the date makes this durable.

5. **[Pass] Scope is appropriately small.** No duplicate subsystem or schema change. Raw ingestion wording remains literal (`src/rebalance/cli/github.py:72`); the dashboard exception is recorded (`PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md:90`). The large transcript is intentional evidence retention (`TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:1–7`).

Validation limitation: source review only; this copy lacks the `mcp` dependency, so I did not independently rerun the reported tests.

**Recommendation:** Fix manifest metadata and the date-sensitive fixture, rerun focused checks, then approve.

```
