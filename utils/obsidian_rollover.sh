#!/bin/bash
# rebalance OS — Obsidian daily notes rollover (launchd wrapper)
#
# WHY A WRAPPER: launchd cannot exec python3 directly against a script under
# ~/Documents — that folder is TCC-protected and a directly-launched interpreter
# is denied (Operation not permitted). Running through /bin/bash inherits the
# Full Disk Access grant the other rebalance launchd jobs already use, so no new
# Full Disk Access entry is required. (Mirrors scripts/pulse_sync.sh.)

set -euo pipefail

source "$(cd "$(dirname "$0")/.." && pwd)/scripts/lib/scheduler_common.sh"

SCRIPT="$REBALANCE_DIR/utils/obsidian_daily_rollover.py"

if [ ! -x "$PYTHON" ]; then
    echo "ERROR: rebalance venv not found at $PYTHON — obsidian-rollover needs it." >&2
    exit 1
fi

exec "$PYTHON" "$SCRIPT" "$@"
