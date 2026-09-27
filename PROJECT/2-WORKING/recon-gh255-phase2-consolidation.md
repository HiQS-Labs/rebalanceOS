# Recon Map — GH-255 Phase 2 Script Consolidation
Commit: `17e08c1` · Mode: `grep+read` · Lanes: A (Entry & Call Paths), B (State & Data), C (Contracts), D (Build & Failure)

## Subject and change class
- **Subject:** Scheduled job runtime wrappers (`scripts/daily_sync.sh`, `scripts/github_sync.sh`, `scripts/obsidian_vault_embeddings.sh`, `utils/obsidian_rollover.sh`, `utils/daily_synthesis.sh`), shared runtime helper `scripts/lib/scheduler_common.sh`, and obsolete spike script pruning.
- **Change class:** Cross-module refactor & code consolidation (DRY / inventory ratchet).

## The seams — where a change here escapes this file
| Seam | Location | Crosses | Breaks if |
|---|---|---|---|
| LaunchAgent plists | `scripts/com.rebalance-os.*.plist.template` | launchd execution of wrapper scripts | Wrapper arguments, paths, or execution environments diverge from template assumptions |
| Job guard wrapper | `utils/job_guard.py` | Lifecycle event logging and timeout supervision | Return codes or child process invocation fails |
| Test suite policy | `tests/test_scheduler_policy.py` | Exact token assertions on wrapper script text (`wrapper_must_contain`) | Required tokens are removed without updating `POLICY` table in test |
| Exit semantics test | `tests/test_daily_sync_exit.py` | Parses `scripts/daily_sync.sh` text for embedded Python heredoc | Heredoc is replaced without updating the test harness |
| Script inventory gate | `utils/pdda/check_script_inventory.py` | CI mechanical ratchet against loose scripts and unapproved deletions | File is deleted or added without updating `script_inventory_baseline.json` |

## Call paths in
- `launchd` -> `job_guard.py` -> `scripts/daily_sync.sh` -> `rb_refresh` -> `rebalance.ingest.index_ops.refresh_index`
- `launchd` -> `job_guard.py` -> `scripts/github_sync.sh` -> `rb_refresh` -> `rebalance.ingest.index_ops.refresh_index`
- `launchd` -> `job_guard.py` -> `scripts/obsidian_vault_embeddings.sh` -> `rb_refresh` -> `rebalance.ingest.index_ops.refresh_index`
- `launchd` -> `job_guard.py` -> `utils/obsidian_rollover.sh` -> `scheduler_common.sh` -> `$PYTHON utils/obsidian_daily_rollover.py`
- `launchd` -> `job_guard.py` -> `utils/daily_synthesis.sh` -> `scheduler_common.sh` -> `$PYTHON utils/daily_synthesis.py`

## State
- **Log destinations:** `temp/logs/<job_prefix>_YYYY-MM-DD.log` (managed by `rb_job_init` in `scheduler_common.sh`).
- **Telemetry stream:** `temp/logs/auth_activity.jsonl` (via `rebalance.ingest.auth_log`).
- **Single write path:** All database mutations route strictly through `index_ops.refresh_index` to `REBALANCE_DB`.

## Contracts
- `classify_sync_outcome`: Accepts `refresh_index` output dict. Returns `("complete", 0)` on no errors; `("degraded", 0)` if partial errors occurred but useful work succeeded; `("fatal", 1)` if migrations failed or all attempted stages failed/skipped.
- `rb_refresh [scopes] [artifact_sync_days]`: Shell helper in `scheduler_common.sh` executing Python via `rb_run_python_stdin`, outputting JSON to `$LOG_FILE`, and returning the classified exit code.
- `scheduler_common.sh`: Single source of truth for `PYTHON` (`.venv/bin/python`), `PYTHONPATH`, and `REBALANCE_DIR`.

## Build, failure and rollback today
- Covered by `tests/test_scheduler_policy.py`, `tests/test_daily_sync_exit.py`, and `tests/test_script_inventory_ratchet.py`.
- Rollback: Revert task commit on `feat/gh255-phase2-consolidation`.

## Unknowns
| Unknown | Why it matters | What would settle it |
|---|---|---|
| CommandCode binary / Node version | Node 18 lacks RegExp `/v` flag causing syntax error on startup | Resolved: Node 26 is installed in `/opt/homebrew/Cellar/node/26.0.0/bin`; verified `cmd --version` prints 0.52.5 when prepended to PATH. |
| Model availability | Ensuring `xiaomi/mimo-v2.5-pro` is reachable in `cmd` | Resolved: Verified via `cmd --list-models`. |

## Current-state radius, one line
Scheduled launchd execution of daily and hourly data refreshes, obsidian notes rollover, and daily synthesis.
