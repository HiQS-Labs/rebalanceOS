#!/bin/bash
# Fixture harness for utils/CLIO/clio-codex-tail.sh (GH-139 Phase 2).
#
# Exercises the at-least-once contract against a synthetic rollout tree:
# start-now default, explicit backfill, restart-no-duplicates (tailer run
# twice with NO exporter in between), truncated final record, rotation
# rescan, overlapping invocations, and a busy append lock.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TAILER="$ROOT/utils/CLIO/clio-codex-tail.sh"
FIXTURE="$ROOT/test/fixtures/clio/codex-rollout.jsonl"
INSTALL_DOC="$ROOT/utils/CLIO/INSTALL.md"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/clio-codex-tail.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || fail "python3 is required to run this harness"
command -v jq >/dev/null 2>&1 || fail "jq is required to run this harness"

# Install the shared writer (extracted from INSTALL.md) into a throwaway HOME.
setup_home() { # $1 = case dir; echoes the home path
  home="$1/home"
  mkdir -p "$home/.claude/hooks" "$home/.zcode"
  awk '/^cat > ~\/\.claude\/hooks\/clio-capture\.sh << .EOF.$/{f=1;next} f&&/^EOF$/{exit} f' \
    "$INSTALL_DOC" > "$home/.claude/hooks/clio-capture.sh"
  [ -s "$home/.claude/hooks/clio-capture.sh" ] || fail "could not extract the shared writer"
  chmod +x "$home/.claude/hooks/clio-capture.sh"
  printf '%s\n' "$home"
}

new_session_file() { # $1 = CODEX_HOME; echoes the rollout path
  seedir="$1/sessions/2026/08/31"
  mkdir -p "$seedir"
  printf '%s\n' "$seedir/rollout-2026-08-31T10-00-00-abc.jsonl"
}

log_count() { [ -f "$1" ] && wc -l < "$1" | tr -d ' ' || echo 0; }

# -- 1. start-now default: pre-existing rollout history is NOT imported -------
home=$(setup_home "$TMP/start-now")
rollout=$(new_session_file "$TMP/start-now/codex")
cp "$FIXTURE" "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/start-now/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=0 deferred_files=0" ] \
  || fail "start-now: expected zero delivered rows, got: $out"
[ "$(log_count "$home/.claude/prompt-log.jsonl")" = "0" ] \
  || fail "start-now: history import happened despite the default"

# -- 2. explicit backfill imports the pre-existing rows -----------------------
home=$(setup_home "$TMP/backfill")
rollout=$(new_session_file "$TMP/backfill/codex")
cp "$FIXTURE" "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" CLIO_TAIL_BACKFILL=1 "$TAILER")
[ "$out" = "clio-codex-tail: delivered=2 deferred_files=0" ] \
  || fail "backfill: expected the two user prompts delivered, got: $out"
log="$home/.claude/prompt-log.jsonl"
[ "$(log_count "$log")" = "2" ] || fail "backfill: expected 2 JSONL rows"
grep -qF '"agent":"codex"' "$log" || fail "backfill: agent not stamped"
grep -qF '"timestamp":"2026-08-27T19:16:03Z"' "$log" \
  || fail "backfill: sub-second timestamp not normalized to UTC seconds"
grep -qF '"repo":"mock-repo"' "$log" || fail "backfill: repo not derived from session cwd"
grep -qF 'Injected AGENTS-style context' "$log" \
  && fail "backfill: response_item content leaked into the log" || true
grep -qF '"timestamp":"2026-08-27T19:16:20Z"' "$log" \
  && fail "backfill: agent_message was captured" || true

# -- 3. restart-no-duplicates: tailer runs twice, NO exporter in between ------
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=0 deferred_files=0" ] \
  || fail "restart: expected an idle second run, got: $out"
[ "$(log_count "$log")" = "2" ] || fail "restart: duplicate rows appeared"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$(log_count "$log")" = "2" ] || fail "restart x2: duplicate rows appeared"
ids=$(jq -r '(.session_id + ":" + .timestamp)' "$log" | sort -u | wc -l | tr -d ' ')
[ "$ids" = "2" ] || fail "restart: JSONL contains duplicate IDs"

# -- 4. live append: only the new prompt is delivered -------------------------
printf '%s\n' '{"payload":{"type":"user_message","message":"This is the third mock user prompt, appended live after the first tailer pass, long enough to clear the capture threshold."},"timestamp":"2026-08-27T19:20:00.000Z","type":"event_msg"}' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "live append: expected 1 new row, got: $out"
[ "$(log_count "$log")" = "3" ] || fail "live append: expected 3 JSONL rows"

# -- 5. truncated final record: retried, never written half -------------------
printf '%s' '{"payload":{"type":"user_message","message":"This is the fourth mock user prompt, deliberately left unfinished on the writes' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$(log_count "$log")" = "3" ] \
  || fail "truncated record: a partial record was written"
printf '%s with no trailing newline."},"timestamp":"2026-08-27T19:21:00.000Z","type":"event_msg"}\n' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "truncated record: completion was not delivered on the next run"
[ "$(log_count "$log")" = "4" ] || fail "truncated record: expected 4 JSONL rows"

# -- 6. rotation: replaced file rescans; IDs suppress duplicates --------------
cp "$FIXTURE" "$rollout.new" && mv "$rollout.new" "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$(log_count "$log")" = "4" ] \
  || fail "rotation: rescan duplicated rows (expected suppression by ID)"
ids=$(jq -r '(.session_id + ":" + .timestamp)' "$log" | sort -u | wc -l | tr -d ' ')
[ "$ids" = "4" ] || fail "rotation: duplicate IDs in the JSONL"

# -- 7. overlapping invocations: a busy tailer lock is a silent no-op ---------
lock="$home/.claude/prompt-log-codex-tail.lock"
mkdir "$lock"
before=$(log_count "$log")
HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER" || fail "busy tailer lock: invocation must exit 0"
[ "$(log_count "$log")" = "$before" ] || fail "busy tailer lock: rows changed"
rmdir "$lock"

# -- 8. busy append lock: the chunk is deferred, cursor NOT advanced ----------
applock="$home/.claude/prompt-log.lock"
mkdir "$applock"
date +%s > "$applock/born"
printf '%s\n' '{"payload":{"type":"user_message","message":"This is the fifth mock user prompt, written while the append lock is held by another writer, long enough to clear the threshold."},"timestamp":"2026-08-27T19:22:00.000Z","type":"event_msg"}' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=0 deferred_files=1" ] \
  || fail "append lock busy: expected the file to be deferred, got: $out"
[ "$(log_count "$log")" = "4" ] || fail "append lock busy: a row was written anyway"
rm -rf "$applock"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "append lock freed: the deferred chunk was not delivered"
[ "$(log_count "$log")" = "5" ] || fail "append lock freed: expected 5 JSONL rows"

echo "PASS: codex tailer"
