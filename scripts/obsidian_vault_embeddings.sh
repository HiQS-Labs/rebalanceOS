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
if "$PYTHON" - <<'PY' >> "$LOG_FILE" 2>&1
import json
import sys
from rebalance.ingest.index_ops import refresh_index
from rebalance.paths import resolve_database_path

db_path = resolve_database_path()
print(f"database={db_path}")
result = refresh_index(db_path, scope=["vault", "semantic"])
print(json.dumps(result, indent=2, default=str))
sys.exit(1 if result.get("errors") else 0)
PY
then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

if [ $EXIT_CODE -eq 0 ]; then
    log "=== rebalance obsidian vault embeddings complete ==="
else
    log "=== rebalance obsidian vault embeddings finished with errors (see JSON above) ==="
fi

rb_trim_logs

exit $EXIT_CODE
