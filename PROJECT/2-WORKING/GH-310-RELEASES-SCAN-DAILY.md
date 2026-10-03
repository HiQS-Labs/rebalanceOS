---
gh_issue: 310
source: https://github.com/HiQS-Labs/rebalanceOS/issues/310
title: Opt-in RELEASES ledger scan and /daily close-loop inputs
status: Plan — Codex QA round 1 dispositions applied
created: 2026-10-02
updated: 2026-10-02
owner: Grok (start-task)
goal: Let the operator (and /daily) see per-repo RELEASES ledger tasks across local clones next to the close-loop flags, read-only and opt-in, without a new tracker or fetch path.
doc_type: project
branch: feat/gh310-releases-scan-daily
effort: 3
complexity: 3
risk: 2
phases: 1
---

# Opt-in RELEASES ledger scan and /daily close-loop inputs

## Status

| What was just completed | What's next |
|---|---|
| (b) and (c) implemented and committed; focused tests green; real read-only run on the Mini changed no ledger (fingerprint identical before and after). Version 0.99.0, CHANGELOG and README updated. | Final Codex QA approved (round 2). Next: the full gate once, then push and open the PR against `development`. |

**Rating: rated 55/30/50/55.**
- **Priority 55:** the operator asked for it explicitly, and it feeds `/daily` and the #709 storyline with local task context. It is not urgent and no work is blocked.
- **Severity 30:** a feature, with no defect.
- **Appeal 50:** neutral; the operator gave no score.
- **Effort 55:** two seams, a Python CLI flag and a stdlib scanner flag, both reusing existing readers.
- **Recurrence:** N/A (a feature, not a defect class; the 14-day windows don't apply).

## Scope decision

- **(b) then (c), in one branch and one PR.** (c) is a thin consumer of (b)'s JSON. Splitting them would leave (c) blocked behind a merge this run may not perform (no stacked-PR authorization). One version bump and one review cover both. The commits stay separated per part.
- **Focus 5 Phase 1 (a) is deferred.**
  - The floating app is `macOS/Apps/Focus5Float`, about 7.4k lines of Swift.
  - It reads the pulse server through `Focus5Client.swift` and the CLIO prompt-log Markdown (`PromptLogModels.swift`).
  - Phase 1 would need a new server endpoint (or the unbuilt #29 shared read layer), Swift model and view changes, and a Swift build and test run.
  - That isn't a small local change inside an existing Focus 5 read path, so it stays a follow-up under #310/#120.
- **Phase 2 (status line) is out of scope.**

## Phase 0 — Prior Art Review

- **`rebalance github-close-loop` / `infer_close_loop_flags`** (`src/rebalance/ingest/github_readiness.py`, #307/#308): the command (b) extends. Its corpus data (issues, PRs, links) and its flags are reused for the drift join. No new GitHub read.
- **`db_connection_readonly`** (`src/rebalance/ingest/db/connection.py`): the existing `?mode=ro` gateway. It is reused to open ledgers, so there is no new `sqlite3.connect` (enforced by the sqlite gateway ratchet).
- **XYZ `releases_app.load_work_evidence`, via `utils/py/releases_cycle.read_work_status` and `utils/daily_work_synthesis.collect_issue_statuses`** (GH-233). This is the qualified reader for **explicitly configured** roots: at most 4, requiring schema ≥ 8 and a trusted harness path. It is **not reused** for the scan, for four reasons:
  1. Most local ledgers are below schema 8 (all 5 rebalanceOS clones), so they would all report "unsupported".
  2. It needs a configured harness checkout.
  3. Its subprocess-per-root model with 2-second windows is sized for 4 roots, not about 30.
  4. It doesn't return title, doc path or updated_at.

  #310 explicitly allows direct `mode=ro` reads. The GH-233 rule "no discovery or guessed sibling path" governs that recorded-status block. The new scan only walks directories the operator names, and it doesn't feed or change that block.
- **`scan_unclosed_loops.py`** (`.agents/skills/daily/scripts/`, mirrored to `.claude/skills/daily/` and enforced by `tests/test_skills_drift.py`): the /daily Step 3 scanner. It already fetches **live** PR state per watched repo (`gh pr list --state all`). (c) adds an opt-in flag here and reuses that live data for re-verification. `utils/daily_work_synthesis.py` consumes its `--json` counts unchanged.
- **The `utils/py/releases_app.py roadmap list` CLI** opens through the writer factory `connect()` and prints text. It is not suitable for a read-only, machine-readable scan.

## Requirements

### (b) Ledger scan on `github-close-loop`
1. `--releases-scan DIR[,DIR…]`. **Default off:** the JSON is byte-identical to before (no `releases` key) and the text output is unchanged.
2. **Discovery** walks each dir down to a *directory* depth of ≤ 3 below the scan dir (for example `XYZ-forge/temp/gh254-x` is depth 3, so its `releases.db` file sits at depth 4, the same as `find -maxdepth 4 -name releases.db`), without following symlinks. Pruning reuses the canonical `rebalance.lib.git_ops.should_descend` (its prune set, including `node_modules`, `.venv`, `__pycache__`, `dist` and `build`, plus every hidden dir), so there is no second prune list.
   - A ledger root is a dir containing both `releases.db` and `.git` (a dir or a gitfile). A `releases.db` without `.git` is skipped and counted as `skipped_non_repo`.
   - Discovery is capped at 200 ledgers and reports `truncated`.
3. **Read-only access.**
   - Open with `db_connection_readonly` (`mode=ro`).
   - Skip a ledger whose SQLite header is in WAL mode (bytes 18–19 == 2) as `wal-mode`, so no `-shm` file is ever created.
   - No migrations, no writes, no CLI `main`.
   - Per-ledger errors (`missing-table`, `unreadable`, `wal-mode`, `identity-unresolved`) are reported per ledger, and the run continues.
4. **Identity.** Resolved **per roadmap row**, through `roadmap_items.repo_id` → `repos.slug`, because a ledger can hold several `repos` rows.
   - The row's slug must equal the `--repo` full name, or equal its basename *and* the clone's origin must resolve to `--repo`.
   - Origin resolution: `git remote get-url origin`, following local-path origins for at most 3 hops.
   - Ledgers for other repos are counted (`other_repo_ledgers`) but not listed.
   - Branch comes from `git branch --show-current`.
5. **Tasks.**
   - `roadmap_items` rows in the **In progress** or **Queue / parked intake** sections, or with marker 🚧 or `status_label == in-progress` (where present).
   - Fields: repo, clone_path, branch, global_id, gh_number, title, section, status (status_label, else `in-progress`/`parked` from the section), rating `P/S/A/E` when present, issue_url, doc_path, updated_at.
   - Columns that may be missing (`status_label`, `rating_*`) degrade to null.
6. **Conflicts.**
   - Group by gh_number, or by global_id when gh_number is null.
   - When clones disagree on section or status, list every clone's value and pick a `preferred` row: the newest `updated_at`, with ties going to the `development`/`main` branch.
   - The merged task list carries one row per key plus a `clones` count.
7. The scan runs on **both** report paths. With `no_local_data` the `releases` block is still attached, just without drift. The read-only guarantee covers the RELEASES ledgers; the existing `ensure_github_schema` call on `rebalance.db` is pre-existing behaviour, and real runs use a `/tmp` copy.
8. **Drift**, joined with the same corpus data the flags use, only for in-progress tasks with a gh_number:
   - `issue_closed`: the corpus issue is closed.
   - `pr_merged`: the issue is open and a linked PR is merged.
   - `pr_stale`: a linked open PR carries a `stale_pr`/`forgotten_draft` flag.
   - An item missing from the corpus is not drift.

### (c) `/daily` wiring
9. **`scan_unclosed_loops.py` daily mode** gets `--close-loop` and `--releases-scan DIRS`.
   - Env defaults: `REBALANCE_DAILY_CLOSE_LOOP=1` and `REBALANCE_RELEASES_SCAN_DIRS`.
   - When enabled, for each `PRIMARY_WATCHED_REPOS` repo it runs `rebalance github-close-loop --repo R --output json [--releases-scan DIRS]`. The binary comes from `REBALANCE_BIN`, else `shutil.which("rebalance")`, with a 30-second timeout.
10. **Merge and dedupe** by `(repo, number)` into `flagged_loops`, where each entry has `sources` tags: `close-loop:<flag>`, `releases:<repo>#<global_id>` and `releases-drift:<kind>`.
11. **Live re-verification** before an item counts as open:
    - PR items must be `OPEN` in the scanner's existing live `gh pr list` data.
    - Issue items must appear in one bounded `gh issue list --state open` per repo (only when enabled).
    - Unverifiable items are excluded and counted as `unverified`.
    - `closed_without_delivery` goes to `questions`, never to open loops.
12. **Output when off:** the payload and summary line are identical.
13. **Output when on:** adds `counts.flagged_loops`, `flagged_loops`, `questions` and `inputs` (per-input `ok` or `skipped: <reason>`), and appends `, N flagged loops (close-loop/releases)` to the summary line.
14. **Degradation:** a missing binary, non-zero exit, bad JSON or empty output prints one stderr line, `daily: <input> input skipped (<reason>)`, and the scan otherwise proceeds as today.
15. **`SKILL.md`** Steps 2/3 and the synthesis guidance get the opt-in inputs, the source-tag citation format (`[Trigger: close-loop:stale_pr …]`, `[Trigger: releases:<repo>#<task>]`), "closed without delivery is a question", and the re-verification rule. Both mirrors are kept identical.

## Smallest surface (ordered)

1. `src/rebalance/ingest/releases_scan.py`, a new module of about 150 lines: `discover_ledgers(dirs, max_depth=3, cap=200)` and `scan_releases(dirs, repo_full_name) -> dict` (ledger reads, identity, tasks, conflicts). Ledger SQL is scoped to the ledger tables, not the github activity tables.
2. `github_readiness.infer_close_loop_flags(..., releases_scan_dirs=None)`: when set, attach `report["releases"] = scan_releases(...)` plus `drift` computed from the corpus data the function already holds.
3. CLI `github-close-loop --releases-scan`: comma-split, `expanduser`; the text output appends a short releases summary.
4. **Tests** (`tests/test_releases_scan.py`):
   - discovery: a found ledger, a skipped non-repo, a pruned dir;
   - two clones conflicting, with the newest preferred;
   - a corrupt ledger and a missing table reported per ledger without failing;
   - the **red control**: the ledger's sha256 and mtime are unchanged after a scan, and no `-wal`/`-shm`/`-journal` sidecar appears. This includes a WAL-mode fixture, which must be skipped as `wal-mode` with its bytes, mtime and sidecar set unchanged;
   - drift `issue_closed` and `pr_merged` positives with a negative twin;
   - default-off JSON identical to the pre-change shape.
5. `scan_unclosed_loops.py` (both mirrors): `_close_loop_inputs(...)`, about 90 lines, wired into the daily branch only.
6. **Tests** (`tests/test_daily_loop_inputs.py`, with a fake `rebalance` binary script and stubbed live PR/issue data):
   - off-mode payload keys and summary line identical to the baseline;
   - on-mode dedupe across sources, with a merged PR excluded and a closed issue excluded;
   - closed_without_delivery appears only in questions;
   - a missing binary produces one skipped line and an unchanged payload.
7. `SKILL.md` in both mirrors.
8. Version 0.98.0 → 0.99.0 (pyproject, manifest, `__init__`), a CHANGELOG entry, a README CLI line, this doc and ROADMAP.

## Non-goals

- Focus 5 (a) Phases 1 and 2.
- Fleet-wide ledger sync.
- Ledger writes or `releases roadmap sync`. Intake is recorded in PDDA and ROADMAP only, because the operator barred ledger writes for this run.
- Changing GH-233's recorded-status reader or its root cap.
- Changing `temp/close-the-loop.md` rendering.
- Any LLM-made field.
- Scanning without explicit dirs.

## Risks and rollback

- **Torn reads:** a ledger written mid-scan can fail to read. It is reported per ledger and the run continues.
- **Identity:** basename slugs plus local-path origins can leave a clone unresolved. It is reported, not guessed.
- **Live verification cost:** at most one extra `gh issue list` per watched repo, only when enabled.
- **Rollback:** everything is opt-in and additive. Revert the PR.

## Tests and gate

- **Focused:** `pytest tests/test_releases_scan.py tests/test_daily_loop_inputs.py tests/test_github_close_loop.py tests/test_shutdown_scanner.py tests/test_skills_drift.py`.
- **Real read-only run** on the Mini: scan `~/Documents/GitHub` against a `/tmp` copy of `rebalance.db`, hashing every ledger before and after (the red control on real data). Counts only in the report.
- **Gate, once on the final commit:** full `pytest tests/`, `ruff check`, `ruff format --check`, `mypy src/`, `pdda.sh run`, `check_read_layer.py` and `check_script_inventory.py --check`.

## Acceptance map (#310)

| #310 acceptance | Check |
|---|---|
| Finds every ledger under the dirs and skips non-repo folders | Discovery test; on the real run, found == 31 for `~/Documents/GitHub` at depth 4. |
| Default-off output identical | CLI JSON test and scanner off-mode test. |
| Red control: checksum and mtime unchanged | Unit test and the real-run hash diff. |
| A missing or corrupt ledger is reported per repo | Corrupt and missing-table test. |
| /daily: both off means schema unchanged | Scanner off-mode test. |
| /daily: at least one real loop per source, cited once | Real run with both inputs on; counts reported. |
| A merged or closed PR is never an open loop | Scanner on-mode negative twin. |

## Codex QA log

**Plan round 1** (Codex via relay-xyz `consult.sh`, read-only worktree, 2026-10-02 PT): verdict CHANGES.

| # | Finding | Disposition |
|---|---|---|
| 1 | BLOCKER: depth ≤ 3 contradicts the 31 ledgers counted at depth ≤ 4. | Accepted as a clarification. Depth is directory depth: a ledger *root* at ≤ 3 has its `releases.db` file at ≤ 4, matching the recon `find -maxdepth 4`. The definition is now in Req 2. |
| 2 | The scan must also run on the `no_local_data` path; scope the read-only guarantee. | Accepted (Req 7). |
| 3 | Resolve identity per row via `repo_id` → `repos`; add a WAL fixture to the red control. | Accepted (Req 4 and test list). |
| 4–5 | Seam, GH-233 distinction, one PR, Focus 5 deferral, tests, version, rating. | Pass. |

**Plan round 2** (same setup): verdict APPROVE, with one SHOULD.

| # | Finding | Disposition |
|---|---|---|
| 1 | SHOULD: add tests for the depth boundary, the `no_local_data` path and a multi-repo ledger. | Accepted. All three are in `tests/test_releases_scan.py`. |

**Code round 1** (Codex via relay-xyz `consult.sh`, HEAD 53cf23e): verdict CHANGES, with two SHOULDs. Both accepted.

| # | Finding | Disposition |
|---|---|---|
| 1 | SHOULD: the recorded `status_label` is folded into `in-progress`, so clones whose labels differ look like they agree. | Accepted. Each task now carries the raw `status_label`, and conflict detection compares section, status and label. New test `test_recorded_status_label_is_kept_and_compared`. |
| 2 | SHOULD: when one watched repo's command fails and another succeeds, the failure is silent (Req 14). | Accepted. The scanner prints one `daily: <inputs> input partial (N of M repo(s) failed: …)` line and lists the repos in `failed_repos`. This is asserted in the on-mode test. |

**Code round 2** (HEAD aae4921): verdict APPROVE. Both round-1 SHOULDs were verified as resolved, with no new blocker. Its one NIT (a trailing blank line at the end of this doc) is fixed.

## Implementation evidence

- **(b)** `src/rebalance/ingest/releases_scan.py`, the `infer_close_loop_flags(..., releases_scan_dirs=)` hook and the CLI flag. `tests/test_releases_scan.py` (5 tests).
  - Red controls witnessed: swapping in the read-write `db_connection` changes the ledger bytes and fails the test; removing the WAL skip creates a `-shm` sidecar and fails the test.
- **(c)** `collect_close_loop_inputs` in `scan_unclosed_loops.py` (both mirrors) and `SKILL.md` (both mirrors). `tests/test_daily_loop_inputs.py` (5 tests).
  - Red control witnessed: removing the live `OPEN` re-check makes the on-mode test fail (a merged PR would be reported as a loop).
- **Real runs** on the Mini, against a `/tmp` backup-API copy of `rebalance.db`, scanning `~/Documents/GitHub`:
  - `github-close-loop --releases-scan`: 32 ledgers found (31 at recon, plus this task's clone). XYZ-forge has 20 ledgers, 102 tasks, 31 in progress, 2 conflicts and 25 drift; rebalanceOS has 7 ledgers, 88 tasks, 41 in progress, 0 conflicts and 0 drift. 0 ledger errors.
  - `/daily` scanner with both inputs on: 21 flagged loops (18 from the ledger scan, 3 from close-loop flags), 0 unverified, and 60 questions (35 closed without delivery, 25 ledger drift). The run took about 13 s.
  - The ledger fingerprint (path, mtime, size for every `releases.db*` file) was identical before and after both runs.
