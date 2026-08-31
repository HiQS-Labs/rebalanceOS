#!/bin/bash
# Fixture harness for utils/CLIO/clio-agy-tail.sh (GH-139 Phase 3).
#
# Exercises the at-least-once contract against a synthetic transcript tree:
# source/type row selection (only USER_EXPLICIT + USER_INPUT), start-now
# default, explicit backfill, restart-no-duplicates (tailer run twice with NO
# exporter in between), live append, truncated final record, rotation rescan,
# overlapping invocations, and a busy append lock.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TAILER="$ROOT/utils/CLIO/clio-agy-tail.sh"
FIXTURE="$ROOT/test/fixtures/clio/agy-transcript.jsonl"
INSTALL_DOC="$ROOT/utils/CLIO/INSTALL.md"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/clio-agy-tail.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || fail "python3 is required to run this harness"
command -v jq >/dev/null 2>&1 || fail "jq is required to run this harness"

setup_home() { # $1 = case dir; echoes the home path
  home="$1/home"
  mkdir -p "$home/.claude/hooks"
  awk '/^cat > ~\/\.claude\/hooks\/clio-capture\.sh << .EOF.$/{f=1;next} f&&/^EOF$/{exit} f' \
    "$INSTALL_DOC" > "$home/.claude/hooks/clio-capture.sh"
  [ -s "$home/.claude/hooks/clio-capture.sh" ] || fail "could not extract the shared writer"
  chmod +x "$home/.claude/hooks/clio-capture.sh"
  printf '%s\n' "$home"
}

new_transcript() { # $1 = AGY root, $2 = conversation id; echoes the path
  conv="$1/brain/$2/.system_generated/logs"
  mkdir -p "$conv"
  printf '%s\n' "$conv/transcript.jsonl"
}

log_count() { [ -f "$1" ] && wc -l < "$1" | tr -d ' ' || echo 0; }

CONV="0125ee13-24a0-46e7-a59e-d6005d4e1fab"

# -- 1. start-now default: pre-existing transcript history is NOT imported ---
home=$(setup_home "$TMP/start-now")
agyroot="$TMP/start-now/agy"
transcript=$(new_transcript "$agyroot" "$CONV")
cp "$FIXTURE" "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$out" = "clio-agy-tail: delivered=0 deferred_files=0" ] \
  || fail "start-now: expected zero delivered rows, got: $out"
[ "$(log_count "$home/.claude/prompt-log.jsonl")" = "0" ] \
  || fail "start-now: history import happened despite the default"

# -- 2. explicit backfill imports ONLY the user rows --------------------------
home=$(setup_home "$TMP/backfill")
agyroot="$TMP/backfill/agy"
transcript=$(new_transcript "$agyroot" "$CONV")
cp "$FIXTURE" "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" CLIO_TAIL_BACKFILL=1 "$TAILER")
[ "$out" = "clio-agy-tail: delivered=2 deferred_files=0" ] \
  || fail "backfill: expected the two user prompts delivered, got: $out"
log="$home/.claude/prompt-log.jsonl"
[ "$(log_count "$log")" = "2" ] || fail "backfill: expected 2 JSONL rows"
grep -qF '"agent":"agy"' "$log" || fail "backfill: agent not stamped"
grep -qF '"session_id":"'$CONV'"' "$log" || fail "backfill: conversation id not used as session"
grep -qF '"timestamp":"2026-08-24T03:46:13Z"' "$log" || fail "backfill: created_at not carried as UTC"
grep -qF 'Planner response text' "$log" \
  && fail "backfill: a MODEL row leaked into the log" || true
grep -qF 'Checkpoint metadata' "$log" \
  && fail "backfill: a SYSTEM row leaked into the log" || true

# -- 3. restart-no-duplicates: tailer runs twice, NO exporter in between ------
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$out" = "clio-agy-tail: delivered=0 deferred_files=0" ] \
  || fail "restart: expected an idle second run, got: $out"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$(log_count "$log")" = "2" ] || fail "restart x2: duplicate rows appeared"
ids=$(jq -r '(.session_id + ":" + .timestamp)' "$log" | sort -u | wc -l | tr -d ' ')
[ "$ids" = "2" ] || fail "restart: JSONL contains duplicate IDs"

# -- 4. live append: only the new prompt is delivered -------------------------
printf '%s\n' '{"content":"This is the third mock Agy user prompt, appended live after the first tailer pass, long enough to clear the capture threshold.","created_at":"2026-08-24T03:50:00Z","source":"USER_EXPLICIT","status":"DONE","step_index":5,"type":"USER_INPUT"}' >> "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$out" = "clio-agy-tail: delivered=1 deferred_files=0" ] \
  || fail "live append: expected 1 new row, got: $out"
[ "$(log_count "$log")" = "3" ] || fail "live append: expected 3 JSONL rows"

# -- 5. truncated final record: retried, never written half -------------------
printf '%s' '{"content":"This is the fourth mock Agy user prompt, deliberately left unfinished on the wr' >> "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$(log_count "$log")" = "3" ] \
  || fail "truncated record: a partial record was written"
printf '%s ites with no trailing newline.","created_at":"2026-08-24T03:51:00Z","source":"USER_EXPLICIT","status":"DONE","step_index":6,"type":"USER_INPUT"}\n' >> "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$out" = "clio-agy-tail: delivered=1 deferred_files=0" ] \
  || fail "truncated record: completion was not delivered on the next run"
[ "$(log_count "$log")" = "4" ] || fail "truncated record: expected 4 JSONL rows"

# -- 6. rotation: replaced transcript rescans; IDs suppress duplicates --------
cp "$FIXTURE" "$transcript.new" && mv "$transcript.new" "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$(log_count "$log")" = "4" ] \
  || fail "rotation: rescan duplicated rows (expected suppression by ID)"

# -- 7. overlapping invocations: a busy tailer lock is a silent no-op ---------
lock="$home/.claude/prompt-log-agy-tail.lock"
mkdir "$lock"
before=$(log_count "$log")
HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER" || fail "busy tailer lock: invocation must exit 0"
[ "$(log_count "$log")" = "$before" ] || fail "busy tailer lock: rows changed"
rm -rf "$lock"

# -- 8. busy append lock: the chunk is deferred, cursor NOT advanced ----------
applock="$home/.claude/prompt-log.lock"
mkdir "$applock"
date +%s > "$applock/born"
printf '%s\n' '{"content":"This is the fifth mock Agy user prompt, written while the append lock is held by another writer, long enough to clear the threshold.","created_at":"2026-08-24T03:52:00Z","source":"USER_EXPLICIT","status":"DONE","step_index":7,"type":"USER_INPUT"}' >> "$transcript"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$out" = "clio-agy-tail: delivered=0 deferred_files=1" ] \
  || fail "append lock busy: expected the file to be deferred, got: $out"
[ "$(log_count "$log")" = "4" ] || fail "append lock busy: a row was written anyway"
rm -rf "$applock"
out=$(HOME="$home" CLIO_AGY_ROOT="$agyroot" "$TAILER")
[ "$out" = "clio-agy-tail: delivered=1 deferred_files=0" ] \
  || fail "append lock freed: the deferred chunk was not delivered"
[ "$(log_count "$log")" = "5" ] || fail "append lock freed: expected 5 JSONL rows"

echo "PASS: agy tailer"
