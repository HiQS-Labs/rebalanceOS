#!/bin/bash
# Install (or reinstall) the rebalance OS daily vault synthesis (GH-74).
#
# What this does:
#   1. Renders com.rebalance-os.daily-synthesis.plist.template into
#      ~/Library/LaunchAgents/.
#   2. Loads it so macOS runs utils/daily_synthesis.sh at 18:20 daily (or on
#      next wake if the Mac was asleep). A catch-up run that fires after
#      midnight skips itself — see the script's late-run guard.
#
# Replaces the two former installers, install_obsidian_daily_sync_scheduler.sh
# and install_git_pulse_daily_synthesis_scheduler.sh (GH-74): the pulse summary
# and the git-pulse summary now run as one process, one launchd job, so there
# is no ordering dependency between two separate fire times to preserve.
#
# RunAtLoad is intentionally false in the template — loading should not fire an
# off-schedule summary write.
#
# Usage:
#   bash scripts/install_daily_synthesis_scheduler.sh
#
# Policy: SCHEDULER.md (job com.rebalance-os.daily-synthesis).

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/install_common.sh"

echo "Installing rebalance OS daily vault synthesis (18:20 daily)..."
echo "  REBALANCE_DIR=$REBALANCE_DIR"

# Job log lives outside the TCC-protected ~/Documents tree.
mkdir -p "$HOME/Library/Logs/rebalance-os"

rb_install_launchd_job "com.rebalance-os.daily-synthesis" "utils/daily_synthesis.sh"

echo
echo "Done! A Gemini daily-activity summary (and, if configured, a Git Pulse"
echo "summary + CLIO export) lands in Today's Notes at 18:20 (or next wake)."
echo
echo "Commands:"
echo "  Check status: launchctl list | grep daily-synthesis"
echo "  View logs:    cat $HOME/Library/Logs/rebalance-os/daily-synthesis.log"
echo "  Dry run now:  bash utils/daily_synthesis.sh --dry-run --force"
echo "  Status now:   bash utils/daily_synthesis.sh --status"
echo "  Uninstall:    launchctl unload $RB_PLIST_DEST && rm $RB_PLIST_DEST"
