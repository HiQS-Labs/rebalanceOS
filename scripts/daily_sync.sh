#!/bin/bash
# rebalance OS — daily data sync
# Runs on boot and daily via launchd. Calls refresh_index() (default recipe:
# all raw sources + code/semantic/sync) so the MCP server always has fresh context.
#
# Single source of truth: this is the same orchestration the MCP
# refresh_index tool exposes to interactive agents.
#
# Policy: SCHEDULER.md (job com.rebalance-os.daily-sync).
# Install: bash scripts/stack.sh install daily-sync

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/scheduler_common.sh"
rb_job_init "daily-sync" 30

log "=== rebalance daily sync starting ==="

# refresh_index orchestrates: vault ingest+embed -> github scan+sync+embed ->
# calendar -> sleuth -> unified semantic backfill+embed. Per-scope failures
# are captured in the result.errors list rather than aborting the run.
if rb_refresh; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

rb_log_sync_outcome "rebalance daily sync" "$EXIT_CODE"

rb_trim_logs

exit $EXIT_CODE
