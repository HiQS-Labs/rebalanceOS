rebalance_skill_dir() { echo "rebalance: not found" >&2; return 1; }
if REBALANCE_SKILL="$(rebalance_skill_dir)"; then
  bash "$REBALANCE_SKILL/collect.sh"
else
  false
fi
