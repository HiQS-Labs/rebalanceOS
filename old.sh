rebalance_skill_dir() { echo "rebalance: not found" >&2; return 1; }
REBALANCE_SKILL="$(rebalance_skill_dir)" || exit 1
bash "$REBALANCE_SKILL/collect.sh"
