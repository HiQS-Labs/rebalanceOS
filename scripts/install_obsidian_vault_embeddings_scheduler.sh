#!/bin/bash
# Install (or reinstall) the rebalance OS hourly obsidian vault embeddings scheduler.
#
# What this does:
#   1. Renders com.rebalance-os.obsidian-vault-embeddings.plist.template (substituting the
#      local checkout path for {{REBALANCE_DIR}}) into ~/Library/LaunchAgents/.
#   2. Loads it so macOS runs obsidian_vault_embeddings.sh at HH:15 from 06:15 through 23:15.
#
# Policy: SCHEDULER.md (job com.rebalance-os.obsidian-vault-embeddings).

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/install_common.sh"

echo "Installing rebalance OS hourly obsidian vault embeddings scheduler..."
echo "  REBALANCE_DIR=$REBALANCE_DIR"

# GH-81 renamed this job from `vault-sync`. A rename in git is not a rename on
# the machine: the OLD plist stays loaded in launchd until something unloads it.
# Dropping `vault-sync` from SCHEDULER.md also drops it from stack.sh's managed
# set (stack.sh reads that table as its manifest), so `stack.sh down`/`purge`
# list it as unmanaged and will not take it down either. Left alone the operator
# ends up running BOTH jobs — and both fire at :15 doing the same vault+semantic
# write, which is exactly the same-minute collision SCHEDULER.md's freshness
# model forbids (GH-175).
#
# Retire it here, before the replacement is installed. Idempotent: every step is
# a no-op once the old job is gone, so reinstalling is safe.
_legacy_label="com.rebalance-os.vault-sync"
_legacy_plist="$HOME/Library/LaunchAgents/$_legacy_label.plist"
if "$LAUNCHCTL_BIN" list "$_legacy_label" > /dev/null 2>&1 || [ -f "$_legacy_plist" ]; then
    echo "  Retiring superseded job $_legacy_label (renamed to obsidian-vault-embeddings in GH-81)"
    "$LAUNCHCTL_BIN" unload "$_legacy_plist" 2>/dev/null || true
    rm -f "$_legacy_plist"
    if "$LAUNCHCTL_BIN" list "$_legacy_label" > /dev/null 2>&1; then
        echo "  WARNING: $_legacy_label is still registered after unload — remove it manually:" >&2
        echo "    launchctl bootout gui/\$UID/$_legacy_label" >&2
    else
        echo "  Retired $_legacy_label"
    fi
fi

rb_install_launchd_job "com.rebalance-os.obsidian-vault-embeddings" "scripts/obsidian_vault_embeddings.sh"

echo
echo "Done! rebalance OS will refresh obsidian vault embeddings on the :15 of every hour, 6 AM through 11 PM."
echo
echo "Commands:"
echo "  Check status:   launchctl list | grep obsidian-vault-embeddings"
echo "  Run now:        bash $SCRIPT_DIR/obsidian_vault_embeddings.sh"
echo "  View logs:      cat $REBALANCE_DIR/temp/logs/obsidian_vault_embeddings_\$(date +%Y-%m-%d).log"
echo "  Uninstall:      launchctl unload $RB_PLIST_DEST && rm $RB_PLIST_DEST"
