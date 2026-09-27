#!/bin/bash
# rebalance OS — hourly obsidian vault embeddings refresh
# Runs hourly via launchd (com.rebalance-os.obsidian-vault-embeddings) between 6 AM and 11 PM.
# Calls refresh_index(scope=["vault", "semantic"]) so notes edited during the
# day surface in the dashboard / pulse / semantic search without waiting for
# the daily 06:30 sync.
#
# Policy: SCHEDULER.md (job com.rebalance-os.obsidian-vault-embeddings).

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/scheduler_common.sh"
rb_job_init "obsidian-vault-embeddings" 14

log "=== rebalance obsidian vault embeddings starting ==="

# Freshness policy: "semantic" is included INTENTIONALLY as the follow-on
# stage — vault ingest alone updates raw tables only; the semantic backfill+
# embed is what makes edited notes searchable within the hour.
if rb_refresh "vault,semantic" "" 1; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

rb_log_sync_outcome "rebalance obsidian vault embeddings" "$EXIT_CODE"

rb_trim_logs

exit $EXIT_CODE
