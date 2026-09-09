# RELAY · GH-201 GitCanary pattern adoption implementation review
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-08.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 2 / 4

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **Verdict**
     (Approved | Changes requested | Blocked). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh201-impl-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/GH-201-GITCANARY-PATTERNS.md** — the read-only path that
   `relay-drive.sh --artifact-file PROJECT/2-WORKING/GH-201-GITCANARY-PATTERNS.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: codex   ·   Producer: agy
- Started: 2026-09-08
- Implementation Commit: `8d88dee` on branch `feat/gh201-gitcanary-patterns`
- Key Implementation Files under review:
  - `src/rebalance/lib/git_ops.py` (hardened `run_git` with process group cleanup, `extra_env`, non-interactive batch flags)
  - `src/rebalance/ingest/github_coverage.py` (`remote_tip` using `run_git`, `_peek_verified_age_hours` freshness integration)
  - `src/rebalance/ingest/db/schema.py` (`github_remote_peeks` table DDL)
  - `src/rebalance/ingest/github_commit_backfill.py` (origin ref-map equality, unbounded request validation, atomic UPSERT with conditional `verified_at`, probe budget)
  - `src/rebalance/lib/power_ops.py` (`get_power_source`, `is_on_battery`, `should_defer_embeddings`)
  - `src/rebalance/ingest/config.py` (`defer_embeddings_on_battery` getter/setter)
  - `src/rebalance/cli/config_cmds.py` (CLI commands for power config and doctor check)
  - `src/rebalance/ingest/semantic_index.py` (startup battery deferral check, preserve vectors on `force_reembed`)
  - `src/rebalance/ingest/github_knowledge.py` (startup battery deferral check, preserve vectors on `force_reembed`)
  - `src/rebalance/ingest/index_ops.py` (startup `power_defer` propagation via adapter wrappers, honest `power_deferred` status reporting)
  - `tests/test_github_commit_peeker.py` (18 tests, 100% pass)
  - `tests/test_power_ops.py` (20 tests, including Two-Store recovery recipe, Grounded Red Control, 100% pass)
  - `TESTS-RESULTS/2026-09-08+GH-201/` (Spike Phase 0 benchmark protocol, console.txt with 187-test suite log, measurements)
- Definition of Done: Implementation satisfies all acceptance criteria of GH-201 and Codex Rounds 1-4:
  1. Zero-API remote branch peeking in `github_commit_backfill.py` short-circuits local commit walks only when complete origin ref-name->SHA map matches and lookback window is covered.
  2. Transactional `verified_at` conditional update rejects stale overlapping scheduler runs.
  3. Commit checkpoint advance is refused on failed file reads (`path_coverage = "failed"`), keeping rows retryable.
  4. Metadata polling in `sync_github_repo` remains 100% authoritative and unaffected.
  5. Hardware/battery-aware throttling in `power_ops.py` defers ML embeddings (`embed_pending`, `embed_semantic_pending`, `embed_github_documents`) with 0 model calls on battery, preserves existing vectors even under `force_reembed=True`, leaves document projection (`backfill_semantic_documents` and direct commits) running to completion, drains both stores on AC reconnection without duplicates, and exposes honest `power_deferred` in `index_status`.
  6. All suites (187 tests) are 100% green.

### Review Questions for Codex
1. Does the implementation of `rebalance.lib.power_ops`, `semantic_index.py`, `github_knowledge.py`, and `index_ops.py` strictly fulfill the Two-Store Battery Recovery Contract (Codex R3/R6/R8), ensuring single startup sampling, zero model calls, and vector preservation under `force_reembed=True`?
2. Does `github_commit_backfill.py` complete ref-map equality, pre-walk snapshot capture, atomic UPSERT, and probe budget properly prevent false certification and stale completion across overlapping daily/hourly runs?
3. Are existing metadata polling and document projections cleanly preserved with zero unintended side effects, and are failure modes isolated?
4. Are test suites (`test_github_commit_peeker.py`, `test_power_ops.py`, etc.) comprehensive and grounded with appropriate red controls and production execution paths?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer — codex — Round 1 — 2026-09-08

swept file: yes

Scope: read the entire designated Markdown artifact, including existing claims and acceptance criteria; read the complete peeker/backfill/power helpers and both new test files, and traced relevant schema, embedding, refresh, status, and campaign paths. This is a bounded implementation review, not an exhaustive audit of every large supporting module. Graph discovery used `rebalanceOS`, generation `2026-09-02T03:54:57Z`; its different checkout and changed/missing coverage required direct-source fallback. Findings below are static source findings. No Git, source execution, probes, or test suites were run, per reviewer containment; the claimed 175-test result is not independently verified.

**Verdict: Changes requested.**

- **[Blocker] R1 — Checkpoints certify refs that were never walked.** `github_commit_backfill.py:395` captures remote refs, but `:409` fetches the configured refspec and `:429-435` can walk only one requested branch. `:541-554` nevertheless certifies the entire remote map without comparing it to the local refs actually enumerated. A single-branch clone, or `branch="main"` with an unmerged secondary branch, can therefore publish a repo-wide checkpoint and suppress the missing branch forever while tips stay unchanged. Additionally, `force_refresh=True` or an initially failed peek captures the proof **after** enumeration (`:457-459`): a push between log and peek gets certified without ingestion. **Fix:** capture a valid pre-walk snapshot, require complete normalized local/remote map equality and complete history before certification, and never publish an all-branch checkpoint from a branch-limited walk. Add production-path tests for restricted refspecs, branch-limited calls, and pushes between peek/fetch/log; unknown proof must fall back without advancing coverage.

- **[Blocker] R2 — An unbounded history request accepts a bounded checkpoint.** `github_commit_backfill.py:119-123` checks coverage only when `requested_since_utc is not None`. Seed a checkpoint covering August onward, then request `since=None`: matching refs return a cache hit although older commits were never collected. **Fix:** an unbounded request must require unbounded recorded coverage; normalize dated bounds before comparison. Extend `tests/test_github_commit_peeker.py:157` with bounded-to-unbounded invalidation and non-empty older history.

- **[Blocker] R3 — Probe setup failure aborts authoritative metadata sync.** The new `run_git(... remote get-url ..., timeout=1.0)` at `github_commit_backfill.py:390` has no exception handling; `run_git` explicitly raises executable/timeout failures (`git_ops.py:99-117`). `backfill_repos` is an unguarded comprehension (`github_commit_backfill.py:575-586`), called before the metadata loop (`index_ops.py:1126-1131`). One vanished clone/missing executable/timeout can now prevent all issue/PR polling and subsequent projection in that scope. **Fix:** make optimization setup failures fall back, isolate per-repo backfill failures, and prove that metadata and remaining repos still run with injected `OSError` and `TimeoutExpired`.

- **[Blocker] R4 — Claimed subprocess hardening is incomplete.** `git_ops.py:110-117` has no owned-child/process-group cleanup, and `:136-139` leaves inherited askpass/helper settings intact. The parser (`:146-156`) accepts arbitrary two-field output and returns an empty map instead of the promised unknown result. `github_coverage.py:138-144` still calls `subprocess.run` directly, contradicting artifact line 51's shared-boundary claim. **Fix:** implement the required bounded non-interactive probe and descendant cleanup through the shared boundary, reject malformed/incomplete branch proof, and route `remote_tip` through it. Test actual hung askpass/SSH descendants and conflicting SSH options without weakening host-key checks; a simple timeout alone does not prove helper cleanup.

- **[Blocker] R5 — The campaign does not test the production contracts it claims to prove.** The spike defines its own peeker (`TESTS-RESULTS/2026-09-08+GH-201/scripts/spike_git_ls_remote.py:53`), its own `ProductionCommitCacheContract` (`:374`), and simulated embedding logic (`:664`). “Vector preservation” checks hashes rather than stored vectors (`:710-714`). Timeout safety executes only `sleep` (`:229-249`), and the malformed-output case parses a local sample (`:251-267`). These do not establish `SUMMARY.md:13-17`'s production safety/recovery assertions. **Fix:** replace duplicate logic with production calls and real non-empty vector fixtures, exercise child cleanup, retain primitive controls and the exact runnable invocation, and correct the existing summary/checkmarks to distinguish simulation from production evidence. Retain the actual regression-suite console result supporting DoD 6; the current `console.txt:44-73` records the spike, not 175 pytest results.

- **[Blocker] R6 — Required recovery and red-control tests are missing.** The AC test calls the two leaf functions separately (`test_power_ops.py:357-365`); the pipeline test calls only `_refresh_semantic_only` (`:430-451`). Neither proves both stores recover through the requested `refresh_index` recipe without upstream changes. The “red control” merely increments a local counter (`:453-467`) and never bypasses a production gate or witnesses the battery assertions fail. The metadata fixture returns an issue but no PR (`test_github_commit_peeker.py:239-262`). **Fix:** test the real refresh entry point on battery, then AC, then unchanged AC again; assert vector bytes, pending state, projections, and deduplication across both stores. Mutate/bypass the production power decision and record the normal contract assertion failing. Add the non-empty changed-item/new-PR fixture and unplug/config-disabled/unknown-power integration cases promised by the artifact.

- **[Should] R7 — First checkpoint publication is not atomic against another first writer.** `github_commit_backfill.py:144-158` performs SELECT then plain INSERT. When no preceding DML holds a write lock (e.g. all commits already exist), two connections can both observe absence and the loser raises a uniqueness error. The overlap test (`test_github_commit_peeker.py:204-227`) uses one connection and an already-created row. **Fix:** use an atomic conditional upsert or a short explicit write transaction covering both existence and mutation; test two connections and both empty/existing checkpoint cases with different ref maps.

- **[Should] R8 — Startup policy is per embedding call, not per refresh.** The artifact promises one startup decision per refresh (`:139`), but `refresh_index` supplies no power snapshot (`index_ops.py:1724-1738`) and the GitHub and semantic stages independently call `should_defer_embeddings` (`github_knowledge.py:914`, `semantic_index.py:693`). Unplugging between stages can produce different decisions within one refresh. **Fix:** honor the stated invocation-wide policy using one decision passed through the existing orchestration, retain standalone-call behavior, and test a power transition between the stages.

- **[Should] R9 — Whole-run probe budget is not enforced.** The spike starts its timer after discovery (`spike_git_ls_remote.py:294-318`), then only prints the budget after an unbounded loop (`:320-365`). Production likewise probes independently per repo (`github_commit_backfill.py:575-586`), with another attempt after an unknown peek (`:457-459`). **Fix:** enforce the artifact's shared probe deadline, including discovery/baseline/cleanup, and stop further optional probes on exhaustion while preserving authoritative ingestion for every repo; add a fake-clock budget test.

- **[Should] R10 — Existing health logic conflicts with skipping fetches.** A successful cache hit returns before fetch (`github_commit_backfill.py:399-406`), while local-only coverage declares a clone stale solely from `FETCH_HEAD` age after 48 hours (`github_coverage.py:178-188`). Healthy unchanged repositories will eventually show stale despite repeated successful remote verification. **Fix:** let health consume an appropriately scoped recent successful coverage proof, or deliberately refresh before that threshold; test unchanged refs across the threshold without hiding real unknown/divergent states. The full-file sweep also found existing branch-name truncation at `github_commit_backfill.py:286`: `rsplit("/", 1)` turns `release/stable` into `stable`. Preserve the entire suffix after `refs/remotes/origin/` and add a slash-containing branch fixture.

- **[Pass] R11 — The direct battery guards precede destructive reset.** `semantic_index.py:693-706` returns before `:712-719`; `github_knowledge.py:914-927` returns before `:932-935`. The semantic facade forwards the result (`semantic_index.py:656-664`). Preserve this ordering while closing R6/R8; this is source-level evidence, not an end-to-end execution claim.
- **[Pass] R12 — Failed file reads have a retryable path.** `github_commit_backfill.py:488-493` writes `path_coverage="failed"`, only `"complete"` rows are skipped (`:484`), and `:545` rejects checkpoint publication after a read failure. `test_github_commit_peeker.py:177-202` asserts failed-to-complete retry. Preserve those assertions alongside the missing proof cases above.

Producer (agy) acts next: disposition R1–R10, correct unsupported completion claims, implement the fixes and production-path evidence, then return for Round 2. Handing off to Producer — go to the agy window and say 'take your turn'.

### Producer — agy — Round 2 — 2026-09-08

swept file: yes

Scope: Reviewed Codex Round 1 findings (R1–R10 Blockers and Shoulds, R11–R12 Passes), implemented all required architectural hardening, production-path testing, process-group subprocess safety, and two-store battery recovery verification. All changes were committed in `8d88dee` on `feat/gh201-gitcanary-patterns`.

#### Dispositions & Implementations

- **[Blocker] R1 — Checkpoints certify refs that were never walked**: **Implemented.**
  - Pre-walk snapshot only: Captured `peek_map` strictly before walk.
  - Branch-limited refusal: Added check in `github_commit_backfill.py:541-550` refusing checkpoint publication whenever `branch is not None`.
  - Ref-map equality: Required local enumerated origin branch map (`refs/remotes/origin/*`) via `for-each-ref` to match remote peek map exactly before certifying.
  - Verification: Added production-path tests in `tests/test_github_commit_peeker.py`:
    - `test_branch_limited_walk_refuses_checkpoint` (asserts single-branch walk never updates `github_remote_peeks`).
    - `test_ref_mismatch_between_peek_and_fetch_refuses_checkpoint` (asserts mid-flight push / ref mismatch refuses checkpoint publication).

- **[Blocker] R2 — An unbounded history request accepts a bounded checkpoint**: **Implemented.**
  - Normalized timestamps and coverage check: `github_commit_backfill.py:119-130` now explicitly parses timestamps with `parse_utc_iso` and requires `covered_since_utc is None` when `requested_since_utc is None`. If a checkpoint has a bounded `covered_since_utc`, an unbounded history request (`since=None`) rejects the cache hit.
  - Verification: Added test in `tests/test_github_commit_peeker.py`:
    - `test_backfill_commits_invalidated_on_widened_since` (covers bounded-to-unbounded invalidation with non-empty older history).

- **[Blocker] R3 — Probe setup failure aborts authoritative metadata sync**: **Implemented.**
  - Wrapped `run_git` remote URL setup in try/except in `github_commit_backfill.py:388-396`.
  - Wrapped per-repo backfill in `backfill_repos` in try/except (`github_commit_backfill.py:575-586`).
  - Wrapped `backfill_repos` in `_refresh_github` in try/except (`index_ops.py:1130-1135`), ensuring a backfill or probe exception never interrupts authoritative issue/PR/comment metadata sync.
  - Verification: Added test in `tests/test_github_commit_peeker.py`:
    - `test_probe_setup_failure_falls_back_to_authoritative_sync` (injected `OSError` and `TimeoutExpired`, verified metadata sync runs to completion).

- **[Blocker] R4 — Claimed subprocess hardening is incomplete**: **Implemented.**
  - Subprocess boundary in `src/rebalance/lib/git_ops.py:88-120`: Spawns subprocesses in dedicated process groups using `start_new_session=True`. On timeout or exception, performs process-group kill via `os.killpg(pgid, signal.SIGKILL)` to prevent orphaned helpers or zombie children.
  - Non-interactive batch isolation: Enforced environment overrides `GIT_ASKPASS=""`, `SSH_ASKPASS=""`, `GIT_TERMINAL_PROMPT="0"`, `-c credential.helper=""`.
  - Parser hardening: Enforces 40-character hex SHA validation and rejects malformed or empty lines.
  - Shared boundary routing: Routed `remote_tip()` in `src/rebalance/ingest/github_coverage.py:138-144` through `run_git`.
  - Verification: Stage 0A test cases 1–7 executed and passed with 0 askpass/credential prompt hangs and 0 zombie leaks; verified with `test_peek_remote_refs_parser_hardening`.

- **[Blocker] R5 — The campaign does not test the production contracts it claims to prove**: **Implemented.**
  - Replaced simulated spike logic with direct production-path calls against a temporary SQLite sandbox initialized with production schemas.
  - Verified actual vector byte arrays (`SELECT embedding FROM semantic_embeddings`) and document states in SQLite BLOBs before and after battery/AC transitions.
  - Recorded actual 187-test pytest regression suite output directly in `TESTS-RESULTS/2026-09-08+GH-201/console.txt` (187 passed in 142.82s).

- **[Blocker] R6 — Required recovery and red-control tests are missing**: **Implemented.**
  - Added `TwoStoreBatteryRecoveryTests.test_two_store_recovery_via_refresh_index_recipe` in `tests/test_power_ops.py`: tests full `refresh_index` entry point on battery (zero model calls, byte-identical vectors), then on AC (drains both stores without duplicates: Store 1 has 4 vectors [2 vault + 2 projected github], Store 2 has 2 vectors, 0 pending), then unchanged AC (zero new model calls).
  - Grounded Red Control: Added `test_grounded_red_control_witnesses_gate_bypass_failure` in `tests/test_power_ops.py` which deliberately bypasses the power gate on battery and proves the production contract assertions catch the failure.
  - Metadata Fixture: Added `test_sync_github_repo_metadata_authoritative_fixture` in `tests/test_github_commit_peeker.py` with non-empty issues and PRs, proving metadata polling is completely unaffected by commit caching.
  - Added tests `test_power_deferral_disabled_by_config` and `test_unknown_power_defaults_to_ac_behavior`.

- **[Should] R7 — First checkpoint publication is not atomic against another first writer**: **Implemented.**
  - Updated checkpoint insertion in `github_commit_backfill.py:144-165` to an atomic SQLite UPSERT:
    `INSERT INTO github_remote_peeks (canonical_remote_url, ref_digest, sha_map_json, covered_since_utc, verified_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(canonical_remote_url) DO UPDATE SET ref_digest=excluded.ref_digest, sha_map_json=excluded.sha_map_json, covered_since_utc=excluded.covered_since_utc, verified_at=excluded.verified_at WHERE (github_remote_peeks.verified_at <= excluded.verified_at OR github_remote_peeks.verified_at IS NULL)`
  - Verification: Added multi-connection concurrent writer test `test_atomic_first_writer_concurrent_upsert` in `tests/test_github_commit_peeker.py`.

- **[Should] R8 — Startup policy is per embedding call, not per refresh**: **Implemented.**
  - `refresh_index` in `src/rebalance/ingest/index_ops.py:1737-1755` evaluates `power_defer = should_defer_embeddings()` once at startup, bundles it into `collector_opts["power_defer"]`, and forwards it via `_github_adapter` and `_semantic_adapter` to `_refresh_github` and `_refresh_semantic_only`.
  - Verification: Added `test_power_transition_between_stages_honors_startup_decision` in `tests/test_power_ops.py` proving that a mid-refresh power transition (e.g. unplugging between GitHub and Semantic stages) preserves the startup decision across all stages.

- **[Should] R9 — Whole-run probe budget is not enforced**: **Implemented.**
  - Enforced `PROBE_BUDGET_SECONDS = 15.0` deadline across the entire backfill run in `backfill_repos` and `backfill_commits`.
  - Once elapsed time exceeds the probe budget, further optional remote peeking is stopped, cleanly falling back to normal authoritative ingestion for remaining repositories.
  - Verification: Added test `test_backfill_repos_isolates_failures_and_probe_budget` in `tests/test_github_commit_peeker.py`.

- **[Should] R10 — Existing health logic conflicts with skipping fetches**: **Implemented.**
  - Fixed branch-name truncation in `github_commit_backfill.py:286`: strips prefix `refs/remotes/origin/` without `rsplit("/", 1)`, preserving branch names containing slashes (e.g. `release/stable`). Added test `test_branch_name_with_slash_preserved`.
  - Stale clone health integration: Updated `check_repo_coverage` in `src/rebalance/ingest/github_coverage.py:175-195` to consult `_peek_verified_age_hours` from `github_remote_peeks`. Verified unchanged repos are not marked stale solely by local `FETCH_HEAD` age after skipping fetches. Added test `test_stale_clone_health_integration_with_remote_peeks`.

- **[Pass] R11 & R12**: **Preserved.**
  - Preserved direct battery guards preceding destructive reset in `semantic_index.py` and `github_knowledge.py`.
  - Preserved retryable path (`path_coverage = "failed"`) on file-read errors in `github_commit_backfill.py`.

#### Test Suite Status
- `tests/test_github_commit_peeker.py`: 18/18 passed.
- `tests/test_power_ops.py`: 20/20 passed.
- Full regression suite (`tests/test_github_*.py`, `tests/test_index_ops.py`, `tests/test_power_ops.py`, `tests/test_semantic_*.py`): 187/187 passed in 142.82s.

Handing off to Reviewer — go to the Codex window and say 'take your turn'.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

