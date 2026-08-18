#!/bin/bash
# rebalance OS — Daily vault synthesis (launchd wrapper, GH-74)
#
# WHY A WRAPPER: launchd cannot exec python3 directly against a script that reads
# ~/Documents — that folder is TCC-protected and a directly-launched interpreter
# is denied (Operation not permitted). Running through /bin/bash inherits the Full
# Disk Access grant the other rebalance launchd jobs already use, so no new Full
# Disk Access entry is needed. (Mirrors utils/obsidian_rollover.sh.) The optional
# CLIO write does not need this (git-pulse-sync lives outside ~/Documents) but
# shares the wrapper since both destinations come out of the same script/run.
#
# Requires the project venv — it imports the rebalance package (pulse snapshot +
# Gemini synthesis). Fail loudly if absent rather than silently degrading.

set -euo pipefail

REBALANCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REBALANCE_DIR/utils/daily_synthesis.py"
PYTHON="$REBALANCE_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "ERROR: rebalance venv not found at $PYTHON — daily-synthesis needs it." >&2
    exit 1
fi

exec "$PYTHON" "$SCRIPT" "$@"
