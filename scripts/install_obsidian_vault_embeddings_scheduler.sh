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

rb_install_launchd_job "com.rebalance-os.obsidian-vault-embeddings" "scripts/obsidian_vault_embeddings.sh"

echo
echo "Done! rebalance OS will refresh obsidian vault embeddings on the :15 of every hour, 6 AM through 11 PM."
echo
echo "Commands:"
echo "  Check status:   launchctl list | grep obsidian-vault-embeddings"
echo "  Run now:        bash $SCRIPT_DIR/obsidian_vault_embeddings.sh"
echo "  View logs:      cat $REBALANCE_DIR/temp/logs/obsidian_vault_embeddings_\$(date +%Y-%m-%d).log"
echo "  Uninstall:      launchctl unload $RB_PLIST_DEST && rm $RB_PLIST_DEST"
