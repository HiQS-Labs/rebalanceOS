#!/bin/bash
# CLIO Agy tailer (GH-139) — turns user prompts from Agy (Antigravity CLI)
# conversation transcripts into CLIO JSONL rows (agent=agy). Strictly read-only
# over the source; all writes go through the shared capture writer.
#
# Source of record: per-conversation FULL transcripts at
#   $CLIO_AGY_ROOT/brain/<conversation-id>/.system_generated/logs/transcript_full.jsonl
# (default CLIO_AGY_ROOT=$HOME/.gemini/antigravity-cli). transcript.jsonl is
# deliberately NOT used — it truncates large text fields. Only rows where
# source == USER_EXPLICIT and type == USER_INPUT carry a submitted prompt;
# the conversation id is the brain directory name. Companion SQLite stores
# are indexes and are never read.
#
# Delivery contract (GH-139 invariant 3, at-least-once): identical to the
# Codex tailer — inode+offset cursor advanced only through terminating
# newlines and only after the writer accepted the chunk, rescan on inode
# change or size regression, no history import on first sighting unless
# CLIO_TAIL_BACKFILL=1, and a busy append lock aborts without advancing.
set -euo pipefail

AGY_ROOT="${CLIO_AGY_ROOT:-$HOME/.gemini/antigravity-cli}"
STATE="$HOME/.claude/prompt-log-agy-tail.state"
TAIL_LOCK="$HOME/.claude/prompt-log-agy-tail.lock"
WRITER="$HOME/.claude/hooks/clio-capture.sh"
ERRLOG="$HOME/.claude/prompt-log-errors.log"
BACKFILL="${CLIO_TAIL_BACKFILL:-0}"

diag() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) clio-agy-tail: $*" >> "$ERRLOG"; }

[ -x "$WRITER" ] || { echo "clio-agy-tail: shared writer not installed at $WRITER" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "clio-agy-tail: python3 is required" >&2; exit 1; }
[ -d "$AGY_ROOT/brain" ] || exit 0
command -v jq >/dev/null 2>&1 || { echo "clio-agy-tail: jq is required" >&2; exit 1; }

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

state_lookup() { # $1 = path -> echoes "inode offset"; nonzero when unseen
  [ -f "$STATE" ] || return 1
  hit=$(awk -F'\t' -v p="$1" '$1 == p { print $2, $3; exit }' "$STATE")
  [ -n "$hit" ] && { printf '%s\n' "$hit"; return 0; }
  return 1
}

state_update() {
  tmp="$STATE.tmp.$$"
  if [ -f "$STATE" ]; then
    awk -F'\t' -v p="$1" '$1 != p' "$STATE" > "$tmp"
  else
    : > "$tmp"
  fi
  printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$tmp"
  mv "$tmp" "$STATE"
}

# Read one transcript from $2 (byte offset), emit one JSON row per submitted
# user prompt on stdout and "CONSUMED <bytes>" on stderr. Rows are
# self-contained (session id comes from the path, not file content), so the
# read seeks straight to the offset — no full-file walk per tick. Byte-exact:
# the cursor only ever lands after a terminating newline.
extract_rows() {
  python3 - "$1" "$2" <<'PYEOF'
import json, sys
from datetime import datetime, timezone

def norm_ts(ts):
    """Normalize any ISO-8601 instant to UTC second precision (clio:id contract)."""
    if not ts:
        return ""
    if ts.endswith("Z") and len(ts) >= 20:
        return ts[:19] + "Z"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ""

path, offset = sys.argv[1], int(sys.argv[2])
with open(path, "rb") as fh:
    fh.seek(offset)
    data = fh.read()

cut = data.rfind(b"\n")
if cut == -1:
    print("CONSUMED 0", file=sys.stderr)
    sys.exit(0)
complete, consumed = data[:cut], cut + 1

parts = path.split("/")
session_id = ""
if "brain" in parts:
    session_id = parts[parts.index("brain") + 1]

for line in complete.split(b"\n"):
    if not line.strip():
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    if obj.get("source") != "USER_EXPLICIT" or obj.get("type") != "USER_INPUT":
        continue
    text = obj.get("content")
    if not isinstance(text, str) or not text.strip() or not session_id:
        continue
    print(json.dumps({
        "timestamp": norm_ts(str(obj.get("created_at") or "")),
        "repo": "",
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

while IFS= read -r file; do
  [ -f "$file" ] || continue
  inode=$(file_id "$file")
  size=$(file_size "$file")
  [ "$inode" = "?" ] && continue

  offset=""
  if cached=$(state_lookup "$file"); then
    cached_inode=${cached%% *}
    cached_offset=${cached##* }
    case "$cached_offset" in ''|*[!0-9]*) cached_offset=0 ;; esac
    if [ "$cached_inode" != "$inode" ] || [ "$size" -lt "$cached_offset" ]; then
      offset=0
    else
      offset=$cached_offset
    fi
  elif [ "$BACKFILL" = "1" ]; then
    offset=0
  else
    # Start now: land the cursor after the last TERMINATING newline so a
    # record completed after first sighting is still delivered.
    offset=$(file_last_newline "$file")
    state_update "$file" "$inode" "$offset"
    continue
  fi

  [ "$offset" -ge "$size" ] && { state_update "$file" "$inode" "$offset"; continue; }

  rows_file=$(mktemp "${TMPDIR:-/tmp}/clio-agy-rows.XXXXXX")
  err_file=$(mktemp "${TMPDIR:-/tmp}/clio-agy-err.XXXXXX")
  if ! python_ok=$(extract_rows "$file" "$offset" > "$rows_file" 2> "$err_file" && echo yes); then
    diag "transcript parse failed: $file (schema drift? failing soft)"
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
    printf '%s' "$row" | "$WRITER" --agent agy --record
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
done < <(find "$AGY_ROOT/brain" -type f -path '*/.system_generated/logs/transcript_full.jsonl' 2>/dev/null | sort)

echo "clio-agy-tail: delivered=$delivered deferred_files=$skipped"
exit 0
