---
gh_issue: 375
source: https://github.com/HiQS-Labs/rebalanceOS/issues/375
title: "T3 Code session store as an opt-in Rebalance work-activity source"
status: "Completed — merged in PR #376 (88a8972)"
created: 2026-11-11
owner: Claude
updated: 2026-11-11
doc_type: feedback
complexity: 3
risk: 2
effort: 3
phases: 3
ratings_provisional: false
non_goals:
  - no T3 writes
  - no github_activity or hiqs_work_activity change
  - no prompt text capture (CLIO PR #371)
  - no Forge board_sync change (follow-on)
  - no fleet aggregation
  - no new scheduler
related:
  - #370
  - #371
  - HiQS-Labs/XYZ-forge#1000
goal: >
  With the flag on, a daily refresh writes per-device T3 activity (repo, day, provider) to agent_session_activity, readable via the agent_session_activity MCP tool and opt-in by the watched-repo set, while github_activity and hiqs_work_activity stay byte-identical.
---

## Key concepts

- register_collector
- agent_session_activity table (migration 0010)
- read-only T3 projection schema_version guard
- frozen hiqs_work_activity contract
- per-device health for doctor

> **Note for plan writers:** apply the `/ponytail` lens — favor the laziest approach that actually
> works over new infrastructure, and question whether new surface needs to exist at all.

# T3 Code session store as an opt-in Rebalance work-activity source

## Status

| What was just completed | What's next |
|---|---|
| Merged in PR #376 as `88a8972`. Operator flag-on smoke done on this Mac 2026-11-11: refresh wrote 25 rows, doctor `_check_t3_code` OK ([receipt](https://github.com/HiQS-Labs/rebalanceOS/issues/375#issuecomment-6808165029)). | Scheduled-refresh check and other devices, tracked in noelsaw1/noels-cross-project-tasks#87 steps 4 and 11. |

## Idea

T3 Code already records every thread, run and message for all of its agent providers (Codex, Claude, Antigravity, Kimi) in one local SQLite store, `~/.t3/userdata/statev2.sqlite`. Rebalance's HiQS work signal ignores it: the signal only knows GitHub authorship. This issue adds an opt-in, read-only collector that turns T3 session metadata into a per-device "repo worked, by which agent, when" signal. The signal is stored in its own table and exposed through its own MCP tool. It does not touch the frozen `hiqs_work_activity` contract or the `github_activity` semantics.

## Observed

| Claim | Command | Observed |
|---|---|---|
| T3 store covers all providers | read-only `sqlite3 'file:~/.t3/userdata/statev2.sqlite?mode=ro'`, counts only | 151 threads, 634 runs, 3,772 messages. Threads by provider: codex 119, claudeAgent 20, antigravity 8, kimi 1. Message range 2026-09-26 → 2026-11-11 |
| Threads map to GitHub repos | `projection_projects.workspace_root` → `git remote get-url origin` | 3 roots: `HiQS-Labs/XYZ-forge` (136 threads), `BinoidCBD/LTVera-Pandas` (14), `noelsaw1/t3code-fork` (1). 0 orphans, all resolvable |
| Per-thread context exists | `json_each(payload_json)` key names on `orchestration_v2_projection_threads` | keys include `branch`, `worktreePath`, `pullRequests` (filled on 17 threads, 36 distinct PR URLs), `createdBy`, `creationSource`. `linkedPullRequest` is never set |
| Counts need no message text | `PRAGMA table_info(orchestration_v2_projection_messages)` | `role` and `created_at` are real columns (`t3code-fork/.../Migrations/055_OrchestrationV2.ts:194-204`) |
| Run history is recent only | `min(requested_at)` on runs | runs start 2026-11-07, at the v2 cutover. Older activity is visible only through messages |
| Schema version signal | `projection_metadata`, `effect_sql_migrations` | `thread-projections` schema_version = 2. 79 migrations (fork already at 080). `PRAGMA user_version` = 0 |
| Rebalance has no T3/agent-session signal | `grep -ri 't3\|statev2' src/ HiQS/ utils/` at f081931 | 0 matches. CLIO (`ingest/clio.py`) reads only the JSONL prompt log into `clio_prompts` for semantic search |
| `github_activity` is GitHub-authorship only | `src/rebalance/ingest/db/schema.py:307-325` | fixed GitHub counters, `UNIQUE(login,repo_full_name,scan_date) ON CONFLICT REPLACE`, no source/device column |

The full recon map (3 read-only lanes at f081931) is condensed into the Blast radius section below.

## Diagnosis / existing gap

Origin: the work signal has one input, the GitHub API (`github_scan.py:465,519-555`, plus the `__watch__` rollups in `github_watch.py:47-75`). Work done through T3 agents is visible only after it becomes a commit or PR on GitHub. A day of agent sessions that ends with no push produces no signal. Which provider did the work is never recorded.

Fix site: a new collector registered through `register_collector` (`src/rebalance/ingest/index_ops.py:35-125`), writing a new table through a new migration. This removes the class for agent harnesses rather than one instance: the table is keyed by `source`, so later harness sources can write there without schema change.

Why not write into `github_activity` (rejected):
- **The contract is frozen.** `get_hiqs_work_activity` is declared frozen for external consumers (`github_scan.py:756-758`).
- **It would fake GitHub events.** `_activity_repos` counts a repo only when commits+pushes+PR counters are above zero (`index_ops.py:943-966`), so T3 rows would have to pretend to be commits.
- **XYZ-forge would inflate silently.** `board_sync._rebalance_active_repos` sums `github_activity` with no login filter (`forge:utils/py/board_sync.py:142-146`), so sentinel rows would inflate the Forge board with no review.

Relation to PR #371 (open, rebalanceOS): #371 copies T3 *prompts* into CLIO history (`utils/clio-capture/clio-store.py`). It records only the repo basename, no PRs and no run timing, and it feeds no work signal. This issue is complementary and does not depend on #371. Both read T3's internal schema, so this issue copies #371's read-only open pattern (`?mode=ro`, `PRAGMA query_only`, `LIMIT 0` column probes) and adds an explicit projection schema_version guard.

## Plan

1. **Migration `0010_agent_session_activity.sql`.** Extends the forward-only, atomic framework in `src/rebalance/ingest/db/migrations/` (`db/migrate.py:83-98`). It creates two tables:
   - `agent_session_activity(source, device_id, repo_full_name, day, provider, threads, runs, runs_completed, user_prompts, agent_threads, branches_json, pr_urls_json, first_at, last_at, scanned_at)`, PRIMARY KEY `(source, device_id, repo_full_name, day, provider)`.
   - `agent_session_source_health(source, device_id, last_attempt_at, last_success_at, status, observed_schema_version, message)`, PRIMARY KEY `(source, device_id)`. This persists health the way `apple_reminders` persists its fingerprint and drift in its sync transaction (`ingest/apple_reminders.py:838-845`), so doctor never opens the live T3 store.
   - Only `CREATE TABLE IF NOT EXISTS` statements. No change to `schema.py` (frozen) or to `github_activity`.
2. **Reader `src/rebalance/ingest/t3_code.py`.**
   - **Path:** `get_t3_code_config()` in `src/rebalance/ingest/config.py` returns `t3_code_activity_enabled` (default false), `t3_code_db_path` (default `~/.t3/userdata/statev2.sqlite`, passed through `expanduser`, because the gateway does not expand `~`, `db/connection.py:99-100`), `t3_code_window_days` (default 30, clamped to 1–90) and `watch_repos_from_agent_sessions` (default false). It follows the `get_claude_cloud_config` getter pattern (`config.py:1370-1383`).
   - **Open:** through the existing gateway `db_connection_readonly` (`ingest/db/connection.py:90-104`), with `PRAGMA query_only=ON`. All reads run inside one `BEGIN` read transaction so threads, runs and messages come from one consistent snapshot. No new SQLite-gateway exemption is needed.
   - **Contract guard:** require `projection_metadata('thread-projections').schema_version == 2` and probe the needed columns with `SELECT … LIMIT 0`. On any mismatch, write a `drift` row to `agent_session_source_health` (observed version, message), write no activity rows, and return `{"scope": "t3_code", "skipped": True, "reason": "unsupported T3 schema: …"}`.
   - **Never selects message text or any `auth_*`, secret, pairing or webhook table.** The only payload paths read are `$.createdBy`, `$.creationSource`, `$.branch`, `$.worktreePath` and `$.pullRequests`.
   - **Repo mapping:** reuse `parse_github_remote_url` (`src/rebalance/lib/git_ops.py:310`) on each distinct root's origin remote, cached per root. Unresolvable roots are counted under `unresolved_roots` in the result and health message. They are not written.
   - **Aggregation contract.** Three independently aggregated event streams are merged per `(repo, day, provider)`, never joined row-to-row, so counts cannot multiply:
     - **Runs:** day = UTC date of `requested_at`; provider = `runs.provider`; `runs` counts all statuses; `runs_completed` counts `status='completed'`.
     - **Messages:** day = UTC date of `created_at`. Provider comes from the message's run (`run_id` → `runs.provider`); when `run_id` is null or predates the 2026-11-07 run cutover, it falls back to the thread's `default_provider`. `user_prompts` counts `role='user' AND createdBy='user'`.
     - **Threads:** `threads` is the number of distinct thread IDs with at least one run or message in that bucket. `agent_threads` is the same count restricted to threads whose `createdBy` is not `user`.
     - **Other fields:** `branches_json` and `pr_urls_json` are distinct sets from the contributing threads. `first_at` and `last_at` are the min and max event timestamps. A run crossing midnight counts on its `requested_at` day.
   - **Dry-run:** `dry_run=True` computes and returns the aggregates and writes nothing.
3. **Write path: one destination transaction per refresh.**
   - Build every aggregate in memory first; if extraction raises, nothing is deleted.
   - Then, in one transaction: delete this device's `source='t3-code'` rows with `day >= window_start`, insert the recomputed rows, and upsert `agent_session_source_health` (status `ok`, `last_success_at`). Any insert failure rolls back the whole transaction and leaves the prior rows in place.
   - Rows older than the window are retained as history.
   - `device_id` comes from `sync_snapshot.get_device_id()` (`src/rebalance/ingest/sync_snapshot.py:74`).
4. **Collector registration.**
   - Register `Collector("t3_code", _t3_code_adapter, kind="raw_source", included_in_all=True)` next to `clio` (`index_ops.py:2389-2397`).
   - When `t3_code_activity_enabled` is false the adapter returns `skipped` without opening the file. When it is true and the file is absent, it records `missing` health and skips. This follows the `clio` skip and `claude_cloud_signal_enabled` patterns.
   - Existing daily-sync then runs it with no scheduler or plist change (GH-241).
   - Disabling the flag stops collection only. Retained rows stay readable until removed with the rollback command.
5. **Read side.**
   - Add `fetch_agent_activity(conn, since_days, source=None)` in `src/rebalance/ingest/db/queries.py`, the existing read layer, which keeps the read-layer ratchet green.
   - Add a new MCP tool `agent_session_activity(since_days=14)` in `src/rebalance/mcp/tools/projects.py`, with since_days clamped to 1–90. It returns per repo: providers, threads, runs, human prompts, branches, PR URLs and last_at.
   - Document that this tool exposes repo, branch and PR metadata, never message text, to any MCP client of the local server.
   - `hiqs_work_activity` is left byte-identical.
6. **Optional watched-repo union.** `_activity_repos` (`index_ops.py:943`) also includes repos from `agent_session_activity`, but only when config `watch_repos_from_agent_sessions` is true (default false). This adds repos to the GitHub sync set, so it stays opt-in.
7. **Doctor.**
   - Add one DB-only check, `_check_t3_code`, modelled on `_check_apple_reminders` (`doctor.py:1475-1502`), that reads `agent_session_source_health`. It reports:
     - OK "not enabled (opt-in)" when the flag is off and there is no health row;
     - WARN "missing" when the store is absent;
     - WARN drift with the observed schema_version;
     - WARN stale when `last_success_at` is older than 2 days;
     - otherwise OK with `last_success_at`.
   - This distinguishes a successful empty scan from no scan. It replaces the `_COLLECTOR_FRESHNESS` row-age approach, which cannot make that distinction.
8. **Docs.**
   - ARCHITECTURE.md: add a Signal Sources row and a Source→Table fanout row, and correct the "one writer per table" line (`ARCHITECTURE.md:359`; `github_activity` already has two writers).
   - INSTALL/config docs: the opt-in flag and the privacy statement (metadata only).
   - CHANGELOG entry.
9. **Tests.** Rebalance expects new tests and requires them red-first (`AGENTS.md:195`, `SOP.md:98`).
   - Add `tests/test_t3_code.py` with a fixture SQLite built from the pinned DDL subset (`055_OrchestrationV2.ts`, `005_Projections.ts`). Coverage:
     - happy path; unsupported schema; missing file; empty store;
     - null `run_id`; a provider switch within one thread; a run crossing midnight;
     - idempotent rerun under a frozen clock;
     - injected insert failure rolls back;
     - migration 0010 applies on both a fresh DB and an existing DB at 0009;
     - `github_activity` contents unchanged.
   - Every guard gets a mutation witness: the test is shown failing with the guard removed.
   - The existing `tests/test_collector_contracts.py` covers the registration shape.
10. **Live smoke on this Mac.** Results go under `TESTS-RESULTS/<date>+GH-<n>/` with the repo/provider table for the last 14 days.

## Blast radius

Recon pinned to `f081931` (rebalanceOS origin/development, clean export). Integration base: `development@f081931`.

| Seam | Location | Effect of this change |
|---|---|---|
| Collector registry | `index_ops.py:35-125,2389-2430` | +1 collector. Per-collector try/except (`:1811-1814`) isolates failures |
| Migrations | `ingest/db/migrations/` 0002–0009 | +0010 (two tables), additive. A failing migration skips *all* collectors (`index_ops.py:1801-1806`), so the DDL is kept trivial |
| `github_activity` and frozen `hiqs_work_activity` | `schema.py:307-325`, `github_scan.py:741-766` | Untouched (acceptance item proves it) |
| Watched-repo sync set | `index_ops.py:943-966,1045,1089` | Only changes if `watch_repos_from_agent_sessions` is set. The argument is a generator, so it defaults off |
| SQLite-gateway ratchet | `ROUTER.md:62`, `connection.py:90-104` | Uses the existing read-only gateway; no exemption |
| Doctor | `doctor.py:1475-1502` | +1 DB-only check reading `agent_session_source_health` |
| T3 internal schema | `t3code-fork/.../055_OrchestrationV2.ts:55,73,194`, `ProjectionStore.ts:736` | Read-only consumer. Upstream reshape → clean `skipped`, never a partial write |
| PR #371 (CLIO T3 prompts) | `utils/clio-capture/clio-store.py` | Not modified. A second reader of the same schema; it uses `?mode=ro` + `LIMIT 0` column probes, and this issue adds the projection schema_version guard on top |
| XYZ-forge board_sync | `forge:utils/py/board_sync.py:133-163` | Not changed by this issue. A follow-on may union the new table |

Write-set:
- `src/rebalance/ingest/db/migrations/0010_agent_session_activity.sql` (new)
- `src/rebalance/ingest/t3_code.py` (new)
- `src/rebalance/ingest/index_ops.py`
- `src/rebalance/ingest/db/queries.py`
- `src/rebalance/mcp/tools/projects.py`
- `src/rebalance/doctor.py`
- `src/rebalance/ingest/config.py` (flags)
- `tests/test_t3_code.py` (new)
- `ARCHITECTURE.md`, `CHANGELOG.md`, and the config/INSTALL doc for the flag
- `TESTS-RESULTS/<date>+GH-<n>/` (new)
- ledger rows through `releases_app.py`

Route: builder Claude or Codex in a fresh task clone; reviewer Codex via relay plan QA and final QA (start-task Steps 6 and 9).

## Dependencies

- None blocking. PR #371 is complementary, and either can land first.
- The T3 store must exist on the device. The connector skips cleanly where it does not.
- Follow-ons, not prerequisites:
  - XYZ-forge `board_sync` repos_source union with `agent_session_activity`.
  - The forge `?mode=ro` CANTOPEN on `rebalance.db`, an unconfirmed sidecar or sandbox cause.
  - Fleet export of the table through `sync_snapshot.py`.

## Acceptance

- [ ] `refresh_index(scope=["t3_code"])` against a fixture T3 DB writes `agent_session_activity` rows with `repo_full_name` resolved to `owner/repo` and the per-provider counts the aggregation contract predicts for the fixture. Red control: on f081931 the scope `t3_code` is unknown and the table does not exist.
- [ ] Fixtures covering a null `run_id`, a provider switch within one thread and a run crossing midnight produce exactly the hand-computed `(repo, day, provider)` counts, with no multiplied rows. Red control: a deliberately row-joined query, used in place of the independent streams, yields inflated counts and fails the assertion.
- [ ] A fixture with `thread-projections` schema_version 3, or a missing probed column, returns `skipped` with an `unsupported T3 schema` reason, writes zero activity rows and records a `drift` health row. Red control: with the guard removed, the same fixture writes activity rows or raises, and the test fails.
- [ ] An empty T3 store (tables present, zero threads) records `ok` health with zero rows. A missing file records `missing` health with zero rows. Neither raises. Red control: the populated fixture writes more than zero rows, so the empty case is not passing vacuously.
- [ ] Two refreshes over the same fixture under a frozen clock yield an identical `agent_session_activity` row set, `scanned_at` included. Red control: adding one message to the fixture and re-running changes exactly the affected `(repo, day, provider)` row.
- [ ] An injected failure on the second insert leaves the previous `agent_session_activity` rows and health row unchanged. Red control: with the transaction removed, the test sees partially deleted rows.
- [ ] Migration 0010 applies cleanly to a fresh database and to an existing database at 0009, and a second run is a no-op. Red control: on f081931 neither table exists after migrate.
- [ ] A content hash of every `github_activity` row, and the `hiqs_work_activity` output, are identical before and after a `t3_code` refresh. Red control: the comparison helper fails when the test deliberately mutates one `github_activity` counter.
- [ ] Every SQL statement in `t3_code.py` is checked by the test to read only the allowed payload paths and no `auth_*`, secret, pairing or webhook table. Red control: a deliberately added `json_extract(payload_json,'$.text')` makes the check fail.
- [ ] MCP `agent_session_activity(since_days=14)` returns per-repo provider, thread, run and prompt counts with PR URLs. Red control: the tool is absent on f081931.
- [ ] `rebalance doctor` reports OK "not enabled" when the flag is off, and WARN for missing store, drift or stale, all from `agent_session_source_health` without opening the T3 file. Red control: on f081931 there is no T3 check.
- [ ] Live smoke on this Mac (flag on, `since_days=14`) lists every repo that the direct read-only count of T3 threads with activity in that same window resolves to, with provider splits. Results are retained under `TESTS-RESULTS/<date>+GH-<n>/` beside that count. Red control: with the flag off, a fresh DB gets no rows from the refresh.

## Verification

- New `tests/test_t3_code.py`, written red-first per `SOP.md:98`, plus the existing `tests/test_collector_contracts.py`, then the full `pytest tests/ HiQS/tests` and `rebalance doctor` per `ROUTER.md:51`.
- CI ratchets: ruff, mypy, SQLite gateway, script inventory, machine paths, read layer and near-duplicate (`.github/workflows/ci.yml:31-54`).
- A manual live smoke and the before/after `hiqs_work_activity` diff, retained under `TESTS-RESULTS/<date>+GH-<n>/` with `provenance.jsonl`.

## Non-goals

- No writes to T3's database and no T3 server or fork change.
- No change to `github_activity`, the frozen `hiqs_work_activity` output, or XYZ-forge `board_sync`; the board union is a separate follow-on.
- No capture of prompt or message text. That is CLIO's job (PR #371).
- No fleet aggregation across Macs; rows are per device.
- No new scheduler, plist or script.
- No ranking influence: no `candidates=` provider in this issue.

## Risk and rollback

- **Upstream T3 schema change:** the version guard plus column probes turn it into a clean `skipped` and a doctor drift line, never a partial write.
- **A broken migration blocks every collector:** keep 0010 to two `CREATE TABLE IF NOT EXISTS` statements plus one index.
- **Privacy:** metadata only, enforced by an acceptance check on the SQL, and opt-in by flag.
- **Watched-repo generator effect:** behind its own default-off flag.
- **Rollback:**
  - Set `t3_code_activity_enabled=false`, then on that device run `DELETE FROM agent_session_activity WHERE source='t3-code' AND device_id=?` and the matching delete on `agent_session_source_health`. The rows are per device, so cleanup is scoped by device.
  - The forward-only tables stay, empty and unread.
  - Reverting the PR removes the reader and the MCP tool. Builds before 0010 never read these tables, so a code revert is safe after any amount of data has been written. The schema itself cannot be un-migrated (forward-only); that is the one irreversible part, and it is additive.

## PRS proposal

- pri 55: closes the blind spot where a full day of T3 agent work without a push is invisible to Rebalance, giving immediate MCP visibility per provider; board benefit is prospective (Forge follow-on)
- sev 35: no breakage today; the cost is under-reporting work and having no per-provider attribution, not wrong data
- appeal 50: neutral until the operator sets it
- effort 45: medium; one migration, one read-only collector, one MCP tool, a doctor entry and red-first tests, following the existing clio and claude_cloud patterns

## Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_t3_code.py tests/test_collector_contracts.py",
  "fix_probes": [
    { "type": "path_absent", "path": "src/rebalance/ingest/t3_code.py",
      "note": "T3 collector module does not exist at development" },
    { "type": "path_absent", "path": "src/rebalance/ingest/db/migrations/0010_agent_session_activity.sql",
      "note": "migration creating agent_session_activity does not exist" },
    { "type": "path_absent", "path": "tests/test_t3_code.py",
      "note": "collector test file does not exist" },
    { "type": "grep_absent", "path": "src/rebalance/ingest/index_ops.py", "pattern": "\"t3_code\"",
      "note": "no t3_code collector registered" }
  ],
  "artifacts": [
    "src/rebalance/ingest/t3_code.py",
    "src/rebalance/ingest/db/migrations/0010_agent_session_activity.sql",
    "tests/test_t3_code.py",
    "src/rebalance/ingest/index_ops.py",
    "src/rebalance/ingest/db/queries.py",
    "src/rebalance/mcp/tools/projects.py",
    "src/rebalance/doctor.py",
    "src/rebalance/ingest/config.py",
    "ARCHITECTURE.md",
    "CHANGELOG.md"
  ],
  "artifacts_new": [
    "src/rebalance/ingest/t3_code.py",
    "src/rebalance/ingest/db/migrations/0010_agent_session_activity.sql",
    "tests/test_t3_code.py"
  ],
  "remediation": {
    "source": "issue",
    "criteria": "Opt-in read-only t3_code collector writes per-device agent_session_activity rows from ~/.t3/userdata/statev2.sqlite with a schema_version guard, exposed via MCP agent_session_activity, with github_activity and hiqs_work_activity unchanged."
  }
}
```

Recon: f081931 · base: development@f081931 · tier: standard · review: consult idea-t3-signal-114049 models=codex, degraded hash 94b5bb775c3624081af170cf328351be3c022c4c08e90c0aa65b695b1b2d982f

## Why

T3 Code already records every thread, run and message for all its agent providers in one local SQLite store, but Rebalance's HiQS work signal only knows GitHub authorship, so agent work without a push and per-provider attribution are invisible.

## Phase 0 — Recon deltas and implementation plan (start-task, 2026-11-11)

Base: `origin/development@70ccfc0` (PR #371 merged after the issue's `f081931` recon pin; #371
touched only `utils/clio-capture/`, CI and docs, so no seam below moved). Clone
`rebalanceOS-gh375-t3-code-session-store-2026-11-11`, branch `feat/<same>`.

### Prior art (ROUTER.md four checks)

- Open PRs: none on `HiQS-Labs/rebalanceOS` or `Hypercart-Dev-Tools/rebalance-OS`.
- Ledger In-progress rows: none on T3 / agent sessions (GH-370 is CLIO prompt capture, complementary).
- `grep -rni 'statev2|t3_code|agent_session' src utils HiQS` (excluding `utils/clio-capture/`): 0 hits.
- Issues: only #370 (closed, CLIO prompts) and this one.
- Rating recurrence: feature, not a defect; no incident class to count (14-day windows N/A). Rating
  kept at the issue's proposal, **55/35/50/45** (appeal neutral, no operator override).

### Recon deltas that change the issue plan

| # | Issue text | Ground truth (live read-only probe + T3 source) | Plan consequence |
|---|---|---|---|
| D1 | guard reads `projection_metadata('thread-projections')` | table is `orchestration_v2_projection_metadata` (`OrchestrationV2/Foundation.ts:151`, writer `EventSink.ts:393-404` stamps `ORCHESTRATION_V2_PROJECTION_SCHEMA_VERSION`=2, `ProjectionStore.ts:736`). Live row: `thread-projections\|2` | guard reads that table |
| D2 | `pr_urls_json` from `$.pullRequests` | `$.pullRequests` is an array of **objects** (keys incl. `url`, `number`, `repository`, `snapshot`); 140 threads carry the array, 71 elements | SQL reads only `$.pullRequests`; Python keeps each element's `url` string and drops everything else |
| D3 | allowed paths include `$.worktreePath`, `$.creationSource` | not needed for any output column | not read at all — read set is `$.createdBy` (threads, messages), `$.branch`, `$.pullRequests` |
| D4 | `included_in_all=True` | `tests/test_collector_contracts.py:28` and `tests/test_collector_registry.py:33-58` pin the exact raw/`all`/default sets | those two existing expectations gain `t3_code` (an intended contract change, not a new suite). `daily_sync.sh` runs the default recipe, so this is what makes collection automatic when the flag is on |
| D5 | MCP returns per-repo `threads` | rows hold per-(day, provider) distinct thread counts; no thread IDs are stored, so a cross-day distinct count is not derivable | per-provider rollup field `thread_days` = sum of that provider's daily distinct threads; repo-level total `thread_provider_days` = sum over (day, provider) buckets, so one thread on two providers in one day counts 2 (definition stated in the MCP docstring; pinned by the provider-switch fixture). Per-row `threads` stays exact. No thread-ID column is added (plan QA r1 S1) |
| D6 | run statuses | live: completed 643, failed 11, interrupted 3, running 1 | `runs` counts all, `runs_completed` counts `completed` only (as specified) |
| D7 | message provenance | 983 user-role messages: 363 `createdBy=user`, 620 `createdBy=agent`; 751 messages have null `run_id`; 0 orphan `run_id`; 0 threads without a project | `user_prompts` = role user AND createdBy user; provider = `COALESCE(run.provider, thread.default_provider)` via a primary-key lookup join (one row per message, cannot multiply) |
| D8 | thread `branch`/`pullRequests` | these are the thread's *current* payload, not history | documented: branch/PR sets are "as of scan", attached to every bucket the thread contributed to |

### Implementation (ordered; verification inline)

1. **Red first.** `tests/test_t3_code.py` with a fixture T3 DB built in-test from the pinned DDL
   subset (threads/runs/messages/projects/projection_metadata columns above) and a temp git repo whose
   `origin` is `git@github.com:acme/widgets.git`. Run it on the base → red (module/scope/table absent).
2. **Migration `0010_agent_session_activity.sql`**: two `CREATE TABLE IF NOT EXISTS` + one day index,
   no transaction control (runner owns it, `migrations/README.md`). → migration tests green.
3. **Config** `get_t3_code_config()` in `ingest/config.py` (getter pattern of `get_claude_cloud_config`):
   `t3_code_activity_enabled` (False), `t3_code_db_path` (`~/.t3/userdata/statev2.sqlite`, expanduser),
   `t3_code_window_days` (30, clamped 1–90), `watch_repos_from_agent_sessions` (False).
4. **Reader/writer `ingest/t3_code.py`** (the single writer of both new tables):
   - `sync_t3_code_activity(database_path, *, dry_run=False, config=None) -> dict`.
   - disabled → `{"scope":"t3_code","skipped":True,"reason":"disabled (opt-in)"}`; T3 file not opened, no write.
   - file absent → health `missing`, skipped. **Every health write (missing / drift / error / ok) is skipped on dry-run.**
   - open via `db_connection_readonly`, `PRAGMA query_only=ON`, one `BEGIN` read snapshot; guard =
     metadata version == 2 + `SELECT <cols> FROM <table> LIMIT 0` probes; mismatch → health `drift`
     (observed version + message), zero activity writes, skipped `unsupported T3 schema: …`.
   - three grouped streams keyed `(thread_id, day, provider)` (runs; messages; thread meta per thread),
     merged in Python per `(repo, day, provider)`; window `day >= today_utc - window_days`.
   - repo per distinct `workspace_root` via `run_git(root, "remote", "get-url", "origin")` +
     `parse_github_remote_url`, cached per root; unresolved roots counted, not written.
   - dry-run returns the aggregates, writes nothing (not even health).
   - write: build all rows first; then one `BEGIN IMMEDIATE` on `rebalance.db`: delete this device's
     `source='t3-code'` rows with `day >= window_start`, insert rows, upsert health `ok`; rollback on
     any failure. Unexpected extraction exception → health `error` (own small txn), then re-raise into
     `refresh_index`'s per-collector error envelope.
5. **Collector**: `_refresh_t3_code` + `Collector("t3_code", …, kind="raw_source", included_in_all=True)`
   next to `clio`; update the two pinned set expectations (D4).
6. **Read side**: `fetch_agent_activity(conn, since_days, source=None)` in `ingest/db/queries.py`
   (per-repo rollup: `providers{p: {thread_days, runs, runs_completed, user_prompts}}`, `thread_provider_days`, `runs`, `runs_completed`, `user_prompts`,
   `branches`, `pr_urls`, `last_at`) + MCP `agent_session_activity(since_days=14)` (clamped 1–90) in
   `mcp/tools/projects.py`. Missing table → `[]`.
7. **Opt-in watched-repo union**: `_activity_repos` appends `fetch_agent_activity` repos only when
   `watch_repos_from_agent_sessions` is true (also reaches `diagnose.py:149`, the only other caller).
8. **Doctor** `_check_t3_code(db_path)`: DB-only read of `agent_session_source_health` + config flag;
   reads **this device's** row (`get_device_id()`). Flag off → OK "not enabled (opt-in)", plus
   "; retained health: <status> <last_success_at>" when a row remains from an earlier enablement. Flag on and
   no row → WARN "enabled, no scan recorded yet". Otherwise WARN missing / WARN drift (observed version) /
   WARN error / WARN stale (`last_success_at` > 2 days) / OK last success. Never opens the T3 file (test
   patches the T3 open to raise).
9. **Docs + version**: ARCHITECTURE.md (Signal Sources row, fanout row, corrected one-writer example:
   `github_activity` is written by `github_scan.py` and the `__watch__` rollups in `github_watch.py`),
   MCP.md tool row with the metadata-only exposure note, CHANGELOG `0.107.0` (MINOR) + `pyproject.toml`
   + `manifest.json` version.
9a. **Ratchet compliance**: `ingest/t3_code.py` imports neither `datetime` nor `subprocess` (GH-126
    banned-import ratchet); window dates come from one new shared primitive `time_ops.utc_date_days_ago(days)`
    in `src/rebalance/lib/time_ops.py`, used by both `t3_code.py` and `fetch_agent_activity`; git runs
    through `git_ops.run_git`. No baseline or pragma change.
10. **Gates**: `pytest tests/ HiQS/tests`, ruff check/format, mypy `src/`, the five `utils/pdda/check_*`
    ratchets, `rebalance doctor`, `utils/pdda/pdda.sh run`. Mutation witnesses (guard removed → named
    test red) and a live dry-run against the real T3 file are recorded under
    `TESTS-RESULTS/2026-11-11+GH-375/`.

### Acceptance map (issue items → tests)

| Issue acceptance | Test / evidence |
|---|---|
| refresh writes resolved rows with predicted counts | `test_refresh_index_writes_predicted_rows` |
| null run_id / provider switch / midnight, no multiplication; row-join red control | `test_aggregation_edge_cases_exact` + `test_row_joined_query_inflates` |
| schema v3 / missing column → skipped, 0 rows, drift health; guard-removed witness | `test_unsupported_schema_*` + mutation witness |
| empty store ok/0 rows; missing file missing/0 rows | `test_empty_store_ok`, `test_missing_file_records_missing` |
| idempotent under frozen clock; +1 message changes exactly one row | `test_rerun_identical_and_single_row_delta` |
| injected second-insert failure keeps prior rows + health; no-txn witness | `test_insert_failure_rolls_back` (a test-DB trigger aborts the 2nd insert) + mutation witness |
| migration fresh + from 0009 + no-op rerun | `test_migration_0010_*` |
| github_activity hash + hiqs_work_activity unchanged; helper red control | `test_github_contract_unchanged` |
| SQL reads only allowed paths/tables; `$.text` red control | `test_executed_sql_is_metadata_only` (captures every executed statement via `set_trace_callback`) |
| MCP tool returns per-repo counts + PR URLs | `test_mcp_agent_session_activity` (real FastMCP `call_tool`) |
| doctor states from health table without opening T3 | `test_doctor_t3_code_states` |
| watched-repo union is opt-in | `test_activity_repos_union_opt_in` |
| live smoke with flag on | **Deferred by the operator for this task**: replaced by a `dry_run=True` read of the live T3 file vs the direct read-only count (no writes, no config change). The flag-on smoke stays an open item on the issue |

### Non-scope (this PR)

XYZ-forge `board_sync` union; fleet export via `sync_snapshot.py`; enabling the flag on any device;
any change to `github_activity`, `hiqs_work_activity`, PR #371's `clio-store.py`, schedulers or plists;
ranking influence (`candidates=`); thread-ID storage.

### Rollback

Flag off stops collection; device-scoped `DELETE` of `source='t3-code'` rows in both tables removes
data; reverting the PR removes reader, tool and doctor check; the two tables are forward-only and stay
empty/unread.

### Implementation notes (2026-11-11)

- Plan QA r2 Approved; one harness defect observed: `relay-drive` exited 4 (`attest-publish-failed`) because
  `relay-system/` is gitignored here and its `git add` (no `-f`) errors on the tracked thread, although the
  attestation commit itself landed (`a278102`). Final QA therefore uses a thread under `TESTS-RESULTS/`.
- Mutation witness run added one assertion (dry-run must not write health on a missing or drifted store);
  the witness for that guard was green before it.
- The 14 root-suite failures are identical by test ID on base `70ccfc0` (disposable verify clone).
- Live smoke ran as a dry run only, per the operator's scope; the flag-on smoke remains open.
