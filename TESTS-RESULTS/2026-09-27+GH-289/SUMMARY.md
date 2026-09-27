# GH-289 Scheduler Python Interpreter Seam Test Campaign

Date: 2026-09-27. Tracking: #289. Protocol: `PROJECT/3-COMPLETED/GH-289-CI-PYTHON-SEAM.md`, reviewed and approved by Codex Plan QA Relay (retained in `qa/gh289-plan-qa.md`, VERDICT: PASS) and Implementation QA Relay (retained in `qa/gh289-impl-qa.md`, VERDICT: PASS).

## Diagnosis & Ground-Truth Reproduction

Following PR #280 landing on `development`, GitHub Actions CI failed on `root-noembed (3.12)` due to `tests/test_daily_sync_exit.py::ShellExecutionTests` exiting with code 127:
- Root cause: `scripts/lib/scheduler_common.sh:28` hardcoded `PYTHON="$REBALANCE_DIR/.venv/bin/python"`.
- In GitHub Actions CI (and fresh checkouts without a repository `.venv`), Python dependencies reside in the runner's Python environment rather than a repository `.venv`.
- Ground truth reproduction: In a fresh full clone (`rebalanceOS-gh289-ci-python-seam`) lacking `.venv`, all 5 `ShellExecutionTests` failed with `AssertionError: 127 != 1` / `AssertionError: 127 != 0`.

## Implementation & Architecture

1. **Interpreter Seam (`scripts/lib/scheduler_common.sh`)**:
   - `PYTHON="${RB_PYTHON:-$REBALANCE_DIR/.venv/bin/python}"`
   - Preserves default `.venv` resolution when `RB_PYTHON` is unset or empty (`:-` bash expansion).
2. **Invocation Guard (`rb_run_python_stdin`)**:
   - Added guard at entry of `rb_run_python_stdin` prior to temporary file allocation:
     ```bash
     if ! command -v "$PYTHON" >/dev/null 2>&1; then
         echo "[$(date '+%Y-%m-%d %H:%M:%S')] interpreter unavailable or not executable: $PYTHON" >&2
         return 127
     fi
     ```
   - Uses `command -v` to support both full paths (missing, non-executable, executable) and bare commands (`python3`).
   - Scoped strictly to `rb_run_python_stdin`. Lifecycle telemetry hooks (`rb_job_mark_started`, `_rb_job_exit`) remain untouched with `|| true` so telemetry never aborts jobs or violates no-venv policy tests.
3. **Test Harness (`tests/test_daily_sync_exit.py`)**:
   - `_run_shell_refresh` exports `RB_PYTHON="{sys.executable}"` before sourcing `scheduler_common.sh`.
4. **Durable Coverage (`SchedulerInterpreterSeamTests`)**:
   - `test_default_resolution_unset`: `env -u RB_PYTHON` resolves to `$REBALANCE_DIR/.venv/bin/python`.
   - `test_default_resolution_empty`: `RB_PYTHON=""` resolves to `$REBALANCE_DIR/.venv/bin/python`.
   - `test_custom_override_resolution`: `RB_PYTHON="/custom/test/python"` resolves to `/custom/test/python`.
   - `test_rb_run_python_stdin_missing_guard`: Non-existent interpreter returns 127 and emits stderr diagnostic.
   - `test_rb_run_python_stdin_non_executable_guard`: Non-executable interpreter (`chmod 0o644`) returns 127 and emits stderr diagnostic.
   - `test_rb_run_python_stdin_bare_command_name`: Bare command name (`python3`) successfully executes.
   - `test_rb_refresh_missing_interpreter_logs_diagnostic`: Missing interpreter path inside `rb_refresh` returns 127 and logs diagnostic into `LOG_FILE`.
   - `test_rb_refresh_non_executable_logs_diagnostic`: Present but non-executable interpreter (`chmod 0o644`) inside `rb_refresh` returns 127 and logs diagnostic into `LOG_FILE`.

## Results

- `pytest tests/test_daily_sync_exit.py`: 25 passed in 0.84s.
- `pytest tests/test_scheduler_policy.py`: 34 passed in 0.82s.
- `pytest tests/test_script_inventory_ratchet.py`: 9 passed in 0.05s.
- `pytest tests/test_stack_script.py`: 30 passed in 22.30s.
- Total test suite: 98 passed (100% green).
- Ratchet check (`utils/pdda/check_script_inventory.py --check`): clean (matches baseline).
- Linter & Formatter (`ruff check`, `ruff format --check`): clean across all touched files.
- Shell syntax (`bash -n scripts/lib/scheduler_common.sh`): valid.

## Threats to Validity

Local macOS testing was conducted in a fresh full clone lacking `.venv` to mirror the runner condition. Full GitHub Actions runner verification across Python 3.12 and 3.13 matrix is attested on PR #295 (run 36339765108, all 11 checks green).

