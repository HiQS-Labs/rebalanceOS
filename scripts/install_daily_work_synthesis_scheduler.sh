#!/bin/bash
# Install the opt-in 15-minute Daily work synthesis canary (GH-210).
set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/install_common.sh"

CONFIG="$REBALANCE_DIR/temp/daily-work-synthesis.json"
if [ ! -f "$CONFIG" ]; then
    echo "ERROR: missing local canary config: $CONFIG" >&2
    echo "Create it with enabled=true only after approving private Terra egress and budgets." >&2
    exit 1
fi

mkdir -p "$HOME/Library/Logs/rebalance-os"

rb_install_launchd_job "com.rebalance-os.daily-work-synthesis" "scripts/daily_work_synthesis.sh"

echo "Installed Daily work synthesis canary every 900 seconds."
echo "Disable: set enabled=false in $CONFIG (or unload the rendered plist)."
