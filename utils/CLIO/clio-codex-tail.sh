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
#   cursor  = per-file inode + byte offset, advanced only through terminating
#             newlines and only after the writer accepted every row of the
#             chunk. Re-delivery after a crash is safe: the writer suppresses
#             already-seen IDs.
#   rescan  = inode change or size regression resets the offset to 0.
#   first sighting = start at end-of-file (no history import) unless
#             CLIO_TAIL_BACKFILL=1, which imports the existing file once.
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

state_lookup() { # $1 = path -> echoes "inode offset"; nonzero when unseen
  [ -f "$STATE" ] || return 1
  hit=$(awk -F'\t' -v p="$1" '$1 == p { print $2, $3; exit }' "$STATE")
  [ -n "$hit" ] && { printf '%s\n' "$hit"; return 0; }
  return 1
}

state_update() { # $1 = path, $2 = inode, $3 = offset
  tmp="$STATE.tmp.$$"
  if [ -f "$STATE" ]; then
    awk -F'\t' -v p="$1" '$1 != p' "$STATE" > "$tmp"
  else
    : > "$tmp"
  fi
  printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$tmp"
  mv "$tmp" "$STATE"
}

# Read one rollout from $2 (byte offset), emit one JSON row per user prompt on
# stdout and "CONSUMED <bytes>" on stderr. Byte-exact: the cursor only ever
# lands after a terminating newline, so multi-byte UTF-8 cannot corrupt it.
# Session context is recovered by walking the file from the START (session_meta
# lives at line 1 and is not re-read by an offset resume); only rows whose line
# begins at or after the offset are emitted.
extract_rows() {
  python3 - "$1" "$2" <<'PYEOF'
import json, sys

path, offset = sys.argv[1], int(sys.argv[2])
with open(path, "rb") as fh:
    data = fh.read()

cut = data.rfind(b"\n")
if cut == -1 or cut < offset:
    print("CONSUMED 0", file=sys.stderr)
    sys.exit(0)
consumed = cut + 1 - offset

session_id, cwd = "", ""
pos = 0
for line in data[:cut].split(b"\n"):
    line_start, pos = pos, pos + len(line) + 1
    if not line.strip():
        continue
    try:
        obj = json.loads(line)
    except Exception:
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
    }, ensure_ascii=False))
print(f"CONSUMED {consumed}", file=sys.stderr)
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
    cached_inode=${cached%% *}
    cached_offset=${cached##* }
    case "$cached_offset" in ''|*[!0-9]*) cached_offset=0 ;; esac
    if [ "$cached_inode" != "$inode" ] || [ "$size" -lt "$cached_offset" ]; then
      offset=0          # rotated or truncated -> full rescan (IDs suppress dups)
    else
      offset=$cached_offset
    fi
  elif [ "$BACKFILL" = "1" ]; then
    offset=0
  else
    offset=$size        # first sighting: start now, no history import
    state_update "$file" "$inode" "$offset"
    continue
  fi

  [ "$offset" -ge "$size" ] && { state_update "$file" "$inode" "$offset"; continue; }

  rows_file=$(mktemp "${TMPDIR:-/tmp}/clio-codex-rows.XXXXXX")
  err_file=$(mktemp "${TMPDIR:-/tmp}/clio-codex-err.XXXXXX")
  if ! python_ok=$(extract_rows "$file" "$offset" > "$rows_file" 2> "$err_file" && echo yes); then
    diag "rollout parse failed: $file"
    rm -f "$rows_file" "$err_file"
    continue
  fi
  consumed=$(sed -n 's/^CONSUMED //p' "$err_file" | head -1)
  rm -f "$err_file"
  case "$consumed" in ''|*[!0-9]*) consumed=0 ;; esac

  chunk_ok=1
  while IFS= read -r row; do
    [ -z "$row" ] && continue
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
    state_update "$file" "$inode" "$((offset + consumed))"
  else
    skipped=$((skipped + 1))
  fi
done < <(find "$CODEX_SESSIONS" -type f -name 'rollout-*.jsonl' -print0 2>/dev/null)

echo "clio-codex-tail: delivered=$delivered deferred_files=$skipped"
exit 0
