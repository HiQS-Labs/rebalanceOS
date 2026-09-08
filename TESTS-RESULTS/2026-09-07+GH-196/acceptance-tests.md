# Acceptance Test Results: GH-196 Shutdown MVP

- **Date:** 2026-09-07
- **Issue:** https://github.com/HiQS-Labs/rebalanceOS/issues/196
- **Pull Request:** https://github.com/HiQS-Labs/rebalanceOS/pull/197
- **Base SHA:** `ed320289f78abe2e5f0228457a95b07a614c2d00`
- **Candidate Branch:** `feat/shutdown-plan`
- **Environment:** macOS Python 3.14.7, pytest 9.1.1, hypothesis 6.167.1

## Test Execution

Command:
```bash
.venv/bin/pytest tests/test_shutdown_scanner.py tests/test_shutdown_handoff.py -v
```

Exit code: `0`

Output:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/noelsaw/Documents/GH Repos/gh196-shutdown/.venv/bin/python3
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: /Users/noelsaw/Documents/GH Repos/gh196-shutdown
configfile: pyproject.toml
plugins: hypothesis-6.167.1, anyio-4.15.1
collecting ... collected 19 items

tests/test_shutdown_scanner.py::test_a1_discovery_nested_edit_and_gitfiles PASSED [  5%]
tests/test_shutdown_scanner.py::test_a2_calendar_day_window PASSED       [ 10%]
tests/test_shutdown_scanner.py::test_a3_honest_git_state PASSED          [ 15%]
tests/test_shutdown_scanner.py::test_a4_two_pass_activity_exclusion PASSED [ 21%]
tests/test_shutdown_scanner.py::test_a5_execution_bounds PASSED          [ 26%]
tests/test_shutdown_scanner.py::test_a6_no_scan_mutations PASSED         [ 31%]
tests/test_shutdown_scanner.py::test_repro_tracked_dirty_edit PASSED     [ 36%]
tests/test_shutdown_scanner.py::test_repro_same_metadata_content_edit PASSED [ 42%]
tests/test_shutdown_scanner.py::test_repro_failed_git_reads PASSED       [ 47%]
tests/test_shutdown_scanner.py::test_repro_failed_pr_lookup PASSED       [ 52%]
tests/test_shutdown_scanner.py::test_repro_single_checkout_daily PASSED  [ 57%]
tests/test_shutdown_handoff.py::test_a7_continuity_brief_formatting PASSED [ 63%]
tests/test_shutdown_handoff.py::test_a8_standalone_and_db_enrichment PASSED [ 68%]
tests/test_shutdown_handoff.py::test_a9_durable_atomic_handoff PASSED    [ 73%]
tests/test_shutdown_handoff.py::test_a10_exclusion_boundary PASSED       [ 78%]
tests/test_shutdown_handoff.py::test_a11_claude_forwarding_compatibility PASSED [ 84%]
tests/test_shutdown_handoff.py::test_a12_useful_restart PASSED           [ 89%]
tests/test_shutdown_handoff.py::test_repro_active_repo_nudges PASSED     [ 94%]
tests/test_shutdown_handoff.py::test_repro_same_run_id_interrupted_write PASSED [100%]

============================== 19 passed in 4.67s ==============================
```

## Review Reproduction Receipts

Executed isolated test harness reproducing Astra's review cases against current branch:

```json
{"case": "tracked_dirty_edit", "raw_status": " M README.md\n", "parsed": ["README.md"], "meta_before": [["README.md", 12, 1788838592, "61e970aa16b75d4963758a7c369331b281cb25da4736e0336df0cf44efdf25aa"]], "meta_after": [["README.md", 40, 1788838592, "93dea2c37a7595b88bc30b59476212def67013c4bc60a97e96d2e42e180d59dc"]], "same_fingerprint": false}
{"case": "same_metadata_content_edit", "same_fingerprint": false, "metadata": [["README.md", 40, 1788838592, "93dea2c37a7595b88bc30b59476212def67013c4bc60a97e96d2e42e180d59dc"], ["new.txt", 4, 1700000000, "81cc5b17018674b401b42f35ba07bb79e211239c23bffe658da1577e3e646877"]]}
{"case": "failed_git_reads", "stable": 0, "excluded": 1}
{"case": "failed_pr_lookup", "branch_status": "unknown", "claims_no_prs": false, "suggests_cut_pr": false}
{"case": "active_repo_nudges", "suggests_cut_or_merge": false, "suggests_top_pr": false}
{"case": "same_run_id_interrupted_write", "latest_markdown": "first brief", "sidecar": {"run": 1}}
{"case": "single_checkout_daily", "registered_worktrees": 1, "active_worktrees": 0, "unpred": 0}
```

Receipt verification:
1. `tracked_dirty_edit`: Preserves leading whitespace from porcelain status; `filepath` parses as `README.md` (unstaged); hashes diverge (`same_fingerprint: false`).
2. `same_metadata_content_edit`: Content hashing detects edits with identical file size and mtime (`same_fingerprint: false`).
3. `failed_git_reads`: Git command read failures are flagged and excluded from stable repos (`stable: 0, excluded: 1`).
4. `failed_pr_lookup`: Network / auth failure on PR query marks branch as `unknown`, avoids claiming no PRs, and suppresses spurious "cut PR" nudges.
5. `active_repo_nudges`: Ongoing activity exclusions suppress active repos from action recommendations (`suggests_cut_or_merge: false, suggests_top_pr: false`).
6. `same_run_id_interrupted_write`: Atomic serialization verifies sidecar data before file modification, preventing mismatched/corrupted handoffs.
7. `single_checkout_daily`: Primary checkout excluded from linked worktrees (`active_worktrees: 0, unpred: 0`).

## Acceptance Matrix Evidence

| ID | Name | Pass Evidence | Red Control Verified |
|---|---|---|---|
| **A1** | Discovery & Worktrees | `test_a1_discovery_nested_edit_and_gitfiles`: Confirms root mtime is not gated; discovers nested edits in old root; distinguishes gitfile worktree and two distinct clones. | Failing case if root mtime gated: nested edits omitted. |
| **A2** | Local Days | `test_a2_calendar_day_window`: Confirms 3-calendar-day window (today + 2 previous local days) from local midnight to current scan instant, properly converting boundaries to UTC across evening rollover and DST shifts. | Failing case if UTC date prefix/72h: evening events misplaced across day boundary. |
| **A3** | Honest Git/PR State | `test_a3_honest_git_state`: Accurately handles detached HEAD, missing upstream, unborn branch without crashing. | Failing case if missing upstream crashes inspection. |
| **A4** | Two-pass Exclusion | `test_a4_two_pass_activity_exclusion`: Verifies same-status content edits (same file size/status, modified hash), ref changes, and active locks (`releases-app.lock`) flag ongoing activity and exclude the repo. | Failing case if comparing only status strings: same-status edit treated as stable. |
| **A5** | Bounds & Uncertainty | `test_a5_execution_bounds`: Verifies subprocess timeout handling and command bounds return error safely. | Failing case if subprocess hangs indefinitely. |
| **A6** | No Scan Mutations | `test_a6_no_scan_mutations`: Asserts working tree refs, index, and untracked files are strictly unmodified by scan; verifies `--no-ledger-write` / `--mode shutdown` leaves `close-the-loop.md` untouched. | Failing case if legacy ledger written: file modification detected. |
| **A7** | Continuity Brief | `test_a7_continuity_brief_formatting`: Formats first screen with what advanced, open arcs/phases, explicit PR review status, proposed merge order, and nudges. | Failing case if missing headings or fields in formatted output. |
| **A8** | Standalone & Enrichment | `test_a8_standalone_and_db_enrichment`: Standalone works cleanly with zero database/runtime dependencies; read-only DB connection enriches commits/items without schema mutation. Missing or stale DB degrades gracefully. | Failing case if missing DB crashes execution. |
| **A9** | Durable Handoff Persistence | `test_a9_durable_atomic_handoff`: Verifies atomic write of `.md` narrative and `.json` evidence under `<output_home>/YYYY-MM-DD/<run_id>`, with `latest.md` symlink updated atomically only after successful write. Prior runs preserved. | Failing case if symlink updated early: points to missing or truncated file. |
| **A10** | Exclusion Boundary | `test_a10_exclusion_boundary`: Verifies ongoing activity exclusions are reported and active repos excluded from action candidates. | Failing case if active repos included in merge actions. |
| **A11** | Compatibility & Forwarding | `test_a11_claude_forwarding_compatibility`: Confirms daily scan entry points across canonical and `.claude` forwarding shims execute without error. | Failing case if shim missing or syntax error. |
| **A12** | Useful Restart | `test_a12_useful_restart`: Verifies cold agent can resume work directly from `latest.md` handoff without conversational chat history. | Failing case if missing handoff leaves agent with no starting context. |

## Static Code Governance Checks

Command:
```bash
.venv/bin/python utils/pdda/check_banned_imports.py --check
```

Output:
```
sqlite gateway ratchet: clean (0 baseline file(s) matched exactly)
banned-import ratchet: clean (29 baseline file(s) matched exactly)
```
Exit code: `0`

Linter:
```bash
.venv/bin/ruff check src/rebalance/ingest/ .agents/skills/ tests/
```
Output:
```
All checks passed!
```
Exit code: `0`
