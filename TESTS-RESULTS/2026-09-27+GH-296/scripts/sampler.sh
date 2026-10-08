#!/bin/bash
# ts,free_pct,swap_used_mb,swap_total_mb,compressor_gb
out="$1"; echo "ts,free_pct,swap_used_mb,swap_total_mb,compressor_gb" > "$out"
ps=$(sysctl -n hw.pagesize)
while :; do
  f=$(memory_pressure -Q 2>/dev/null | awk -F': ' '/free percentage/{gsub("%","",$2);print $2}')
  sw=$(sysctl -n vm.swapusage)
  su=$(echo "$sw" | sed -E 's/.*used = ([0-9.]+)M.*/\1/'); st=$(echo "$sw" | sed -E 's/total = ([0-9.]+)M.*/\1/')
  c=$(vm_stat | awk -v ps=$ps '/occupied by compressor/{gsub("\\.","",$5); printf "%.2f", $5*ps/1e9}')
  echo "$(date +%H:%M:%S),$f,$su,$st,$c" >> "$out"; sleep 5
done
