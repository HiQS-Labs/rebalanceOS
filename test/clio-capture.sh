#!/bin/bash
# Fixture harness for the CLIO capture path (GH-139 schema v2).
#
# The shared writer (clio-capture.sh) and the Claude shim (log-prompt.sh) live
# as heredocs inside utils/CLIO/INSTALL.md, so this harness extracts both by
# MARKER (not line numbers — the heredocs get edited) and runs them against a
# throwaway $HOME. Legacy cases run through the SHIM to prove delegation; the
# new agent cases run the writer directly.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
INSTALL_DOC="$ROOT/utils/CLIO/INSTALL.md"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/clio-capture.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

WRITER="$TMP/clio-capture.sh"
HOOK="$TMP/log-prompt.sh"
awk '/^cat > ~\/\.claude\/hooks\/clio-capture\.sh << .EOF.$/{f=1;next} f&&/^EOF$/{exit} f' \
  "$INSTALL_DOC" > "$WRITER"
awk '/^cat > ~\/\.claude\/hooks\/log-prompt\.sh << .EOF.$/{f=1;next} f&&/^EOF$/{exit} f' \
  "$INSTALL_DOC" > "$HOOK"
[ -s "$WRITER" ] || { echo "FAIL: could not extract clio-capture.sh from $INSTALL_DOC" >&2; exit 1; }
[ -s "$HOOK" ] || { echo "FAIL: could not extract log-prompt.sh from $INSTALL_DOC" >&2; exit 1; }
chmod +x "$WRITER" "$HOOK"

fail() { echo "FAIL: $*" >&2; exit 1; }

long_prompt="This is a substantive session-opening prompt that comfortably exceeds the one hundred character minimum threshold."

# Feed stdin to a script under a fresh $HOME; echo the resulting line count.
# Usage: run_case <script> <case> <input-json> [env assignments...]
run_case() {
  script=$1; case_name=$2; input=$3; shift 3
  home="$TMP/$case_name"
  mkdir -p "$home/.claude"
  printf '%s' "$input" \
    | env HOME="$home" CLAUDE_PROJECT_DIR="$ROOT" "$@" "$script" \
    || fail "$case_name: capture exited non-zero (it must always exit 0)"
  log="$home/.claude/prompt-log.jsonl"
  [ -f "$log" ] || : > "$log"
  wc -l < "$log" | tr -d ' '
}

# Hook mode via the shim (Claude Code path; proves delegation + stamping).
run_hook() {
  case_name=$1; input=$2; shift 2
  run_case "$HOOK" "$case_name" "$input" "$@"
}

# Writer mode (direct invocation with writer args, e.g. --agent zcode [--record]).
run_writer() {
  case_name=$1; input=$2; shift 2
  home="$TMP/$case_name"
  mkdir -p "$home/.claude"
  printf '%s' "$input" \
    | env HOME="$home" CLAUDE_PROJECT_DIR="$ROOT" /bin/bash "$WRITER" "$@" \
    || fail "$case_name: writer exited non-zero where exit 0 was required"
  log="$home/.claude/prompt-log.jsonl"
  [ -f "$log" ] || : > "$log"
  wc -l < "$log" | tr -d ' '
}

# Writer hook mode with extra env assignments (e.g. the session-id fallback).
run_case_env() {
  case_name=$1; input=$2; shift 2
  home="$TMP/$case_name"
  mkdir -p "$home/.claude"
  printf '%s' "$input" \
    | env HOME="$home" CLAUDE_PROJECT_DIR="$ROOT" "$@" /bin/bash "$WRITER" --agent zcode \
    || fail "$case_name: writer exited non-zero where exit 0 was required"
  log="$home/.claude/prompt-log.jsonl"
  [ -f "$log" ] || : > "$log"
  wc -l < "$log" | tr -d ' '
}

json_input() { jq -nc --arg p "$1" '{session_id:"s1", prompt:$p}'; }

# ---------------- legacy suite (must keep passing through the shim) ---------

captures_substantive_prompt() {
  n=$(run_hook "substantive" "$(json_input "$long_prompt")")
  [ "$n" = "1" ] || fail "expected substantive prompt to be captured, got $n line(s)"
  grep -qF "session-opening prompt" "$TMP/substantive/.claude/prompt-log.jsonl" \
    || fail "captured line lost the prompt text"
}

skips_short_prompt() {
  n=$(run_hook "short" "$(json_input 'push it')")
  [ "$n" = "0" ] || fail "expected short prompt to be skipped, got $n line(s)"
}

boundary_is_inclusive() {
  exactly100=$(printf 'x%.0s' $(seq 1 100))
  n=$(run_hook "boundary" "$(json_input "$exactly100")")
  [ "$n" = "1" ] || fail "expected exactly-100-char prompt to be captured, got $n line(s)"
  n=$(run_hook "boundary99" "$(json_input "$(printf 'x%.0s' $(seq 1 99))")")
  [ "$n" = "0" ] || fail "expected 99-char prompt to be skipped, got $n line(s)"
}

skips_task_notification() {
  note='[SYSTEM NOTIFICATION - NOT USER INPUT]
This is an automated background-task event, NOT a message from the user.
<task-notification>
<task-id>b90l1vf7i</task-id>
<summary>Monitor event: "CLIO marathon phase progress + terminal state"</summary>
<event>marathon: phase 1/2 clio-p1-idempotent reviewer=agy round-cap=7</event>
</task-notification>'
  n=$(run_hook "tasknote" "$(json_input "$note")")
  [ "$n" = "0" ] || fail "expected task-notification to be skipped, got $n line(s)"
}

skips_bare_system_notification() {
  note='[SYSTEM NOTIFICATION - NOT USER INPUT]
This is an automated background-task event that is deliberately long enough to exceed one hundred characters on its own.'
  n=$(run_hook "sysnote" "$(json_input "$note")")
  [ "$n" = "0" ] || fail "expected bare SYSTEM NOTIFICATION to be skipped, got $n line(s)"
}

strips_injected_blocks_before_measuring() {
  padded="<system-reminder>$(printf 'y%.0s' $(seq 1 400))</system-reminder>short ask"
  n=$(run_hook "strip" "$(json_input "$padded")")
  [ "$n" = "0" ] || fail "expected length to be measured after stripping, got $n line(s)"
}

threshold_is_configurable() {
  n=$(run_hook "override" "$(json_input 'push it')" CLIO_MIN_PROMPT_CHARS=0)
  [ "$n" = "1" ] || fail "expected CLIO_MIN_PROMPT_CHARS=0 to capture a short prompt, got $n line(s)"
}

malformed_input_never_blocks() {
  home="$TMP/malformed"
  mkdir -p "$home/.claude"
  printf '%s' 'this is not json {{{' \
    | env HOME="$home" CLAUDE_PROJECT_DIR="$ROOT" "$HOOK" \
    || fail "malformed input made the hook exit non-zero"
  [ -s "$home/.claude/prompt-log-errors.log" ] \
    || fail "malformed input was not recorded in the error log"
  [ ! -s "$home/.claude/prompt-log.jsonl" ] \
    || fail "malformed input wrote a line to the prompt log"
}

captured_lines_are_valid_json() {
  home="$TMP/substantive"
  jq -e . "$home/.claude/prompt-log.jsonl" >/dev/null \
    || fail "captured line is not valid JSON"
}

# ---------------- schema v2 (GH-139) ----------------------------------------

stamps_agent_field_via_shim() {
  n=$(run_hook "agent-stamp" "$(json_input "$long_prompt")")
  [ "$n" = "1" ] || fail "expected the shim path to capture, got $n line(s)"
  grep -qF '"agent":"claude-code"' "$TMP/agent-stamp/.claude/prompt-log.jsonl" \
    || fail "shim row is missing agent=claude-code"
}

writer_stamps_zcode_agent() {
  n=$(run_writer "zcode-stamp" "$(jq -nc --arg p "$long_prompt" '{session_id:"z1", prompt:$p}')" --agent zcode)
  [ "$n" = "1" ] || fail "expected zcode hook-mode capture, got $n line(s)"
  grep -qF '"agent":"zcode"' "$TMP/zcode-stamp/.claude/prompt-log.jsonl" \
    || fail "writer did not stamp agent=zcode"
}

adapter_accepts_message_key() {
  # Client payload drift: prompt text under `message` instead of `prompt`.
  n=$(run_writer "adapter-message" "$(jq -nc --arg p "$long_prompt" '{session_id:"z2", message:$p}')" --agent zcode)
  [ "$n" = "1" ] || fail "expected the message-key adapter to capture, got $n line(s)"
}

wrong_typed_prompt_never_emits_a_row() {
  n=$(run_writer "wrongtype" "$(jq -nc '{session_id:"z3", prompt: 12345}')" --agent zcode)
  [ "$n" = "0" ] || fail "expected a wrong-typed prompt to be dropped, got $n line(s)"
  grep -q "row dropped" "$TMP/wrongtype/.claude/prompt-log-errors.log" \
    || fail "wrong-typed drop left no content-free diagnostic"
}

null_prompt_never_emits_a_row() {
  n=$(run_writer "nullprompt" "$(jq -nc '{session_id:"z4", prompt: null}')" --agent zcode)
  [ "$n" = "0" ] || fail "expected a null prompt to be dropped, got $n line(s)"
}

missing_session_falls_back_to_env() {
  n=$(run_case_env "env-sid" "$(jq -nc --arg p "$long_prompt" '{prompt:$p}')" CLAUDE_SESSION_ID=env-s1)
  [ "$n" = "1" ] || fail "expected the session-id env fallback to capture, got $n line(s)"
  grep -qF '"session_id":"env-s1"' "$TMP/env-sid/.claude/prompt-log.jsonl" \
    || fail "env fallback session id not used"
}

missing_session_never_emits_a_row() {
  n=$(run_writer "nosid" "$(jq -nc --arg p "$long_prompt" '{prompt:$p}')" --agent zcode)
  [ "$n" = "0" ] || fail "expected a row without any session id to be dropped, got $n line(s)"
  grep -q "row dropped" "$TMP/nosid/.claude/prompt-log-errors.log" \
    || fail "missing-session drop left no content-free diagnostic"
}

record_mode_normalizes_timestamp_and_stamps_agent() {
  home="$TMP/record-mode"
  mkdir -p "$home/.claude"
  printf '%s' "$(jq -nc --arg p "$long_prompt" \
    '{timestamp:"2026-08-27T19:16:03.123Z", repo:"rollrepo", branch:"main", machine:"rowmachine", session_id:"cx1", prompt:$p}')" \
    | env HOME="$home" /bin/bash "$WRITER" --agent codex --record \
    || fail "record mode exited non-zero"
  grep -qF '"timestamp":"2026-08-27T19:16:03Z"' "$home/.claude/prompt-log.jsonl" \
    || fail "record mode did not normalize the timestamp to UTC seconds"
  grep -qF '"agent":"codex"' "$home/.claude/prompt-log.jsonl" \
    || fail "record mode did not stamp the agent"
  grep -qF '"machine":"rowmachine"' "$home/.claude/prompt-log.jsonl" \
    || fail "record mode lost the row's machine"
}

record_mode_fills_machine_when_row_lacks_it() {
  home="$TMP/record-machine"
  mkdir -p "$home/.claude"
  printf '%s' "$(jq -nc --arg p "$long_prompt" \
    '{timestamp:"2026-08-27T19:16:04Z", repo:"", branch:"", machine:"", session_id:"cx2", prompt:$p}')" \
    | env HOME="$home" /bin/bash "$WRITER" --agent agy --record \
    || fail "record mode exited non-zero"
  grep -qE '"machine":"[^"]+"' "$home/.claude/prompt-log.jsonl" \
    || fail "record mode left machine empty"
  grep -qF '"agent":"agy"' "$home/.claude/prompt-log.jsonl" \
    || fail "record mode did not stamp agent=agy"
}

collision_is_suppressed_with_a_trace() {
  home="$TMP/collision"
  mkdir -p "$home/.claude"
  row=$(jq -nc --arg p "$long_prompt" \
    '{timestamp:"2026-08-27T19:16:05Z", repo:"r", branch:"", machine:"m", session_id:"cx3", prompt:$p}')
  for i in 1 2; do
    printf '%s' "$row" | env HOME="$home" /bin/bash "$WRITER" --agent codex --record \
      || fail "collision case: writer exited non-zero on attempt $i"
  done
  n=$(wc -l < "$home/.claude/prompt-log.jsonl" | tr -d ' ')
  [ "$n" = "1" ] || fail "expected the same-second collision to be suppressed, got $n line(s)"
  grep -q "id-collision suppressed: cx3:2026-08-27T19:16:05Z" "$home/.claude/prompt-log-errors.log" \
    || fail "suppressed collision left no content-free trace"
}

collision_suppression_holds_at_scale() {
  # Regression: with `jq ... | grep -q` under pipefail, an early-exit match
  # SIGPIPEd jq and a real collision thousands of lines before EOF read as
  # "no collision". The ID set is now captured before matching.
  home="$TMP/collision-scale"
  mkdir -p "$home/.claude"
  for i in $(seq 1 5000); do
    printf '{"timestamp":"2026-08-27T19:16:06Z","repo":"r","branch":"","machine":"m","agent":"codex","session_id":"bulk%s","prompt":"filler row that pads the log volume past the pipe buffer boundary for the collision scan"}\n' "$i" >> "$home/.claude/prompt-log.jsonl"
  done
  printf '%s' "$(jq -nc '{timestamp:"2026-08-27T19:16:06Z", repo:"r", branch:"", machine:"m", session_id:"bulk2500", prompt:"a colliding row whose matching id sits thousands of lines before the end of the log, long enough to clear the capture threshold and reach the suppression scan"}')" \
    | env HOME="$home" /bin/bash "$WRITER" --agent codex --record \
    || fail "collision at scale: writer exited non-zero"
  n=$(wc -l < "$home/.claude/prompt-log.jsonl" | tr -d ' ')
  [ "$n" = "5000" ] || fail "collision at scale: expected suppression, log has $n rows"
  grep -q "id-collision suppressed: bulk2500:" "$home/.claude/prompt-log-errors.log" \
    || fail "collision at scale: no suppression trace"
}

lock_busy_returns_3_and_writes_nothing() {
  home="$TMP/lockbusy"
  mkdir -p "$home/.claude" "$home/.claude/prompt-log.lock"
  date +%s > "$home/.claude/prompt-log.lock/born"
  set +e
  printf '%s' "$(jq -nc --arg p "$long_prompt" \
    '{timestamp:"2026-08-27T19:16:06Z", repo:"r", branch:"", machine:"m", session_id:"cx4", prompt:$p}')" \
    | env HOME="$home" /bin/bash "$WRITER" --agent codex --record
  rc=$?
  set -e
  [ "$rc" = "3" ] || fail "expected exit 3 on a busy append lock, got $rc"
  [ ! -s "$home/.claude/prompt-log.jsonl" ] || fail "a busy lock must write nothing"
}

invalid_agent_is_a_usage_error() {
  home="$TMP/badagent"
  mkdir -p "$home/.claude"
  set +e
  printf '%s' '{"prompt":"x"}' | env HOME="$home" "$WRITER" --agent mystery
  rc=$?
  set -e
  [ "$rc" = "2" ] || fail "expected exit 2 for an invalid --agent, got $rc"
  [ ! -s "$home/.claude/prompt-log.jsonl" ] || fail "invalid agent wrote a row"
}

command -v jq >/dev/null 2>&1 || fail "jq is required to run this harness"

# GH-242: a second interpreter cell is only meaningful when /bin/bash differs from
# `bash` on PATH. When it does, re-exec the whole harness under /bin/bash so both
# interpreters run every case against their own throwaway $HOME.
if [ "${1:-}" != "--cell2" ] \
   && [ "$(readlink -f "$(command -v bash)" 2>/dev/null || command -v bash)" \
     != "$(readlink -f /bin/bash 2>/dev/null || echo /bin/bash)" ]; then
  /bin/bash "$0" --cell2
fi

run_second_cell_note() {
  if [ "${1:-}" != "--cell2" ] \
     && [ "$(readlink -f "$(command -v bash)" 2>/dev/null || command -v bash)" \
       = "$(readlink -f /bin/bash 2>/dev/null || echo /bin/bash)" ]; then
    echo "SKIP: /bin/bash — same interpreter as \`bash\` on this host;"
    echo "      a second run would repeat the first, not widen coverage."
  fi
}

captures_substantive_prompt
skips_short_prompt
boundary_is_inclusive
skips_task_notification
skips_bare_system_notification
strips_injected_blocks_before_measuring
threshold_is_configurable
malformed_input_never_blocks
captured_lines_are_valid_json
stamps_agent_field_via_shim
writer_stamps_zcode_agent
adapter_accepts_message_key
wrong_typed_prompt_never_emits_a_row
null_prompt_never_emits_a_row
missing_session_falls_back_to_env
missing_session_never_emits_a_row
record_mode_normalizes_timestamp_and_stamps_agent
record_mode_fills_machine_when_row_lacks_it
collision_is_suppressed_with_a_trace
collision_suppression_holds_at_scale
lock_busy_returns_3_and_writes_nothing
invalid_agent_is_a_usage_error
run_second_cell_note "$@"
echo "PASS: all capture cases ($([ "${1:-}" = "--cell2" ] && echo /bin/bash || echo bash))"
