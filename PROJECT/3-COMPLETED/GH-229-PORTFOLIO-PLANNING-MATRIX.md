---
gh_issue: 229
source: https://github.com/HiQS-Labs/rebalanceOS/issues/229
title: Executive portfolio planning matrix view in decoupled standalone macOS app & local API
status: Complete
created: 2026-09-15
updated: 2026-09-22
owner: Maintainer
doc_type: execution_plan
rating: pri/sev/appeal/effort 70/50/75/50 · calc 245
effort: 3
complexity: 2
risk: 1
phases: 3
goal: >
  Provide an always-on-top, instant-glance Executive Portfolio Matrix HUD via a decoupled
  standalone macOS app (macOS/Apps/PortfolioMatrix), leaving Focus5Float 100% untouched, backed
  by a single read-only projection endpoint (GET /portfolio-matrix.json) in rebalance serve, sourced
  strictly from project_registry and project-sectioned 0. Goals.md, with task completions routing
  exclusively through the existing single writer path (POST /api/focus5/goals/complete) hardened with
  goals_revision optimistic concurrency, single-dispatch POST execution, and AmbiguousGoalError (HTTP 409),
  plus an interactive '+' quick-issue modal with canonical PRS 1-400 override (default 200).
non_goals:
  - Modifying the existing Focus5Float app (Focus5Float remains 100% untouched to ensure zero blast radius)
  - Multi-repo releases.db querying in v1 (deferred to v2; v1 strictly uses project_registry + 0. Goals.md)
  - Cold-start disk caching for the matrix in v1 (v1 retains in-memory state on transient errors; mutations disabled offline)
  - Creating any new database, tables, or persistence engines (re-uses project_registry in rebalance.db)
  - Creating a parallel task completion engine (re-uses POST /api/focus5/goals/complete -> goals_file.complete_goal_in_file)
  - Arbitrary cell-by-cell spreadsheet formula editing (v1 is an operational HUD with actionable task pills)
---

# Executive Portfolio Planning Matrix (#229)

## Problem & Operational Context

The operator steers multi-project execution using a 2D matrix spreadsheet ("2026 - Q3 Planning") tracking ~12 portfolio projects and subprojects (Binoid/Bloomz, Inspired Magazine, MangaJDM, XYZ-Forge, AEGIS Sleuth, Meetup groups, Bailiwik, CreditRegistry, Nexus AI).
Each project row presents:
1. Project name & Sub-project hierarchy.
2. Value metrics: Revenue Ranking (1–5), Revenue Potential, Computed Score.
3. Immediate execution front: **Task 1**, **Task 2**, **Task 3** laid out horizontally side-by-side.
4. Quick-add capability: inline `＋` button opening a new issue modal pre-selected to that project with a PRS override (1–400, default 200).

GitHub Projects v2 cannot natively render this view because its data model is strictly 1 Item = 1 Row / Card (columns represent item metadata attributes, not sibling tasks; sub-issues expand vertically down, breaking 2D scannability). Meanwhile, a web dashboard tab is easily buried beneath IDE and terminal windows.

The solution is an always-on-top Executive Matrix HUD inside a decoupled standalone macOS app (`macOS/Apps/PortfolioMatrix`), completely decoupled from `Focus5Float` so that Focus 5 code is untouched, pulling from a single local endpoint (`GET /portfolio-matrix.json`) and preserving existing single-writer paths.

---

## Architectural Invariants & Reuse Discipline (DRY)

1. **V1 Minimal Scope & Single-Read Content Parsing:**
   - **Data Sources:** Sourced strictly from local `rebalance.db`'s `project_registry` table and the operator's `0. Goals.md` file. Multi-repo `releases.db` querying is explicitly deferred to v2.
   - **Path Resolution:** Reuses existing `resolve_database_path()` from `rebalance.paths` and `get_vault_path() + FOCUS5_GOALS_FILENAME` from `src/rebalance/web.py:1037-1073`.
   - **Missing File Graceful Degradation:** If the DB does not exist, returns HTTP 200 `{ "computed_at": null, "goals_revision": null, "projects": [] }`. If `0. Goals.md` is missing or unreadable, all active projects from `project_registry` still render as bare rows with `tasks: []` (preserving portfolio visibility).
   - **Single-Read In-Memory Parsers:**
     - Introduces `rebalance.ingest.goals_file.parse_goals_content(content: str, limit: int | None = None) -> list[dict]` and `parse_sectioned_goals_content(content: str) -> list[RawSectionGroup]`.
     - `parse_goals(path:)` and `parse_sectioned_goals(path:)` become thin path wrappers reading content once and delegating to the content parsers.
     - **Strict Snapshot Binding:** Both `_focus5_goals_payload()` (`GET /focus-5/goals`) and `GET /portfolio-matrix.json` read `0. Goals.md` **exactly once** per response. That single UTF-8 string is passed to `compute_goals_revision(content)` and the content parser, guaranteeing that every emitted `line_index` and `goals_revision` are mathematically bound to the identical file snapshot with zero time-of-check to time-of-use gap.
2. **Route-Owned Project Matching & Subproject Delimiter:**
   - The route (`src/rebalance/web.py`) owns semantic mapping:
     - **Spaced Slash Delimiter:** Splits `header_raw` on the exact spaced token `" / "` into `(project_token, subproject_token)`. An unspaced slash (e.g. `Binoid/Bloomz`) is treated as part of the project name.
     - **Exact Normalized Equality:** Matches `project_token` against `project_registry.name` using `normalize_match_text()` from `src/rebalance/ingest/project_classifier.py:24-31`.
     - **Collision Safety:** Colliding normalized keys in `project_registry` log a warning and attach zero tasks to prevent misattributing work.
     - **Duplicate Section Coalescing:** If duplicate identical `(project, subproject)` sections appear in the file, their tasks are coalesced in file order before applying the 3-task cap, guaranteeing exactly one row per derived `id`.
     - **Active Project Preservation:** Every active project in `project_registry` without a matching goal section emits one bare row with `subproject=None` and `tasks=[]`.
     - **Multi-Subproject Rows:** If multiple subprojects exist for one project, each emits a row sharing parent metrics, sorted subproject-first (`subproject=None` first, then alphabetically).
     - Stable Swift row identity: `id: "\(name):\(subproject ?? "")"`.
3. **End-to-End Safe Single Writer Path & Consumer Compatibility:**
   - **Wire Contract & Backward Compatibility:**
     - `Focus5GoalCompleteRequest` defines `title: str`, `line_index: int | None = None`, and `goals_revision: str | None = None`.
     - `goals_revision` is an optional field in the request schema to preserve full backward compatibility for legacy external callers.
     - Both `_focus5_goals_payload()` (`GET /focus-5/goals`) and `GET /portfolio-matrix.json` return `goals_revision: str | None` (SHA-256 content hash of `0. Goals.md`).
     - Existing `Focus5GoalsResponse` and `Focus5GoalCompleteResponse` in `Models.swift` are extended with `goals_revision: String?`.
     - `ObsidianRemindersStore.swift` retains and advances `goalsRevision: String?` in **both** `apply(_ response: Focus5GoalsResponse)` and `apply(_ response: Focus5GoalCompleteResponse)`, guaranteeing that sequential reminder completions immediately carry the updated revision without a manual reload.
   - **Process-Local Path Serialization & Single-Owner Revision Check:**
     - A process-local `threading.Lock()` scoped to the target goals file path protects the entire writer critical section inside `complete_goal_in_file()`.
     - While holding the lock, the helper: (1) reads file content once; (2) validates `goals_revision` if supplied; (3) selects the target task; (4) writes to a unique temporary file (`NamedTemporaryFile(dir=path.parent, prefix=".goals_", suffix=".tmp", delete=False)`); and (5) atomically replaces the target path (`os.replace`).
     - **Concurrency Guarantee:** Two concurrent requests carrying the same valid revision serialize behind the lock. Request 1 checks hash V, writes new file with hash V+1, and finishes. Request 2 acquires the lock, reads the new content, sees hash V+1 != V, and raises `StaleRevisionError` -> **HTTP 409 `stale_goal_snapshot`** with zero writes. No lost updates.
   - **Strict Ambiguity Selection Rules:**
     - **With `expected_revision` supplied:** verifies hash equality first. Once verified identical to disk, tests `line_index` first. If line shifted or omitted, collects all open goals matching title: if >1 matches, raises `AmbiguousGoalError` -> **HTTP 409 `ambiguous_goal_title`** (zero writes); if 1 match, mutates; if 0, returns None/404.
     - **With `expected_revision` omitted (legacy compatibility):** **collects all open goals matching `title` FIRST.** If count > 1, strictly raises `AmbiguousGoalError` -> **HTTP 409 `ambiguous_goal_title`** (zero writes), even if `line_index` was provided and points to one of them.
   - **Strict Primary-Server Origin Affinity in Swift Client:**
     - `Focus5Client.swift` enforces strict **primary-only affinity** for all endpoints involved in reading mutable state or mutating goals:
       - `fetchGoals()` is primary-only.
       - `fetchPortfolioMatrix()` is primary-only (both initial fetch and post-mutation refetch).
       - `completeGoal()` is strictly single-dispatch against the primary URL.
       - Ambiguous transport recovery GET is primary-only.
     - Candidate port failover is disabled for these endpoints, guaranteeing that a matrix loaded from port 8787 never sends a revision to port 8767 or refetches state from a diverged origin.
   - **UI-Wide Mutation Lock & Guard-Before-Await:**
     - In `Focus5Model.swift`, `isMutatingTask: Bool` disables **all** matrix task checkboxes while a completion request is in flight, preventing concurrent clicks across different tasks.
     - In `ObsidianRemindersStore.swift`, `completingLineIndexes.insert(lineIndex)` and the interaction lock are set **before** `await client.completeGoal(...)` and cleared in a `defer` block.
     - **Success (HTTP 200):** dispatches primary-only `fetchPortfolioMatrix()` to refresh state in place.
     - **Explicit HTTP Error (409/4xx):** clears in-flight lock, retains the last matrix, and displays a targeted error banner.
     - **Ambiguous Transport Failure:** dispatches primary-only recovery GET (`fetchPortfolioMatrix()`). If successful, updates state to server ground truth; if recovery fails, retains prior matrix and surfaces connection error.
4. **Data Contract (`GET /portfolio-matrix.json`):**
   - Responds at HTTP 200 with snake_case fields:
     ```json
     {
       "computed_at": "2026-09-15T15:30:00Z",
       "goals_revision": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
       "projects": [
         {
           "name": "Binoid/Bloomz",
           "subproject": null,
           "revenue_ranking": 5,
           "revenue_potential": 4,
           "computed_score": 9,
           "tasks": [
             { "title": "PCI compliance", "line_index": 12 },
             { "title": "Weekly Performance Review", "line_index": 15 }
           ]
         }
       ]
     }
     ```
   - **Defensive Metric Coercion (`_safe_int`):**
     - Helper `_safe_int(val, default=0)` handles `None`, string numbers ("4"), floats, and malformed strings ("N/A", lists) without raising 500:
       - `revenue_ranking`: `_safe_int(custom_fields.get("revenue_ranking"), default=_safe_int(priority_tier, 0))`
       - `revenue_potential`: `_safe_int(custom_fields.get("revenue_potential"), default=0)`
       - `computed_score`: `_safe_int(custom_fields.get("computed_score"), default=revenue_ranking + revenue_potential)`
     - Top-level rows sort descending by `computed_score`, then ascending by `name`, then `subproject`.
     - Tasks are capped at the first 3 open items in file order per group.
5. **Frozen-Column UI Ergonomics with Fixed Row Heights:**
   - Implements `PortfolioMatrixView.swift` with a split-scrolling layout:
     - **Shared Row Height:** Every row enforces a fixed height (58pt) on both sides to guarantee row alignment across scrolling boundaries.
     - **Left Column (Frozen):** Fixed 130pt width displaying Project Name (lineLimit 1), optional subproject caption (lineLimit 1), and Computed Score badge. Pinned at x=0; never scrolls away.
     - **Right Scroller:** Horizontal `ScrollView` hosting Task 1, Task 2, Task 3 columns (150pt minimum width each, lineLimit 2 for titles).
     - Verified manually at both 340pt (default) and 420pt panel widths.
   - Comprehensive `ViewMode` integration:
     - Model state: `matrixResponse: PortfolioMatrixResponse?`, `matrixLoadState: LoadState`, `isMatrixOffline: Bool`, `completingTaskKey: String?`.
     - `Focus5Model.init(client: Focus5Client = Focus5Client())` allows client dependency injection.
     - `Focus5Model.refresh()` calls `refreshMatrix()` when `viewMode == .matrix`.
     - `ContentView.swift` updates segmented controls and toolbar status.

---

## Detailed Component Breakdown

### What is Reused / Adapted:
| Component / Subsystem | Location | How it is Reused / Adapted |
|---|---|---|
| `project_registry` | `rebalance.ingest.registry` | Sourced via `get_projects(db, status="active")` with zero schema changes. |
| `project_classifier` | `rebalance.ingest.project_classifier` | `normalize_match_text()` reused for exact project header matching. |
| `goals_file.py` | `rebalance.ingest.goals_file` | Adds in-memory `parse_goals_content()` and `parse_sectioned_goals_content()`; `complete_goal_in_file()` does single file read, checks `goals_revision` when supplied, and collects duplicate titles first when revision omitted. |
| `complete_goal` API | `src/rebalance/web.py` | `POST /api/focus5/goals/complete` accepts optional `goals_revision`; catches `StaleRevisionError` -> 409 and `AmbiguousGoalError` -> 409. `_focus5_goals_payload()` returns `goals_revision` from single file read. |
| `ObsidianRemindersStore` | `Focus5Float/ObsidianRemindersStore.swift` | Advances `goalsRevision` in both `apply(Focus5GoalsResponse)` and `apply(Focus5GoalCompleteResponse)`; sets interaction lock before `await` and clears in `defer`. |
| `Models.swift` | `Focus5Float/Sources/Focus5Float/Models.swift` | Extends `Focus5GoalsResponse` and `Focus5GoalCompleteResponse` with `goals_revision: String?`. |
| `Focus5Model` | `Focus5Float/Focus5Model.swift` | Extended with client injection, `.matrix` mode, `isMutatingTask` global lock, `refreshMatrix()`, and `completeMatrixTask()` with primary-pinned transport recovery GET. |
| `Focus5Client` | `Focus5Float/Focus5Client.swift` | Enforces primary-only affinity for `fetchGoals()`, `fetchPortfolioMatrix()`, `completeGoal()`, and all refetches/recovery. |
| `Theme.swift` | `Focus5Float/Theme.swift` | Reuses existing colors, glass backgrounds, typography, and status dot tokens. |

### What is New (Surgical Footprint):
| New File | Location | Purpose & Line Budget |
|---|---|---|
| `MatrixModels.swift` | `Focus5Float/Sources/Focus5Float/` | Swift `Codable` structs for `PortfolioMatrixResponse`, `MatrixProject`, `MatrixTask` with stable derived `id` (~40 lines). |
| `PortfolioMatrixView.swift` | `Focus5Float/Sources/Focus5Float/` | SwiftUI View with frozen left project column + fixed 58pt row height + in-flight pill disable (~130 lines). |
| Route `GET /portfolio-matrix.json` | `src/rebalance/web.py` | Projection endpoint reading registry & sectioned groups from single file read with `_safe_int` coercion & `goals_revision` hash (~70 lines). |
| `test_portfolio_matrix.py` | `tests/` | Python tests covering missing DB, missing goals, single-read snapshot consistency, malformed metrics, stale revision 409, omitted revision preferred-line duplicate 409, concurrent writer serialization 409, unspaced slashes, and coalesced duplicates (~160 lines). |
| `MatrixTests.swift` | `Focus5Float/Tests/` | Swift tests for JSON decoding, single-attempt POST, primary-pinned recovery GET, sequential reminders revision advancement, and global in-flight lock via `MockURLProtocol` (~120 lines). |

**Total footprint:** ~520 lines. Zero external dependencies.

---

## Verification & Edge Case Matrix

| Edge Case | Expected System Behavior | Verification Test |
|---|---|---|
| **Missing / Unreadable DB** | Route returns HTTP 200 `{ "computed_at": null, "goals_revision": null, "projects": [] }`. Client shows clean empty state. | `test_portfolio_matrix_missing_db()` |
| **Missing / Unreadable `0. Goals.md`** | Projects from `project_registry` render as bare rows with empty `tasks: []`. | `test_portfolio_matrix_missing_goals()` |
| **Single-Read Snapshot Consistency** | Goals file read exactly once per GET; emitted `line_index` and `goals_revision` are guaranteed identical bytes with zero parse/hash race. | `test_single_read_snapshot_consistency()` |
| **Unspaced Slash in Project Name** | `## Binoid/Bloomz` does not split on unspaced slash; matches project `Binoid/Bloomz` with `subproject=None`. | `test_sectioned_goals_unspaced_slash_preserved()` |
| **Duplicate Identical Headings** | Identical `## Project / Subproject` sections coalesce tasks in file order up to 3-task cap, emitting exactly one row. | `test_sectioned_goals_coalesce_duplicate_headings()` |
| **Active Project with No Goals** | Active registry projects absent from `0. Goals.md` emit a row with `subproject=None` and `tasks=[]`. | `test_active_project_without_goals_rendered()` |
| **Malformed Metric Values** | `_safe_int` gracefully handles `"N/A"`, `None`, `"5"`, `[1]`, falling back to 0 or sum without 500 error. | `test_portfolio_matrix_malformed_metrics()` |
| **Stale `goals_revision` on Shifted Line** | If file edited before completion POST, route refuses with HTTP 409 `stale_goal_snapshot` and zero file writes. | `test_complete_goal_stale_revision_409()` |
| **Concurrent Same-Revision POSTs Serialized** | Two concurrent POSTs carrying the same revision serialize behind the path lock; exactly one succeeds, second gets 409 stale snapshot, zero lost writes. | `test_concurrent_same_revision_completions_serialized()` |
| **Omitted Revision with Preferred Line on Duplicate Title** | When revision is omitted and preferred index points to one of duplicate open titles, raises `AmbiguousGoalError` (409) with zero file writes. | `test_complete_goal_omitted_revision_preferred_line_duplicate_409()` |
| **Single-Attempt POST (No Port Failover)** | On 409 or transport error, `Focus5Client.completeGoal` issues exactly 1 POST to primary port; never retries port 8767. | `MatrixTests.testCompleteGoalSingleAttemptNoFailover()` |
| **Primary Server Affinity Across All Mutable State** | `fetchGoals`, `fetchPortfolioMatrix`, `completeGoal`, and post-mutation refetch all target primary base URL, never secondary candidates. | `MatrixTests.testMutableStateQueriesPinnedToPrimaryServer()` |
| **Ambiguous Transport Recovery Pinned to Primary** | On lost response during POST, dispatches recovery GET strictly to primary base URL (never port 8767); updates state on success. | `MatrixTests.testRecoveryGETPinnedToPrimaryServer()` |
| **Recovery GET Failure Handling** | If both POST transport and subsequent recovery GET fail, retains prior in-memory matrix and displays persistent error banner. | `MatrixTests.testRecoveryGETFailureRetainsMatrix()` |
| **Sequential Reminders Advance Revision** | Two sequential reminder completions succeed because completion response advances stored `goalsRevision` without reload. | `MatrixTests.testSequentialRemindersAdvanceRevision()` |
| **Existing Reminders Caller Compatibility** | `ObsidianRemindersStore` refresh populates `goalsRevision` and successfully completes task passing revision to `Focus5Client`. | `test_obsidian_reminders_store_with_revision()` |
| **Global In-Flight Interaction Lock** | All task checkboxes in Matrix view and all reminder completions are disabled while any mutation is in flight. | `MatrixTests.testGlobalInteractionLockDuringMutation()` |
| **Row Alignment & Fixed Height** | Both left and right columns share 58pt row frame; text truncates gracefully without row misalignment at 340pt and 420pt. | Manual layout verification at both panel widths. |

---

## Phases

### Phase 1: Python Data Plane & API Projection
- [ ] Add `RawSectionGroup`, `parse_goals_content()`, and `parse_sectioned_goals_content()` to `src/rebalance/ingest/goals_file.py`, with path wrappers `parse_goals()` and `parse_sectioned_goals()`.
- [ ] Add SHA-256 `compute_goals_revision(content: str)` to `goals_file.py`.
- [ ] Update `complete_goal_in_file()`: add process-local path-scoped `threading.Lock()`, unique temporary file creation, single file read, revision check when supplied, and unconditional title ambiguity check when revision omitted.
- [ ] Extend `_focus5_goals_payload()` in `src/rebalance/web.py` to read file once and return `goals_revision`.
- [ ] Update `focus5_complete_goal()` in `src/rebalance/web.py` to accept optional `goals_revision` in request body, map `StaleRevisionError` -> HTTP 409 `stale_goal_snapshot`, and map `AmbiguousGoalError` -> HTTP 409 `ambiguous_goal_title`.
- [ ] Implement `GET /portfolio-matrix.json` in `src/rebalance/web.py` with single file read, `_safe_int` coercion, spaced slash split, normalized matching, duplicate heading coalescing, and unsectioned project preservation.
- [ ] Add and pass `tests/test_portfolio_matrix.py` (all Python test cases above).

### Phase 2: macOS Swift App (`Focus5Float`)
- [ ] Add `goals_revision: String?` to `Focus5GoalsResponse` and `Focus5GoalCompleteResponse` in `Models.swift`.
- [ ] Update `ObsidianRemindersStore.swift`: advance `goalsRevision` in both `apply` methods, set lock before `await`, and clear in `defer`.
- [ ] Add `MatrixModels.swift` with `Codable` models including `goals_revision` and derived `id: "\(name):\(subproject ?? "")"`.
- [ ] Update `Focus5Client.swift` with primary-only affinity for `fetchGoals()`, `fetchPortfolioMatrix()`, `completeGoal()`, and refetches/recovery.
- [ ] Inject `client: Focus5Client` into `Focus5Model.init()`, add `matrixResponse`, `matrixLoadState`, `isMatrixOffline`, `isMutatingTask`, `refreshMatrix()`, and `completeMatrixTask()`.
- [ ] Implement `PortfolioMatrixView.swift` with frozen 130pt left column, fixed 58pt row height, global in-flight disable, and horizontal task scroller.
- [ ] Connect task checkbox to `Focus5Model.completeMatrixTask()`.
- [ ] Add `Matrix` tab to `ModeSegmentedControl` in `ContentView.swift`.
- [ ] Add `MatrixTests.swift` covering decoding, primary-pinned requests, sequential reminder revision advancement, and global interaction lock.
- [ ] Update `CONTRACT.md`.

### Phase 3: Verification & Test
- [ ] Run Python test suite (`pytest tests/test_portfolio_matrix.py`).
- [ ] Run Swift test suite (`swift test --package-path macOS/Apps/Focus5Float`).
- [ ] Verify manual layout and row alignment at 340pt and 420pt window sizes.

## Lessons Learned (For Future Agents)

- **The plan's Phase 2 checklist predates the decoupling decision.** It names `Focus5Float`
  files, but the shipped implementation is the standalone `macOS/Apps/PortfolioMatrix` package
  (frontmatter goal and non-goals are the authoritative statement). When a plan pivots
  mid-flight, rewrite the phase checklist in the same commit — a stale checklist reads as
  "139 open tasks" to `merge-cleanup` and to any agent triaging the doc later.
- **A read-only projection needs a home on the server that is actually running.** The first
  cut put `GET /portfolio-matrix.json` only in `rebalance serve` (port 8787), which is not
  always up. The fix (620f42d) mirrors the route on the always-running pulse server
  (`scripts/pulse_server.py`, port 8767) and gives `PortfolioClient` an ordered candidate list
  (`pulseServerBaseURL`, `devServerBaseURL`) with an `allCandidatesFailed` error, so the HUD
  shows live data without asking the operator to start a second server.
- **Single-writer hardening was the right place to spend effort.** `goals_revision`
  (SHA-256 of the goals file) plus a process-local path lock in `complete_goal_in_file()`
  turned a silent last-write-wins into an explicit `StaleRevisionError` → HTTP 409; the matrix
  app refetches on 409 instead of retrying blind.
- **Operator-facing server output is part of the contract.** `serve` now prints the matrix URL
  and an explicit "Server running" line (e163047); the earlier output made a healthy server look
  stalled during the first manual test.
- **Landing friction was all housekeeping, not code.** `ROADMAP.md` conflicted with
  `development` only because both sides appended a bullet at the same spot (resolved by keeping
  both); `ruff` failed on two unused test imports and formatting in three files. Run
  `ruff check . && ruff format --check .` before opening the PR. The remaining red `lint` and
  `root-noembed` checks on the PR were pre-existing on `development` (since 2026-09-13) and are
  not from this change.
