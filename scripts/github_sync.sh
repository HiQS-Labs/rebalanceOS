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
if rb_refresh "github,focus5" 7 1; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

rb_log_sync_outcome "rebalance hourly github sync" "$EXIT_CODE"

rb_trim_logs

exit $EXIT_CODE
