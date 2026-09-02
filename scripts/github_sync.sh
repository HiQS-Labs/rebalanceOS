#!/bin/bash
# rebalance OS — hourly github sync (+ Focus 5 roster refresh)
# Runs hourly via launchd to keep github context fresh and, piggybacked on the
# same cadence, recompute the device-local Focus 5 roster so it never freezes
# until someone clicks ↻ Refresh.
#
# Policy: SCHEDULER.md (job com.rebalance-os.github-sync).

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/scheduler_common.sh"
rb_job_init "github-sync" 14

log "=== rebalance hourly github sync starting ==="

# Freshness policy: intentionally NO "semantic" follow-on here. GitHub rows
# land in the raw tables hourly; the github -> semantic backfill+embed runs
# in the 06:30 daily sync. The gap is observable as the
# github_documents_missing_from_semantic drift metric (index_status).
#
# Focus 5 piggybacks on this cadence ("focus5" scope): a device-local git scan
# (~30s, no network) that recomputes focus5_roster so the dashboard stays fresh
# unattended. It does NOT need the GitHub token — a github error won't skip it
# (refresh_index runs each scope independently), and the non-blocking page from
# PR #72 is untouched (this is the background writer the page reads from).
if rb_run_python_stdin <<'PY' >> "$LOG_FILE" 2>&1
import json
import sys
from rebalance.ingest.index_ops import refresh_index
from rebalance.paths import resolve_database_path

db_path = resolve_database_path()
print(f"database={db_path}")
# GH-148: the hourly run narrows ONLY the per-item artifact sync window (the
# issues/PRs/comments/check-runs fan-out measured at 5-7k API calls/run over the
# 30-day default). Watched-set resolution, the events scan and the watched-repo
# rollups keep the wide window; the 06:30 daily-sync still does the full 30-day
# sweep, so nothing loses coverage — the hourly job just stops re-reading
# month-old PRs every hour.
result = refresh_index(db_path, scope=["github", "focus5"], artifact_sync_days=7)
print(json.dumps(result, indent=2, default=str))
sys.exit(1 if result.get("errors") else 0)
PY
then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

if [ $EXIT_CODE -eq 0 ]; then
    log "=== rebalance hourly github sync complete ==="
else
    log "=== rebalance hourly github sync finished with errors ==="
fi

rb_trim_logs

exit $EXIT_CODE
