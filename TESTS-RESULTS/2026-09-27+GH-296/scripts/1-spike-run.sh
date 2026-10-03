#!/bin/bash
# usage: run.sh guarded|off
R="<repos>/rebalanceOS"; PY="$R/.venv/bin/python"; G="$R/utils/job_guard.py"
mode=$1; S=$(dirname "$0"); res="$S/results-$mode.csv"; echo "job,start,exit,secs" > "$res"
if [ "$mode" = off ]; then export REBALANCE_JOB_GUARD_MAX_COMPRESSOR_GB=999; extra=(--max-footprint-gb 999 --min-available-gb 0); else extra=(); fi
run() { local j=$1 t=$2; shift 2; local st=$(date +%s) s0=$(date +%H:%M:%S)
  "$PY" "$G" --name scheduler-$j --max-runtime-seconds $t --lifecycle-job $j "${extra[@]}" -- "$@" > "$S/$mode-$j.log" 2>&1
  echo "$j,$s0,$?,$(( $(date +%s)-st ))" >> "$res"; }
run pulse-sync 1800 "$R/scripts/pulse_sync.sh"
run pulse-web-sync 7200 "$R/scripts/pulse_web_sync.sh"
run pulse-warning-watch 300 "$PY" "$R/scripts/pulse_warning_watch.py" --url http://127.0.0.1:8767/ --log "$R/temp/pulse-warning-watch.jsonl" --state "$R/temp/pulse-warning-watch.state.json"
run github-sync 7200 "$R/scripts/github_sync.sh"
run obsidian-vault-embeddings 7200 "$R/scripts/obsidian_vault_embeddings.sh"
cat "$res"
