#!/bin/bash
# Install (or reinstall) the rebalance OS twice-daily progress digest (GH-142).
#
# What this does:
#   1. Renders com.rebalance-os.hiqs-digest.plist.template (substituting
#      {{REBALANCE_DIR}}) into ~/Library/LaunchAgents/.
#   2. Loads it so macOS runs scripts/hiqs_digest.sh at 1:05 PM and 5:05 PM
#      local time.
#
# The digest is pushed to the shared pulse repo; AEGIS Sleuth's snapshot-relay
# posts it to Slack. Nothing here talks to Slack.
#
# WHERE TO INSTALL THIS: on the always-on machine, from the declared runtime
# root. launchd plists pin absolute paths, so the job belongs to exactly one
# checkout — running this from the wrong clone silently rebinds the fleet
# (GH-36, GH-59). A laptop that sleeps through 13:05 runs the job on next wake;
# the digest stamps its own generated_at so a late post says so in the channel.
#
# SECRETS: synthesis needs GEMINI_API_KEY. NEVER add it to the template (tracked
# in git). After installing, either add it to the RENDERED plist's
# EnvironmentVariables dict (~/Library/LaunchAgents is gitignored) and re-run
# `launchctl unload`/`load`, or rely on the keyring lookup.
# Reinstalling OVERWRITES the rendered plist — a hand-added key must be re-added.
#
# COST: 2 Gemini calls per day. To stop them without a code change, add
# HIQS_DIGEST_LLM_DISABLE=1 to the rendered plist. That is an operator no-op,
# not a failure: the job exits 0 and publishes nothing.
#
# Usage:
#   bash scripts/install_hiqs_digest_scheduler.sh
#
# Policy: SCHEDULER.md (job com.rebalance-os.hiqs-digest).

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/install_common.sh"

echo "Installing rebalance OS progress digest (1:05 PM / 5:05 PM)..."
echo "  REBALANCE_DIR=$REBALANCE_DIR"

DEST="$HOME/Library/LaunchAgents/com.rebalance-os.hiqs-digest.plist"
if [ -f "$DEST" ] && grep -q "GEMINI_API_KEY" "$DEST"; then
    echo
    echo "  WARNING: the currently installed plist carries a hand-added"
    echo "  GEMINI_API_KEY. Reinstalling will remove it — re-add it to"
    echo "  $DEST afterwards and reload the job."
    echo
fi

# launchd opens StandardOutPath/StandardErrorPath itself and does NOT create missing parent
# directories — the redirect just fails, silently, and the job's output goes nowhere. Same
# line as install_daily_synthesis_scheduler.sh:32 and install_obsidian_rollover_scheduler.sh:26;
# rb_install_launchd_job only creates $REBALANCE_DIR/temp/logs, not this one.
mkdir -p "$HOME/Library/Logs/rebalance-os"

# The wrapper argument is not optional here: it makes rb_install_launchd_job verify the
# script exists and chmod +x it. Omitted, both guards are skipped, and any deploy that
# loses the file mode (rsync/tarball, core.fileMode=false) installs a job launchd cannot
# exec — failing at 13:05 with a bare "Operation not permitted" and no install-time warning.
rb_install_launchd_job "com.rebalance-os.hiqs-digest" "scripts/hiqs_digest.sh"

echo
echo "Verify without publishing anything:"
echo "  bash scripts/hiqs_digest.sh --dry-run"
echo
echo "Logs: \$HOME/Library/Logs/rebalance-os/hiqs-digest.log"
echo "      $REBALANCE_DIR/temp/logs/hiqs_digest_\$(date +%Y-%m-%d).log"
