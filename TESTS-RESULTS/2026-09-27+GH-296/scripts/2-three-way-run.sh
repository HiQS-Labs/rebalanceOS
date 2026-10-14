#!/bin/bash
R="<repos>/rebalanceOS"; PY="$R/.venv/bin/python"; G="$R/utils/job_guard.py"; D=$(dirname "$0")
res="$D/results.csv"; echo "mode,job,start,exit,secs,swap_used_mb,free_pct" > "$res"
JOBS=(pulse-sync pulse-web-sync pulse-warning-watch github-sync obsidian-vault-embeddings)
cmd() { case $1 in
  pulse-sync) echo "$R/scripts/pulse_sync.sh";; pulse-web-sync) echo "$R/scripts/pulse_web_sync.sh";;
  github-sync) echo "$R/scripts/github_sync.sh";; obsidian-vault-embeddings) echo "$R/scripts/obsidian_vault_embeddings.sh";; esac; }
tmo() { case $1 in pulse-sync) echo 1800;; pulse-warning-watch) echo 300;; *) echo 7200;; esac; }
for mode in old proposed none; do
  for j in "${JOBS[@]}"; do
    if [ $j = pulse-warning-watch ]; then c=("$PY" "$R/scripts/pulse_warning_watch.py" --url http://127.0.0.1:8767/ --log "$R/temp/pulse-warning-watch.jsonl" --state "$R/temp/pulse-warning-watch.state.json"); else c=("$(cmd $j)"); fi
    sw=$(sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/'); fp=$(memory_pressure -Q | awk -F': ' '/free percentage/{gsub("%","",$2);print $2}')
    st=$(date +%s); s0=$(date +%H:%M:%S); log="$D/$mode-$j.log"
    case $mode in
      old) "$PY" "$G" --name scheduler-$j --max-runtime-seconds $(tmo $j) --lifecycle-job $j -- "${c[@]}" > "$log" 2>&1;;
      proposed) REBALANCE_JOB_GUARD_MAX_COMPRESSOR_GB=999 "$PY" "$G" --name scheduler-$j --max-runtime-seconds $(tmo $j) --lifecycle-job $j -- "${c[@]}" > "$log" 2>&1;;
      none) /usr/bin/time -l "${c[@]}" > "$log" 2>&1;;
    esac
    echo "$mode,$j,$s0,$?,$(( $(date +%s)-st )),$sw,$fp" >> "$res"
  done
done
