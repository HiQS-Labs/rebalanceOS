#!/bin/bash
# CLIO Codex tailer (GH-139) — turns user prompts from Codex session rollouts
# into CLIO JSONL rows (agent=codex). Strictly read-only over the source; all
# writes go through the shared capture writer.
#
# Source of record: $CODEX_HOME/sessions/**/rollout-*.jsonl. Only
# event_msg/user_message payloads carry submitted text; session identity and
# cwd come from the nearest preceding session_meta. response_item entries are
# never parsed — product/context material can be combined with user input
# there. history.jsonl is deliberately not used: it is TUI-only and can be
# disabled entirely.
#
# Delivery contract (GH-139 invariant 3, at-least-once):
#   cursor  = per-file inode + byte offset, always landing after a terminating
#             newline (first sighting included), advanced only after the
#             writer accepted the chunk. Re-delivery after a crash is safe:
#             the writer suppresses already-seen IDs.
#   context = session id + cwd are checkpointed WITH the cursor, so each tick
#             reads only new bytes; a state row without context triggers one
#             recovery pass from byte 0. In-chunk session_meta entries (resume
#             forks) update the context in file order.
#   rescan  = inode change or size regression resets the offset to 0.
#   first sighting = start at the last terminating newline (no history import)
#             unless CLIO_TAIL_BACKFILL=1, which imports from byte 0 once.
#   overlap = a tailer lock serializes invocations; a busy lock is a silent
#             no-op (the next tick catches up).
#   lock-busy on the shared append lock (writer exit 3) aborts WITHOUT
#             advancing the cursor; the chunk is retried next run.
set -euo pipefail

CODEX_SESSIONS="${CODEX_HOME:-$HOME/.codex}/sessions"
STATE="$HOME/.claude/prompt-log-codex-tail.state"
TAIL_LOCK="$HOME/.claude/prompt-log-codex-tail.lock"
WRITER="$HOME/.claude/hooks/clio-capture.sh"
ERRLOG="$HOME/.claude/prompt-log-errors.log"
BACKFILL="${CLIO_TAIL_BACKFILL:-0}"

diag() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) clio-codex-tail: $*" >> "$ERRLOG"; }

[ -x "$WRITER" ] || { echo "clio-codex-tail: shared writer not installed at $WRITER" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "clio-codex-tail: python3 is required" >&2; exit 1; }
[ -d "$CODEX_SESSIONS" ] || exit 0
command -v jq >/dev/null 2>&1 || { echo "clio-codex-tail: jq is required" >&2; exit 1; }

# Overlapping invocations: busy tailer lock is a silent no-op, never a failure.
mkdir "$TAIL_LOCK" 2>/dev/null || exit 0
trap 'rm -rf "$TAIL_LOCK"' EXIT
date +%s > "$TAIL_LOCK/born" 2>/dev/null || true

file_id() { stat -f '%i' "$1" 2>/dev/null || stat -c '%i' "$1" 2>/dev/null || echo "?"; }
file_size() { stat -f '%z' "$1" 2>/dev/null || stat -c '%s' "$1" 2>/dev/null || echo 0; }
file_last_newline() { # byte offset just after the last terminating newline (0 if none)
  python3 - "$1" <<'PYEOF'
import sys
with open(sys.argv[1], "rb") as fh:
    print(fh.read().rfind(b"\n") + 1)
PYEOF
}

# State: path<TAB>inode<TAB>offset<TAB>session_id<TAB>cwd (tab-sanitized).
state_lookup() { # $1 = path -> echoes "inode<TAB>offset<TAB>sid<TAB>cwd"; nonzero when unseen
  [ -f "$STATE" ] || return 1
  hit=$(awk -F'\t' -v p="$1" '$1 == p { printf "%s\t%s\t%s\t%s\n", $2, $3, $4, $5; exit }' "$STATE")
  [ -n "$hit" ] && { printf '%s\n' "$hit"; return 0; }
  return 1
}

state_update() { # $1 = path, $2 = inode, $3 = offset, $4 = session_id, $5 = cwd
  tmp="$STATE.tmp.$$"
  if [ -f "$STATE" ]; then
    awk -F'\t' -v p="$1" '$1 != p' "$STATE" > "$tmp"
  else
    : > "$tmp"
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" \
    "$(printf '%s' "$4" | tr '\t' ' ')" "$(printf '%s' "$5" | tr '\t' ' ')" >> "$tmp"
  mv "$tmp" "$STATE"
}

# Read a rollout from $2 (byte offset) with optional session context $3/$4.
# Emits one JSON row per user prompt (with a trailing cwd field for the shell
# to resolve repo/branch from) on stdout; on stderr: "CONSUMED <bytes>",
# "CTX<tab>sid<tab>cwd", "MALFORMED <n>". Byte-exact: the cursor only ever
# lands after a terminating newline. When context is known the read seeks
# straight to the offset; otherwise one pass from byte 0 recovers the nearest
# preceding session_meta before the offset.
extract_rows() {
  python3 - "$1" "$2" "${3:-}" "${4:-}" <<'PYEOF'
import json, sys

path, offset = sys.argv[1], int(sys.argv[2])
ctx_sid, ctx_cwd = sys.argv[3], sys.argv[4]
with open(path, "rb") as fh:
    if offset > 0 and ctx_sid:
        fh.seek(offset)
        data, scan_start = fh.read(), offset
    else:
        data, scan_start = fh.read(), 0

cut = data.rfind(b"\n")
malformed = 0
session_id, cwd = ctx_sid, ctx_cwd
if cut != -1 and cut >= (offset - scan_start):
    consumed = cut + 1
    if scan_start != offset:
        session_id, cwd = "", ""
    session_id, cwd = (ctx_sid, ctx_cwd) if scan_start == offset else ("", "")
    pos = scan_start
    for line in data[:cut].split(b"\n"):
        line_start, pos = pos, pos + len(line) + 1
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            malformed += 1
            continue
        payload = obj.get("payload") or {}
        if obj.get("type") == "session_meta":
            session_id = str(payload.get("id") or session_id)
            cwd = str(payload.get("cwd") or cwd)
            continue
        if line_start < offset:
            continue
        if obj.get("type") != "event_msg" or payload.get("type") != "user_message":
            continue
        text = payload.get("message")
        if not isinstance(text, str) or not text.strip() or not session_id:
            continue
        repo = cwd.rstrip("/").rsplit("/", 1)[-1] if cwd else ""
        print(json.dumps({
            "timestamp": str(obj.get("timestamp") or ""),
            "repo": repo,
            "branch": "",
            "machine": "",
            "session_id": session_id,
            "prompt": text,
            "cwd": cwd,
        }, ensure_ascii=False))
else:
    consumed = 0
print(f"CONSUMED {consumed}", file=sys.stderr)
print(f"CTX\t{session_id}\t{cwd}", file=sys.stderr)
print(f"MALFORMED {malformed}", file=sys.stderr)
PYEOF
}

delivered=0
skipped=0

while IFS= read -r -d '' file; do
  inode=$(file_id "$file")
  size=$(file_size "$file")
  [ "$inode" = "?" ] && continue

  offset=""
  if cached=$(state_lookup "$file"); then
    cached_inode=$(printf '%s' "$cached" | awk -F'\t' '{print $1}')
    cached_offset=$(printf '%s' "$cached" | awk -F'\t' '{print $2}')
    cached_sid=$(printf '%s' "$cached" | awk -F'\t' '{print $3}')
    cached_cwd=$(printf '%s' "$cached" | awk -F'\t' '{print $4}')
    case "$cached_offset" in ''|*[!0-9]*) cached_offset=0 ;; esac
    if [ "$cached_inode" != "$inode" ] || [ "$size" -lt "$cached_offset" ]; then
      offset=0          # rotated or truncated -> full rescan (IDs suppress dups)
      cached_sid=""; cached_cwd=""
    else
      offset=$cached_offset
    fi
  elif [ "$BACKFILL" = "1" ]; then
    offset=0
    cached_sid=""; cached_cwd=""
  else
    # Start now: land the cursor after the last TERMINATING newline so a
    # record completed after first sighting is still delivered.
    offset=$(file_last_newline "$file")
    state_update "$file" "$inode" "$offset" "" ""
    continue
  fi

  [ "$offset" -ge "$size" ] && { state_update "$file" "$inode" "$offset" "$cached_sid" "$cached_cwd"; continue; }

  rows_file=$(mktemp "${TMPDIR:-/tmp}/clio-codex-rows.XXXXXX")
  err_file=$(mktemp "${TMPDIR:-/tmp}/clio-codex-err.XXXXXX")
  if ! python_ok=$(extract_rows "$file" "$offset" "$cached_sid" "$cached_cwd" > "$rows_file" 2> "$err_file" && echo yes); then
    diag "rollout parse failed: $file"
    rm -f "$rows_file" "$err_file"
    continue
  fi
  consumed=$(sed -n 's/^CONSUMED //p' "$err_file" | head -1)
  ctx_line=$(sed -n 's/^CTX\t//p' "$err_file" | head -1)
  ctx_sid=$(printf '%s' "$ctx_line" | awk -F'\t' '{print $1}')
  ctx_cwd=$(printf '%s' "$ctx_line" | awk -F'\t' '{print $2}')
  new_malformed=$(sed -n 's/^MALFORMED //p' "$err_file" | head -1)
  rm -f "$err_file"
  case "$consumed" in ''|*[!0-9]*) consumed=0 ;; esac
  case "$new_malformed" in ''|*[!0-9]*) new_malformed=0 ;; esac
  [ "$new_malformed" -gt 0 ] && diag "$new_malformed malformed source line(s) skipped in $file"

  chunk_ok=1
  last_cwd=""; last_repo=""; last_branch=""
  while IFS= read -r row; do
    [ -z "$row" ] && continue
    # Resolve repo/branch from the session cwd (cached per distinct cwd).
    row_cwd=$(printf '%s' "$row" | jq -r '.cwd // ""')
    if [ -n "$row_cwd" ]; then
      if [ "$row_cwd" != "$last_cwd" ]; then
        last_cwd="$row_cwd"
        last_repo=$(basename "$(git -C "$row_cwd" rev-parse --show-toplevel 2>/dev/null || echo "$row_cwd")")
        last_branch=$(git -C "$row_cwd" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
      fi
      row=$(printf '%s' "$row" | jq -c --arg repo "$last_repo" --arg branch "$last_branch" '.repo = $repo | .branch = $branch')
    fi
    set +e
    printf '%s' "$row" | "$WRITER" --agent codex --record
    rc=$?
    set -e
    if [ "$rc" -eq 3 ]; then
      diag "append lock busy — cursor not advanced; chunk will retry"
      chunk_ok=0
      break
    elif [ "$rc" -ne 0 ]; then
      diag "writer rejected a row (rc=$rc) — cursor not advanced"
      chunk_ok=0
      break
    fi
    delivered=$((delivered + 1))
  done < "$rows_file"
  rm -f "$rows_file"

  if [ "$chunk_ok" = 1 ]; then
    state_update "$file" "$inode" "$((offset + consumed))" "$ctx_sid" "$ctx_cwd"
  else
    skipped=$((skipped + 1))
  fi
done < <(find "$CODEX_SESSIONS" -type f -name 'rollout-*.jsonl' -print0 2>/dev/null)

echo "clio-codex-tail: delivered=$delivered deferred_files=$skipped"
exit 0
