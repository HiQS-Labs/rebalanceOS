---
gh_issue: 201
source: https://github.com/HiQS-Labs/rebalanceOS/issues/201
title: "GH-201 — GitHub Ingestion Modernization: 0-API Remote Peeking and Battery-Aware ML (GitCanary Patterns)"
status: "Implementation & Verification Complete (Ready for Codex Final QA)"
created: 2026-09-08
updated: 2026-09-08
owner: noel
doc_type: architecture
rating: "pri/sev/appeal/effort 90/80/90/40 · calc 300"
effort: 3
complexity: 3
risk: 2
phases: 3
ratings_provisional: false
goal: >
  Modernize RebalanceOS's GitHub ingestion by adopting high-leverage architectural patterns from GitCanary:
  Zero-API remote branch peeking via git ls-remote to short-circuit redundant local commit walking,
  hardware/battery-aware throttling of ML embeddings while preserving document projection, and multi-worktree
  probe deduplication via Focus 5 inventory.
non_goals:
  - Skipping issue/PR metadata sync based on branch tip SHA (issues/reviews change without commits moving).
  - Modifying PR-scoped commit fetching or check-run refresh in sync_github_repo (commit gating is strictly confined to local backfill).
  - Modifying sync_github_repo's PR timestamp gating (check-run freshness under unchanged PRs is deferred).
  - Network reachability preflight in launchd/adapters (deferred pending reproduction of wake-up auth failure claims).
  - Replacing the GitHub REST API for non-local / external watched repositories.
  - Building a macOS GUI or menu-bar app for RebalanceOS (remains headless daemon / CLI / library).
  - Merging candidate digest / unread cursors into this PR (deferred to a dedicated next-actions slice).
  - Adding a new Flightdeck collector or session-context tracking (independent of XYZ-forge #494).
  - Active-worktree next-action prioritization (deferred; multi-worktree scope here is probe deduplication only).
---

# GH-201 — GitHub Ingestion Modernization (GitCanary Patterns)

## Context & Motivation

A comparative architectural audit between RebalanceOS's GitHub ingestion (`src/rebalance/ingest/index_ops.py`, `github_scan.py`, `github_knowledge.py`) and GitCanary (a local-first macOS git monitor) revealed key structural improvements.

While RebalanceOS provides deep cross-repo artifact ingestion (issues, PRs, comments, reviews, check-runs, vector embeddings), it suffers from two operational friction points:
1. **Redundant Commit History Walks**: `github_commit_backfill.py` unconditionally walks all origin refs across local checkouts even when remote branch tips have not moved.
2. **Thermal & Battery Drain on Portable Macs**: ML vector embedding passes (`embed_github_documents`, MLX / MPS neural engine) run unconditionally on battery power.

Following Codex QA reviews (Rounds 1–3), the plan is surgically bounded to local commit walking and embedding deferral with verified recovery and completion contracts.

---

## Code Seam Reuse & Architecture Map

Per Codex QA findings, existing RebalanceOS subsystems are reused directly with zero parallel abstraction sprawl:
* **Hardened Subprocess Boundary**: `src/rebalance/lib/git_ops.py:88` (`run_git`) is extended with an optional `extra_env: dict[str, str] | None = None` parameter for per-call environment isolation without mutating process-wide environment.
* **`ls-remote` Reference Implementation**: `src/rebalance/ingest/github_coverage.py:122` (`remote_tip()`) is consolidated to use the hardened `run_git` boundary with non-interactive and child-cleanup protections.
* **Workspace Worktree Inventory**: `iter_git_repos` at `src/rebalance/ingest/focus5_scan.py:456` and clone resolution at `src/rebalance/ingest/github_commit_backfill.py:151, 166` are reused to resolve and deduplicate clone paths by canonical remote URL.
* **Document Projection vs. Vector Embedding**: 
  - `backfill_semantic_documents` in `src/rebalance/ingest/semantic_index.py:533` and `index_ops.py:1160` are **document projection functions**. They MUST continue running on battery.
  - Only `embed_pending` / `embed_semantic_pending` and `embed_github_documents` are gated when on battery power. Deferred rows remain in `pending` state in `semantic_documents`.

---

## Phased Architecture & Execution Plan

### Phase 0: Technical Spike — Two-Stage "Safe Read/Write" Compatibility Harness (Timeboxed 1–2h)
*Objective*: De-risk git subprocess execution across live repository configurations and prove the write/rollback caching contract inside a safe, isolated database sandbox before touching `index_ops.py`.

#### Stage 0A: Live Read-Only Compatibility Probe (Zero Production Mutation)
- [x] **Strict Production Read-Only Guarantee**:
  - Open production `rebalance.db` strictly via URI `file:... ?mode=ro` or `PRAGMA query_only = ON`.
  - Zero DDL execution (no schema-initializing DB helpers like `ensure_github_schema`), zero SQL `INSERT`/`UPDATE` calls, and zero git mutations (`fetch`/`pull`/`checkout`).
- [x] **Affected-Systems Integration Sweep**:
  - **`project_registry` & Workspace Resolvers** (`rebalance.ingest.registry`): Read all local project repository paths from disk and verify clean canonical remote URL resolution.
  - **Target Repo Resolver** (`index_ops._resolve_repos_for_refresh`): Validate that target repos resolved by Rebalance cleanly map to local clones vs. external watchlists.
  - **Multi-Worktree Layouts** (`focus5_scan.py:456`): Test behavior on linked worktrees (`.git` file referencing common git dir) vs. standard `.git` directories. Deduplicate probes by canonical remote URL + ref set across clones/worktrees.
  - **Coverage & Backfill Baseline** (`github_coverage.remote_tip`, `github_commit_backfill.py`): Compare existing bare HTTPS `remote_tip` against the hardened local-clone peeker.
  - **Headless Environment Probe**: Execute in a sanitized subshell simulating macOS `launchd` (no interactive TTY, stripped env vars, preserve existing SSH config + append `BatchMode=yes`).
- [x] **Subprocess Safety Matrix & Test Cases**:
  - Extend `src/rebalance/lib/git_ops.py:run_git` with `extra_env: dict[str, str] | None = None` ensuring per-call isolation.
  - Non-interactive flags: `GIT_TERMINAL_PROMPT="0"`, `GIT_SSH_COMMAND` appends `-o BatchMode=yes -o ConnectTimeout=5`.
  - Test Case 1: HTTPS with credential-helper / askpass — asserts no interactive hang occurs.
  - Test Case 2: Conflicting SSH command options — asserts clean failure without weakening host-key verification.
  - Test Case 3: Offline network (exit 128) — returns `None` (Unknown), does not raise.
  - Test Case 4: Absent git binary — degrades to authoritative fallback.
  - Test Case 5: Detached / unborn HEAD — peeks explicit named remote ref without error.
  - Test Case 6: Subprocess timeout & zombie cleanup — verifies child process is terminated and no helper survives timeout.
  - Test Case 7: Empty, malformed, or missing-ref output — properly parses as `None` (Unknown).
  - Strict 2.0s timeout per probe and 15s whole-run budget (covering discovery, baseline, and cleanup).
  - Budget exhaustion policy: Repos exceeding budget fall back to normal authoritative ingestion (disabling the peek optimization, never dropping or skipping repos).
- [x] **Go / No-Go Stop Rule**:
  - If any test reveals a prompt hang, askpass hang, or child-process leak: HALT rollout.
  - If average `git ls-remote` probe latency on local clones exceeds 500ms: HALT rollout.
  - **Campaign Verdict**: **NO-GO (HALT ROLLOUT)**. Average probe latency on local clones was 609.1ms (exceeding the 500ms ceiling). All 7/7 subprocess safety cases and 9/9 Stage 0B sandbox recovery tests passed.
  - **Rollout Enforcement**: To strictly honor the Stop Rule without loosening the threshold, the remote peeking optimization is **DISABLED BY DEFAULT** in production (`enable_remote_peeking = False` via `rebalance.ingest.config`). Live backfill bypasses peeking probes unless explicitly enabled. Rollout is halted pending passing network conditions or explicit operator sign-off.
  - **Independent Phase 2**: Battery-aware ML embedding deferral (Phase 2) is independent of the network gate, fully verified across both stores, and enabled by default.
- [x] Deliverable 0A: Benchmark protocol and read-only matrix published in `TESTS-RESULTS/` per SOP §§1–3, reporting: `Repo | Canonical Remote URL | Branch | Remote Peek SHA | SQLite Stored SHA | Divergence Match? | Latency (ms) | Probe Status`.

#### Stage 0B: Isolated Sandboxed Read/Write Contract Test (Zero Production Risk)
- [x] **Disposable Database Sandbox**:
  - Clone production `rebalance.db` schema into a temporary database (`tempfile.NamedTemporaryFile`).
  - Initialize the new `github_remote_peeks` table via standard production schema helper (`ensure_github_schema`).
  - Seed known checkpoint rows plus non-empty pending documents across **both stores** (`semantic_documents` and `github_knowledge`).
- [x] **Production Completion Predicate Verification & Controls (Codex R2)**:
  - Call the exact production completion predicate: require equality of the **complete canonical ref-name -> SHA map across all origin branches** (`refs/remotes/origin/*`), matching `--remotes=origin` (`github_commit_backfill.py:295, 319`), and adequate history window (`since <= covered_since_utc`). Missing or unverified remote proof forces normal authoritative backfill.
  - **Failed-File-Read -> Retry Control**: Simulate `git show` file-read failure on a commit; verify commit is NOT marked complete and checkpoint advance is REFUSED, remaining retryable at both row and checkpoint levels.
  - **Unchanged-Default-Tip / Changed-Other-Branch Control**: Verify that when `main` tip is unchanged but a secondary branch moves, cache hit is rejected and authoritative walk runs.
  - **Ref Addition / Deletion Control**: Verify that newly pushed branches or deleted branches invalidate the cached ref map.
  - **Stale Overlap Control**: Verify that an older/slower overlapping backfill run (`SCHEDULER.md:72`) cannot overwrite a newer checkpoint (conditional update rejecting stale timestamps).
  - **Negative Control**: Deliberately simulate a partial/broken checkpoint advance and assert that the test suite catches and fails it.
  - Test cache invalidation: Widened lookback window (`since` earlier than recorded) or `--no-cache` forces full backfill.
  - Verify first-run / cache-miss executes full backfill and establishes the initial checkpoint.
  - Verify `--dry-run` is 100% probe-free and write-free.
- [x] **Two-Store Battery Recovery Contract Tests (Codex R3)**:
  - Seed non-empty fixtures for both stores with existing vectors plus pending documents:
    - Store 1: `semantic_index` (`embed_semantic_pending`, reset path at `src/rebalance/ingest/semantic_index.py:691`)
    - Store 2: `github_knowledge` (`embed_github_documents`, reset path at `src/rebalance/ingest/github_knowledge.py:911`)
  - Battery run assertions: Existing vectors are untouched; pending markers remain intact; projection runs to completion; exactly zero ML model calls occur.
  - AC reconnection assertions: The next AC refresh via default recipe `refresh_index(db_path)` (or `scope=["github", "semantic"]`) embeds all eligible pending backlog across both stores without duplicate rows and without requiring upstream source changes.
  - Edge cases tested: `force_reembed=True` on battery (preserves existing vectors without destructive deletion), startup-on-AC then unplug (startup-only policy), disabled config (`defer_embeddings_on_battery=False`), and unknown power fallback.
  - **Red Control**: A test control that deliberately bypasses the power decision and fails the battery assertions, with results recorded in the campaign report.
- [x] Automatic teardown: disposable sandbox is purged cleanly upon test completion.

---

### Phase 1: Repo-Level Commit Gating & Atomic Checkpoint Cache
*Objective*: Short-circuit expensive local commit history walking (`github_commit_backfill.py`) when remote branch SHAs are unchanged (Rollout Status: Implemented & fully verified; disabled by default via config flag pending Phase 0 stop-rule disposition).

- [x] **Strict Scope Boundary (Codex R1)**: Gating applies **exclusively to the local commit history walk in `github_commit_backfill.py`**. `sync_github_repo` (issues, PRs, comments, reviews, check-runs, and PR commit endpoints) remains 100% authoritative and untouched by this gate.
- [x] Single Checkpoint Writer: `record_commit_coverage_checkpoint(conn, canonical_remote_url, ref_digest, sha_map_json, covered_since_utc)` in `github_commit_backfill.py`.
- [x] SQLite Cache Table: `github_remote_peeks (canonical_remote_url TEXT, ref_digest TEXT, sha_map_json TEXT, covered_since_utc TEXT, verified_at TEXT, PRIMARY KEY(canonical_remote_url))`.
- [x] Complete Ref-Map Cache-Hit Equality: Match requires identical ref-name -> SHA mapping across all canonical origin branches (`refs/remotes/origin/*`) and requested lookback window covered by `covered_since_utc`.
- [x] Conditional Checkpoint Update & Overlap Policy: Update uses a conditional SQL check (`UPDATE github_remote_peeks ... WHERE canonical_remote_url = ? AND (verified_at <= ? OR verified_at IS NULL)`) and transactional verification, rejecting stale completion from overlapping daily/hourly runs (`SCHEDULER.md:72`).
- [x] Checkpoint advances only to pre-sync captured SHAs after successful completion of enumeration and per-commit reads, with zero network wait inside the write transaction.
- [x] Authoritative local walk retained whenever local clone is missing, divergent, or `git ls-remote` returns unverified status.
- [x] Regression Fixtures: Add non-empty unchanged-repo-SHA/changed-issue fixture and newly discovered PR fixture to verify that existing metadata polling is completely preserved.

---

### Phase 2: Hardware & Battery-Aware Embedding Deferral
*Objective*: Adopt GitCanary's `PowerMonitor` posture to preserve battery life and prevent thermal throttling on portable Macs.

- [x] Add `rebalance.lib.power_ops` inspecting power source via macOS `pmset -g batt` / `IOPowerSources` (neutral fallback on non-macOS).
- [x] Configuration: `defer_embeddings_on_battery: bool` (default: `true`).
- [x] **Durable Two-Store Recovery Contract (Codex R3)**:
  - Startup-only check per refresh invocation, placed BEFORE model loading or destructive `force_reembed` vector clearing.
  - When on battery: Document projection (`backfill_semantic_documents` and `index_ops.py:1160`) runs normally.
  - Heavy ML model embedding (`embed_pending`, `embed_semantic_pending`, `embed_github_documents`) is deferred.
  - Existing vectors in both `semantic_index` and `github_knowledge` are preserved; new documents remain safely in `pending` state without loss of history.
  - Scheduled runs on AC power via the default recipe `refresh_index(db_path)` (or `scripts/daily_sync.sh`) and explicit two-store refresh `refresh_index(db_path, scope=["github", "semantic"])` drain both embedding stores without requiring another source change.
  - Unknown power or disabled config defaults to AC power behavior.
  - Expose honest `power_deferred` indicators in `index_status` signal health without altering stuck-row thresholds.

---

## Acceptance Criteria

1. Phase 0 spike proves safe, non-interactive execution with named assertions across offline, timeout, askpass, conflicting SSH options, and detached HEAD cases; Stage 0B validates production completion predicate with failed-file-read retry, branch addition/deletion, out-of-order overlap protection, and negative broken-checkpoint control.
2. Unchanged local repositories skip redundant commit history walks when remote peeking is enabled, while remaining safely disabled by default per Phase 0 Stop-Rule NO-GO; sync_github_repo continues authoritative metadata polling, confirmed by non-empty unchanged-repo-SHA/changed-item and newly discovered PR fixtures.
3. Startup-only power throttling halts `embed_pending`, `embed_semantic_pending`, and `embed_github_documents` on battery before model loading or vector reset across both `semantic_index` and `github_knowledge` stores, with zero model calls and intact vectors; AC reconnection via default recipe `refresh_index(db_path)` cleanly drains backlog without duplicates; verified with a red control.
4. All existing pytest suites (`tests/test_github_*.py`, `tests/test_index_ops.py`) remain 100% green.
