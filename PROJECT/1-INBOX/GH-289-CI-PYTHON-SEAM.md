---
gh_issue: 289
source: https://github.com/HiQS-Labs/rebalanceOS/issues/289
title: "ci: development red since #280 — ShellExecutionTests exit 127 because scheduler_common.sh pins PYTHON to the repo .venv"
status: "Approved via Codex Plan QA Relay (2026-09-27). Proceeding to implementation."
created: 2026-09-27
updated: 2026-09-27
owner: noel
doc_type: architecture
goal: >
  Make the scheduler Python interpreter an explicit, overridable seam (PYTHON="${RB_PYTHON:-$REBALANCE_DIR/.venv/bin/python}")
  so test suites running in CI environments without a local repository .venv (such as GitHub Actions runner environments)
  can execute ShellExecutionTests reliably, while preserving default .venv resolution for launchd fleet jobs.
effort: 85
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-289 — Fix CI development red failure: Python interpreter seam for scheduler tests

## Status

| What was just completed | What's next |
|---|---|
| Fresh full clone created (`rebalanceOS-gh289-ci-python-seam`), reproduction confirmed (5/5 ShellExecutionTests failing in fresh clone without `.venv`). Plan QA Relay approved by Codex (VERDICT: PASS). | Implement scheduler seam, update test harness, run comprehensive verification, record campaign evidence in `TESTS-RESULTS/`, and open PR. |

## Why

Since PR #280 landed on `development`, GitHub Actions CI has been red (`root-noembed (3.12)` failed, `root-noembed (3.13)` cancelled). `scripts/lib/scheduler_common.sh` hardcodes `PYTHON="$REBALANCE_DIR/.venv/bin/python"`. In CI, dependencies are installed into the runner's Python environment rather than a repository `.venv`, causing `rb_refresh` in `ShellExecutionTests` to fail because the interpreter binary is missing.

## Ratings, with reasons

| Field | Value | Why |
|---|---|---|
| `pri` | 90 | Urgent: `development` is currently red; every downstream PR inherits the red CI status. |
| `sev` | 85 | Blocks automated CI validation and causes matrix cancellation across Python versions. |
| `appeal` | 50 | Neutral (standard developer hygiene and CI repair). |
| `effort` | 85 | High cheapness: surgical environment override (`RB_PYTHON`) + `sys.executable` export in tests. |

## Implementation Plan

### 1. Scheduler Seam & Guard Placement
In `scripts/lib/scheduler_common.sh`:
- Seam definition at line 28:
  ```bash
  PYTHON="${RB_PYTHON:-$REBALANCE_DIR/.venv/bin/python}"
  ```
  This cleanly handles unset and empty `RB_PYTHON` via bash `:-` expansion, preserving default `.venv/bin/python` resolution.
- Guard placement (Invocation-Time, Scoped Solely to `rb_run_python_stdin`):
  Do NOT add an executable check at top-level source time (which would break existing scheduler tests in `tests/test_scheduler_policy.py` that source the runtime without a `.venv`).
  Do NOT alter `rb_job_mark_started` or `_rb_job_exit`; their lifecycle logging is explicitly best-effort (`|| true`) per lines 21, 44, and 51–55, so telemetry must never abort jobs under `set -e`.
  Place the guard solely at the entry of `rb_run_python_stdin` before any temporary file allocation:
  ```bash
  rb_run_python_stdin() {
      if [ ! -x "$PYTHON" ]; then
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] interpreter unavailable or not executable: $PYTHON" >&2
          return 127
      fi
      local script capture attempt=0 code
  ...
  ```
  This requires no cleanup variables and avoids leaving orphaned temporary files on early return.

### 2. Test Harness Update
In `tests/test_daily_sync_exit.py`:
- In `ShellExecutionTests._run_shell_refresh`, set `export RB_PYTHON="{sys.executable}"` **before** `source "{COMMON}"`:
  ```bash
  set -eu
  export RB_PYTHON="{sys.executable}"
  source "{COMMON}"
  ```
- This ensures line 28 of `scheduler_common.sh` evaluates the current test suite Python interpreter at source time.

### 3. Verification & Acceptance Tests
Durable test cases added to `tests/test_daily_sync_exit.py`:
1. **CI Environment Simulation (`ShellExecutionTests`)**:
   - `pytest tests/test_daily_sync_exit.py -k ShellExecution` passes in a clean environment lacking a `.venv` (GitHub Actions runner condition).
2. **Default Interpreter Resolution**:
   - Explicitly clear any inherited `RB_PYTHON` (`env -u RB_PYTHON` / `RB_PYTHON=""`).
   - Sourcing `scheduler_common.sh` resolves `$PYTHON` to `$REBALANCE_DIR/.venv/bin/python`.
3. **Red Control & Direct Invalidation on `rb_run_python_stdin`**:
   - Set `RB_PYTHON` to a non-existent path or a non-executable file (`chmod -x`).
   - Invoking `rb_run_python_stdin` returns exit code 127 and emits `"interpreter unavailable or not executable: ..."` directly on standard stderr.
4. **Red Control & Diagnostic Capture on `rb_refresh`**:
   - Sourcing `scheduler_common.sh` with a temporary `LOG_FILE` and an invalid `RB_PYTHON`.
   - Invoking `rb_refresh` returns non-zero / 127, and the diagnostic message is captured inside `LOG_FILE` (matching `rb_refresh`'s logging redirection contract `>> "${LOG_FILE:-/dev/null}" 2>&1`).
5. **No Regression on Existing Policy Tests**:
   - `pytest tests/test_scheduler_policy.py` passes 100% with no disruption to no-venv sourcing tests.
