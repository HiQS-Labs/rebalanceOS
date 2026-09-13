#!/bin/bash
# Rebalance Daily work synthesis canary (GH-210).
set -euo pipefail

REBALANCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$REBALANCE_DIR/scripts/lib/scheduler_common.sh"
rb_job_init "daily-work-synthesis" 14

"$PYTHON" "$REBALANCE_DIR/utils/daily_work_synthesis.py" \
  --config "$REBALANCE_DIR/temp/daily-work-synthesis.json"
