#!/bin/bash
# GH-45 shakedown matrix for the rebalance skill's collector locator.
#
# The bug: SKILL.md documented `bash "<skill_dir>/collect.sh"` — a placeholder the
# reader had to invent a value for. It returned NOT-FOUND / exit 127 in all eight
# shakedown scenarios while an anchored control passed all eight.
#
# This harness extracts the locator FROM SKILL.md by MARKER (not line numbers — the
# block gets edited), exactly like test/clio-capture.sh extracts the CLIO hook from
# INSTALL.md. That is load-bearing: it means this suite tests the command a reader
# actually copies, so the doc and the test cannot drift apart.
#
# Scenarios: control CWD, foreign CWD, nested CWD, spaces in install path,
# project install, user install, symlinked install, stripped execute bit.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd -P)
SKILL_DOC="$HERE/SKILL.md"
REAL_COLLECT="$HERE/collect.sh"

# Resolve the temp root to its REAL path up front. On macOS $TMPDIR lives under
# /var/folders/…, and /var is a symlink to /private/var — so the locator (which ends in
# `pwd -P`) and the collector both report /private/var while a raw $TMP string says /var.
# Resolving once here keeps every path comparison below comparing like with like.
TMP=$(mktemp -d "${TMPDIR:-/tmp}/gh45-locator.XXXXXX")
TMP=$(cd "$TMP" && pwd -P)
trap 'rm -rf "$TMP"' EXIT

fails=0
pass() { echo "  ok   — $*"; }
fail() { echo "  FAIL — $*" >&2; fails=$((fails + 1)); }

# --- extract the documented locator ------------------------------------------
extract_block() {
  awk -v s="# >>> $1 >>>" -v e="# <<< $1 <<<" \
    '$0==s{f=1;next} f&&$0==e{exit} f' "$SKILL_DOC"
}

LOCATOR="$TMP/locator.sh"
extract_block rebalance-skill-locator > "$LOCATOR"
if [ ! -s "$LOCATOR" ]; then
  echo "FAIL: could not extract the rebalance-skill-locator block from $SKILL_DOC" >&2
  echo "      (the marker comments must survive verbatim — this suite tests the documented path)" >&2
  exit 1
fi
grep -q 'rebalance_skill_dir()' "$LOCATOR" \
  || { echo "FAIL: extracted block does not define rebalance_skill_dir()" >&2; exit 1; }

# The locator is only half the documented contract — the reader also copies the
# invocation that consumes it. Extract that too, so it cannot drift or regress
# while this suite stays green.
INVOCATION="$TMP/invocation.sh"
extract_block rebalance-collect-invocation > "$INVOCATION"
if [ ! -s "$INVOCATION" ]; then
  echo "FAIL: could not extract the rebalance-collect-invocation block from $SKILL_DOC" >&2
  exit 1
fi
grep -q 'rebalance_skill_dir' "$INVOCATION" \
  || { echo "FAIL: documented invocation no longer calls rebalance_skill_dir" >&2; exit 1; }
grep -q 'collect.sh' "$INVOCATION" \
  || { echo "FAIL: documented invocation no longer runs collect.sh" >&2; exit 1; }

# The documented command as a reader actually assembles it: locator, then invocation.
DOCUMENTED="$TMP/documented.sh"
cat "$LOCATOR" "$INVOCATION" > "$DOCUMENTED"

# --- fixture builders ---------------------------------------------------------
# Build a fake install at $1 with a REAL collect.sh, deliberately mode 644 so every
# scenario also proves the stripped-execute-bit case (we always invoke via `bash`).
make_install() {
  mkdir -p "$1"
  printf '# fixture SKILL.md\n' > "$1/SKILL.md"
  cp "$REAL_COLLECT" "$1/collect.sh"
  chmod 644 "$1/SKILL.md" "$1/collect.sh"
}

# Resolve the locator from a given CWD and HOME. Echoes the resolved path.
# Usage: resolve <cwd> <home>
resolve() {
  ( cd "$1" 2>/dev/null || exit 1
    HOME="$2"
    # shellcheck disable=SC1090
    . "$LOCATOR"
    rebalance_skill_dir ) 2>/dev/null
}

# A scenario passes when the locator resolves to the expected real path AND the
# collector it points at actually runs through `bash` despite mode 644.
check() {
  desc=$1; cwd=$2; home=$3; want=$4
  got=$(resolve "$cwd" "$home")
  if [ -z "$got" ]; then
    fail "$desc: locator returned nothing (NOT-FOUND — the GH-45 regression)"
    return
  fi
  want_real=$(cd "$want" && pwd -P)
  if [ "$got" != "$want_real" ]; then
    fail "$desc: resolved '$got', expected '$want_real'"
    return
  fi
  if ! bash "$got/collect.sh" "$TMP/empty-scan-root" >/dev/null 2>&1; then
    fail "$desc: resolved correctly but 'bash \$dir/collect.sh' failed (exec-bit/invocation)"
    return
  fi
  pass "$desc"
}

# --- fixtures -----------------------------------------------------------------
# Project install inside a repo, plus a deep nested dir to run from.
PROJ="$TMP/proj"
make_install "$PROJ/.claude/skills/rebalance"
mkdir -p "$PROJ/src/rebalance/ingest/deep"

# User install under a throwaway HOME.
USER_HOME="$TMP/home"
make_install "$USER_HOME/.claude/skills/rebalance"

# Install path containing spaces (both the repo dir and a nested CWD).
SPACED="$TMP/GH Repos/my project"
make_install "$SPACED/.claude/skills/rebalance"
mkdir -p "$SPACED/nested dir/deeper"

# Symlinked install: real skill lives elsewhere, project points at it.
REALSKILL="$TMP/real skills/rebalance"
make_install "$REALSKILL"
SYMPROJ="$TMP/symproj"
mkdir -p "$SYMPROJ/.claude/skills"
ln -s "$REALSKILL" "$SYMPROJ/.claude/skills/rebalance"

# A CWD with no install anywhere above it, and an empty HOME — the fail-loudly case.
BARE="$TMP/bare/deep/deeper"
mkdir -p "$BARE"
EMPTY_HOME="$TMP/empty-home"
mkdir -p "$EMPTY_HOME"

echo "GH-45 locator shakedown matrix"

# --- the eight scenarios ------------------------------------------------------
check "control CWD (at the project root)" \
  "$PROJ" "$EMPTY_HOME" "$PROJ/.claude/skills/rebalance"

check "nested CWD (deep inside the project)" \
  "$PROJ/src/rebalance/ingest/deep" "$EMPTY_HOME" "$PROJ/.claude/skills/rebalance"

check "foreign CWD (no project install; falls back to user install)" \
  "$BARE" "$USER_HOME" "$USER_HOME/.claude/skills/rebalance"

check "user install (HOME copy, CWD elsewhere)" \
  "$TMP" "$USER_HOME" "$USER_HOME/.claude/skills/rebalance"

check "project install wins over user install" \
  "$PROJ" "$USER_HOME" "$PROJ/.claude/skills/rebalance"

check "spaces in install path" \
  "$SPACED" "$EMPTY_HOME" "$SPACED/.claude/skills/rebalance"

check "spaces in install path, nested CWD" \
  "$SPACED/nested dir/deeper" "$EMPTY_HOME" "$SPACED/.claude/skills/rebalance"

check "symlinked install (resolves to the real path)" \
  "$SYMPROJ" "$EMPTY_HOME" "$REALSKILL"

# --- stripped execute bit, called out explicitly ------------------------------
# Every check() above already runs a mode-644 collect.sh through `bash`; assert the
# mode really is stripped so this scenario can never silently become a no-op.
mode=$(ls -l "$PROJ/.claude/skills/rebalance/collect.sh" | cut -c1-10)
case "$mode" in
  *x*) fail "stripped execute bit: fixture collect.sh is executable ($mode) — scenario is a no-op" ;;
  *)   pass "stripped execute bit (fixtures are $mode; invoked via bash throughout)" ;;
esac

# --- the FULL documented command, end to end ----------------------------------
# Everything above tests the locator in isolation. These run the locator and the
# documented invocation together, exactly as a reader pastes them, so a regression
# in either half is caught.
out=$( ( cd "$PROJ" && HOME="$EMPTY_HOME"; bash "$DOCUMENTED" ) 2>/dev/null )
rc=$?
if [ "$rc" != "0" ]; then
  fail "documented command (locator + invocation) exited $rc from a project install"
elif ! printf '%s' "$out" | grep -q '.'; then
  fail "documented command produced no collector output"
else
  pass "documented command runs end to end (project install)"
fi

out=$( ( cd "$SPACED/nested dir/deeper" && HOME="$USER_HOME"; bash "$DOCUMENTED" ) 2>/dev/null )
[ $? = 0 ] && [ -n "$out" ] \
  && pass "documented command runs end to end (spaces + nested CWD)" \
  || fail "documented command failed from a spaced, nested CWD"

# Interactive-shell safety: the failure path must NOT terminate the caller's shell.
# `|| exit 1` would; the documented `else false` must not. Simulate an interactive
# paste by sourcing the command into a shell that then has to keep running.
probe=$( ( cd "$BARE" && HOME="$EMPTY_HOME"
           bash -c '. "$1"; echo "SHELL-SURVIVED:$?"' _ "$DOCUMENTED" ) 2>/dev/null )
case "$probe" in
  SHELL-SURVIVED:0)
    fail "failure path returned 0 — the non-zero status was lost" ;;
  SHELL-SURVIVED:*)
    pass "failure path is non-zero (${probe#SHELL-SURVIVED:}) and the shell survived" ;;
  *)
    fail "failure path killed the calling shell (no SHELL-SURVIVED marker; got '$probe')" ;;
esac

# --- fail-loudly contract -----------------------------------------------------
err=$( ( cd "$BARE" && HOME="$EMPTY_HOME"; . "$LOCATOR"; rebalance_skill_dir ) 2>&1 >/dev/null )
rc=$(  ( cd "$BARE" && HOME="$EMPTY_HOME"; . "$LOCATOR"; rebalance_skill_dir >/dev/null 2>&1 ); echo $? )
if [ "$rc" = "0" ]; then
  fail "no install anywhere: expected non-zero exit, got 0"
elif ! printf '%s' "$err" | grep -q 'could not locate the rebalance skill'; then
  fail "no install anywhere: exited $rc but printed no actionable message"
else
  pass "no install anywhere: exits $rc and explains where it looked"
fi

# Override honored, and a bad override fails loudly rather than falling through.
got=$( ( cd "$BARE" && HOME="$EMPTY_HOME" REBALANCE_SKILL_DIR="$REALSKILL"; \
         . "$LOCATOR"; rebalance_skill_dir ) 2>/dev/null )
[ "$got" = "$(cd "$REALSKILL" && pwd -P)" ] \
  && pass "REBALANCE_SKILL_DIR override honored" \
  || fail "REBALANCE_SKILL_DIR override: resolved '$got', expected '$REALSKILL'"

rc=$( ( cd "$PROJ" && HOME="$USER_HOME" REBALANCE_SKILL_DIR="$TMP/nope"; \
        . "$LOCATOR"; rebalance_skill_dir >/dev/null 2>&1 ); echo $? )
[ "$rc" != "0" ] \
  && pass "bad REBALANCE_SKILL_DIR fails loudly instead of falling through" \
  || fail "bad REBALANCE_SKILL_DIR silently fell back (exit 0)"

# --- collector contract -------------------------------------------------------
# GH-45 acceptance: keep the collector read-only and preserve positional scan roots.
scan="$TMP/scanroot"
mkdir -p "$scan/repo-a"
( cd "$scan/repo-a" && git init -q . 2>/dev/null \
    && git -c user.email=t@t -c user.name=t -c commit.gpgsign=false commit -q --allow-empty -m init 2>/dev/null )
before=$(find "$scan" | sort)
out=$(bash "$PROJ/.claude/skills/rebalance/collect.sh" "$scan" 2>/dev/null)
after=$(find "$scan" | sort)
[ "$before" = "$after" ] \
  && pass "collector left the scan root byte-identical (read-only)" \
  || fail "collector mutated the scan root"
printf '%s' "$out" | grep -q "$scan/repo-a" \
  && pass "positional scan-root override still honored" \
  || fail "positional scan-root override was ignored"

echo
if [ "$fails" -eq 0 ]; then
  echo "PASS — all GH-45 locator shakedown checks green"
  exit 0
fi
echo "FAIL — $fails check(s) failed" >&2
exit 1
