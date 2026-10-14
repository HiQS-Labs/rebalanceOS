#!/bin/bash
# GH-296 5.1: old guard (main checkout @ 4349ff5) vs fixed guard (task clone), same Mac, back to back.
OLD="<repos>/rebalanceOS"; NEW="<repos>/rebalanceOS-gh296-job-guard"
PY="$OLD/.venv/bin/python"; D=$(dirname "$0"); res="$D/results.csv"
echo "mode,job,start,exit,secs,swap_used_mb,swap_total_mb,free_pct,compressor_gb" > "$res"
snap() { local sw=$(sysctl -n vm.swapusage); echo "$(echo "$sw"|sed -E 's/.*used = ([0-9.]+)M.*/\1/'),$(echo "$sw"|sed -E 's/total = ([0-9.]+)M.*/\1/'),$(memory_pressure -Q|awk -F': ' '/free percentage/{gsub("%","",$2);print $2}'),$(vm_stat|awk -v ps=$(sysctl -n hw.pagesize) '/occupied by compressor/{gsub("\\.","",$5);printf "%.2f",$5*ps/1e9}')"; }
for mode in old fixed; do
  if [ $mode = old ]; then R="$OLD"; else R="$NEW"; fi
  for j in pulse-warning-watch github-sync obsidian-vault-embeddings; do
    case $j in
      pulse-warning-watch) c=("$PY" "$R/scripts/pulse_warning_watch.py" --url http://127.0.0.1:8767/ --log "$OLD/temp/pulse-warning-watch.jsonl" --state "$OLD/temp/pulse-warning-watch.state.json"); t=300;;
      github-sync) c=("$R/scripts/github_sync.sh"); t=7200;;
      obsidian-vault-embeddings) c=("$R/scripts/obsidian_vault_embeddings.sh"); t=7200;;
    esac
    m=$(snap); st=$(date +%s); s0=$(date +%H:%M:%S)
    RB_PYTHON="$PY" REBALANCE_CONFIG="$OLD/temp/rbos.config" "$PY" "$R/utils/job_guard.py" --name scheduler-$j --max-runtime-seconds $t -- "${c[@]}" > "$D/$mode-$j.log" 2>&1
    echo "$mode,$j,$s0,$?,$(( $(date +%s)-st )),$m" >> "$res"
  done
done
cat "$res"
