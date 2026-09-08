# Acceptance Test Results: GH-196 Shutdown MVP

- **Date:** 2026-09-07
- **Issue:** https://github.com/HiQS-Labs/rebalanceOS/issues/196
- **Base SHA:** `ed320289f78abe2e5f0228457a95b07a614c2d00`
- **Candidate Commit:** `feat/shutdown-plan` (working tree atop `b3d776e`)
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
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/noelsaw/Documents/GH Repos/gh196-shutdown/.venv/bin/python
rootdir: /Users/noelsaw/Documents/GH Repos/gh196-shutdown
configfile: pyproject.toml
plugins: hypothesis-6.167.1, anyio-4.15.1
collected 12 items

tests/test_shutdown_scanner.py::test_a1_discovery_and_worktrees PASSED   [  8%]
tests/test_shutdown_scanner.py::test_a2_calendar_window_utc PASSED      [ 16%]
tests/test_shutdown_scanner.py::test_a3_branch_pr_matching PASSED       [ 25%]
tests/test_shutdown_scanner.py::test_a4_two_pass_exclusion PASSED       [ 33%]
tests/test_shutdown_scanner.py::test_a5_bounds_and_uncertainty PASSED   [ 41%]
tests/test_shutdown_scanner.py::test_a6_no_scan_mutations PASSED        [ 50%]
tests/test_shutdown_handoff.py::test_a7_continuity_brief PASSED         [ 58%]
tests/test_shutdown_handoff.py::test_a8_standalone_and_enrichment PASSED [ 66%]
tests/test_shutdown_handoff.py::test_a9_durable_handoff_persistence PASSED [ 75%]
tests/test_shutdown_handoff.py::test_a10_approval_and_delegation PASSED [ 83%]
tests/test_shutdown_handoff.py::test_a11_compatibility_and_privacy PASSED [ 91%]
tests/test_shutdown_handoff.py::test_a12_useful_restart PASSED          [100%]

============================== 12 passed in 2.82s ==============================
```

## Acceptance Matrix Evidence

| ID | Name | Pass Evidence | Red Control Verified |
|---|---|---|---|
| **A1** | Discovery & Worktrees | `test_a1_discovery_and_worktrees`: Confirms root mtime is not gated; discovers nested edits in old root; distinguishes gitfile worktree and two distinct clones; classifies dirty untracked files of unknown age under older/unresolved work. | Failing case if root mtime gated: nested edits omitted. |
| **A2** | Local Days | `test_a2_calendar_window_utc`: Confirms 3-calendar-day window (today + 2 previous local days) from local midnight to current scan instant, properly converting boundaries to UTC across evening rollover and DST shifts. | Failing case if UTC date prefix/72h: evening events misplaced across day boundary. |
| **A3** | Honest Git/PR State | `test_a3_branch_pr_matching`: Accurately correlates local branch tips with PR numbers/statuses (open, merged, none, unknown). Handles detached HEAD, missing upstream, and simulated gh failure reporting explicit unknown. | Failing case if gh errors suppressed to empty success: unknown reported as zero work. |
| **A4** | Two-pass Exclusion | `test_a4_two_pass_exclusion`: Verifies same-status content edits (same file size/status, modified hash), ref changes, and active locks (`releases-app.lock`) flag ongoing activity and exclude the entire logical repo group. | Failing case if comparing only status strings: same-status edit treated as stable. |
| **A5** | Bounds & Uncertainty | `test_a5_bounds_and_uncertainty`: Verifies per-file (10 MiB) and per-repo (100 MiB) fingerprint caps; enforces that capped/inaccessible files cause liveness to be marked uncertain/active, preventing unsafe cleanup. | Failing case if capped repo treated as safe/stable: exclusion dropped. |
| **A6** | No Scan Mutations | `test_a6_no_scan_mutations`: Asserts working tree refs, index, and untracked files are strictly unmodified by scan; verifies `--no-ledger-write` / `--mode shutdown` leaves `close-the-loop.md` untouched. | Failing case if legacy ledger written: file modification detected. |
| **A7** | Continuity Brief | `test_a7_continuity_brief`: Formats first screen with what advanced, open arcs/phases, explicit PR review status, proposed merge order, and exactly one next-session prompt/nudge per project. Distinguishes merged phase PR from incomplete project arc. | Failing case if merged PR implies project complete: arc marked done prematurely. |
| **A8** | Standalone & Enrichment | `test_a8_standalone_and_enrichment`: Standalone works cleanly with zero database/runtime dependencies; read-only DB connection enriches commits/items without invoking `ensure_project_schema` or creating schema tables. Missing or stale DB degrades gracefully. | Failing case if writable connection opens DB: schema tables auto-created in empty file. |
| **A9** | Durable Handoff Persistence | `test_a9_durable_handoff_persistence`: Verifies atomic write of `.md` narrative and `.json` evidence under `<output_home>/YYYY-MM-DD/<run_id>`, with `latest.md` symlink updated atomically only after successful write. Interrupted writes or reruns never corrupt prior handoffs. | Failing case if symlink updated early: points to missing or truncated file. |
| **A10** | Approval & Delegation | `test_a10_approval_and_delegation`: Verifies report-only default; requires explicit approved targets; rejects unapproved/active targets; validates that merge-cleanup revalidates live state before execution. | Failing case if unapproved target executed: mock cleanup called. |
| **A11** | Compatibility & Privacy | `test_a11_compatibility_and_privacy`: Confirms daily scan JSON schema compatibility across canonical and forwarding paths; confirms no absolute machine paths or secrets in output. | Failing case if divergence between daily and shutdown scanner output: schema validation error. |
| **A12** | Useful Restart | `test_a12_useful_restart`: Verifies cold agent can resume work directly from `latest.md` handoff without conversational chat history. | Failing case if missing daily history produces empty brief: agent has no next action. |

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
