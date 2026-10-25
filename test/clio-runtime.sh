#!/bin/bash
# Harness for utils/clio-capture/clio-runtime.sh (GH-364): install, repair, upgrade, adopt and
# uninstall CLIO capture in a throwaway HOME, from a fake Skills Army collection, with launchctl
# stubbed on PATH. Never touches the real HOME or launchd.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d "${TMPDIR:-/tmp}/clio-runtime.XXXXXX") && [ -d "$T" ] || { echo "FAIL: mktemp" >&2; exit 1; }
trap 'rm -rf "${T:?}"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || fail "jq is required to run this harness"

# The collection path has a space, like the real "~/git-pulse-sync/Deployed Skills" (PR #365 review).
export HOME="$T/home" XYZ_SKILLS_ROOT="$T/Deployed Skills"
mkdir -p "$HOME/.claude" "$XYZ_SKILLS_ROOT" "$T/bin"
cp -R "$ROOT/utils/clio-capture" "$XYZ_SKILLS_ROOT/clio-capture"
RT="$XYZ_SKILLS_ROOT/clio-capture/clio-runtime.sh"
H="$HOME/.claude/hooks"; LA="$HOME/Library/LaunchAgents"
# launchctl stub: `list` prints loaded labels; load/unload keep that list and log every call.
cat > "$T/bin/launchctl" <<'EOF'
#!/bin/bash
db="$HOME/.launchctl-loaded"
[ "$1" = load ] && [ -n "${LAUNCHCTL_FAIL:-}" ] && exit 1
case "$1" in
  list) [ -f "$db" ] && while read -r l; do printf -- '-\t0\t%s\n' "$l"; done < "$db"; exit 0 ;;
  load) echo "$*" >> "$HOME/.launchctl-calls"; touch "$db"; l=$(basename "$2" .plist); grep -qx "$l" "$db" || echo "$l" >> "$db" ;;
  unload) echo "$*" >> "$HOME/.launchctl-calls"; touch "$db"; l=$(basename "$2" .plist); grep -vx "$l" "$db" > "$db.tmp"; mv "$db.tmp" "$db" ;;
esac
EOF
chmod +x "$T/bin/launchctl"; export PATH="$T/bin:$PATH"
snapshot() { (cd "$HOME" && find . -path ./.launchctl-calls -prune -o -path ./.launchctl-loaded -prune -o -print0 | sort -z | xargs -0 stat -f '%N %i %m %z' 2>/dev/null); }

# 6. refused from anywhere but <collection>/clio-capture; nothing written
before=$(snapshot)
bash "$ROOT/utils/clio-capture/clio-runtime.sh" install --apply >/dev/null 2>&1; rc=$?
[ "$rc" = 2 ] || fail "repo-path run: expected exit 2, got $rc"
[ "$(snapshot)" = "$before" ] || fail "repo-path run wrote files"

# 1. fresh install: preview writes nothing; --apply converges; capture works; no ZCode side effects
before=$(snapshot)
bash "$RT" install > "$T/out" || fail "install preview failed"
[ "$(snapshot)" = "$before" ] || fail "install preview wrote files"
bash "$RT" status >/dev/null && fail "status on an empty HOME should exit 1"
bash "$RT" install --apply > "$T/out" || fail "install --apply failed: $(cat "$T/out")"
bash "$RT" status > "$T/status" || fail "status after install not clean: $(cat "$T/status")"
for f in clio-store.py prompt-log-to-md.sh clio-codex-tail.sh clio-agy-tail.sh; do
  [ "$(readlink "$H/$f")" = "$(cd "$XYZ_SKILLS_ROOT/clio-capture" && pwd -P)/$f" ] || fail "$f is not a link into the collection"; done
[ -f "$H/clio-capture.sh" ] && [ ! -L "$H/clio-capture.sh" ] || fail "writer not generated"
jq -e '.hooks.UserPromptSubmit[0].hooks[0].command == "$HOME/.claude/hooks/log-prompt.sh"' "$HOME/.claude/settings.json" >/dev/null \
  || fail "Claude registration missing"
[ ! -e "$HOME/.zcode" ] || fail "install created ~/.zcode without one present"
if [ "$(uname -s)" = Darwin ]; then
  for t in codex agy; do
    [ -f "$LA/com.claude.clio-$t-tail.plist" ] || fail "$t tailer plist not created"
    grep -qx "com.claude.clio-$t-tail" "$HOME/.launchctl-loaded" || fail "$t tailer not loaded"
  done
  [ ! -e "$LA/com.claude.prompt-log-to-md.plist" ] || fail "installer created the exporter plist"
fi
echo '{"prompt":"a substantive prompt captured through the installed shim","session_id":"rt-1"}' \
  | env CLAUDE_PROJECT_DIR="$ROOT" "$H/log-prompt.sh"
[ "$(jq -r .session_id "$HOME/.claude/prompt-log.jsonl" 2>/dev/null | tail -1)" = rt-1 ] || fail "installed shim did not capture"

# 7. rerun on a converged HOME: nothing to do, nothing changes
before=$(snapshot)
bash "$RT" install --apply | grep -q "nothing to do" || fail "converged rerun did not report nothing to do"
[ "$(snapshot)" = "$before" ] || fail "converged rerun changed files"

# 2. a deleted link: status names it; repair restores only it
rm "$H/clio-agy-tail.sh"
{ bash "$RT" status || true; } | grep -q "clio-agy-tail.sh *missing" || fail "status did not report the missing link"
keep=$(stat -f '%i %m' "$H/clio-capture.sh" "$H/clio-store.py" "$HOME/.claude/settings.json")
bash "$RT" repair --apply >/dev/null || fail "repair failed"
[ -L "$H/clio-agy-tail.sh" ] || fail "repair did not restore the link"
[ "$(stat -f '%i %m' "$H/clio-capture.sh" "$H/clio-store.py" "$HOME/.claude/settings.json")" = "$keep" ] || fail "repair touched other files"

# 3. the deployed writer heredoc changes: status says stale; upgrade regenerates it
sed -i '' 's/^# CLIO shared capture writer (GH-139)/# CLIO shared capture writer (GH-139, upgraded)/' "$XYZ_SKILLS_ROOT/clio-capture/INSTALL.md"
{ bash "$RT" status || true; } | grep -q "clio-capture.sh *stale" || fail "status did not report a stale writer"
bash "$RT" upgrade --apply >/dev/null || fail "upgrade failed"
grep -q "GH-139, upgraded" "$H/clio-capture.sh" || fail "upgrade did not regenerate the writer"
bash "$RT" status >/dev/null || fail "status after upgrade not clean"

# 4 + 5. a fresh HOME with a hand install: preview refuses to touch it; --apply backs it up; uninstall restores it
export HOME="$T/home2"; H="$HOME/.claude/hooks"; LA="$HOME/Library/LaunchAgents"; mkdir -p "$H" "$LA"
printf '#!/bin/bash\n# hand-made\n' > "$H/log-prompt.sh"; chmod +x "$H/log-prompt.sh"
echo '{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"$HOME/.claude/hooks/log-prompt.sh"}]},{"hooks":[{"type":"command","command":"/other/hook.sh"}]}]}}' > "$HOME/.claude/settings.json"
printf 'pre-existing plist\n' > "$LA/com.claude.clio-codex-tail.plist"
before=$(snapshot)
bash "$RT" install > "$T/out" || fail "adopt preview failed"
grep -q "back up and replace: .*log-prompt.sh" "$T/out" || fail "preview did not name the hand-made file"
[ "$(snapshot)" = "$before" ] || fail "adopt preview wrote files"
bash "$RT" install --apply >/dev/null || fail "adopt --apply failed"
grep -q "hand-made" "$H/log-prompt.sh" && fail "hand-made file was not replaced"
bk=$(jq -r --arg p "$H/log-prompt.sh" '.backups[$p]' "$HOME/.claude/clio-runtime.json")
grep -q "hand-made" "$bk" || fail "hand-made file was not backed up"
[ "$(cat "$LA/com.claude.clio-codex-tail.plist")" = "pre-existing plist" ] || fail "existing tailer plist was rewritten"
bash "$RT" uninstall --apply >/dev/null || fail "uninstall failed"
grep -q "hand-made" "$H/log-prompt.sh" || fail "uninstall did not restore the hand-made file"
for f in clio-store.py prompt-log-to-md.sh clio-codex-tail.sh clio-agy-tail.sh clio-capture.sh; do
  [ ! -e "$H/$f" ] && [ ! -L "$H/$f" ] || fail "uninstall left $f"; done
jq -e '[.hooks.UserPromptSubmit[].hooks[].command] == ["$HOME/.claude/hooks/log-prompt.sh", "/other/hook.sh"]' "$HOME/.claude/settings.json" >/dev/null \
  || fail "uninstall changed registrations it did not add"
[ "$(cat "$LA/com.claude.clio-codex-tail.plist")" = "pre-existing plist" ] || fail "uninstall removed a plist it did not create"
if [ "$(uname -s)" = Darwin ]; then [ ! -e "$LA/com.claude.clio-agy-tail.plist" ] || fail "uninstall left the plist it created"; fi
[ ! -e "$HOME/.claude/clio-runtime.json" ] || fail "uninstall left the receipt"

# 8. drift-safe uninstall: a hook edited after install survives, with its backup; the rest is removed
export HOME="$T/home3"; H="$HOME/.claude/hooks"; mkdir -p "$H"
printf '#!/bin/bash\n# hand-made\n' > "$H/log-prompt.sh"; chmod +x "$H/log-prompt.sh"
bash "$RT" install --apply >/dev/null || fail "case 8 install failed"
echo '# local edit after install' >> "$H/log-prompt.sh"
bash "$RT" uninstall --apply > "$T/out"; rc=$?
[ "$rc" = 1 ] || fail "uninstall with a drifted hook: expected exit 1, got $rc"
grep -q "drifted (left in place): $H/log-prompt.sh" "$T/out" || fail "drifted hook not reported"
grep -q "local edit after install" "$H/log-prompt.sh" || fail "uninstall overwrote a post-install edit"
bk=$(jq -r --arg p "$H/log-prompt.sh" '.backups[$p]' "$HOME/.claude/clio-runtime.json")
grep -q "hand-made" "$bk" || fail "drifted hook's backup was not kept"
[ ! -e "$H/clio-capture.sh" ] && [ ! -L "$H/clio-store.py" ] || fail "unchanged items were not removed"

# 9. look-alike registrations are not mistaken for the managed ones (final QA R1)
export HOME="$T/home4"; mkdir -p "$HOME/.claude" "$HOME/.zcode/cli"
echo '{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"/foreign/hooks/log-prompt.sh"}]}]}}' > "$HOME/.claude/settings.json"
echo '{"hooks":{"enabled":true,"events":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"/foreign/clio-capture.sh --agent other"}]}]}}}' > "$HOME/.zcode/cli/config.json"
{ bash "$RT" status || true; } | grep -q "claude-registration *missing" || fail "look-alike Claude command counted as registered"
{ bash "$RT" status || true; } | grep -q "zcode-registration *missing" || fail "look-alike ZCode command counted as registered"
bash "$RT" install --apply >/dev/null || fail "case 9 install failed"
jq -e '[.hooks.UserPromptSubmit[].hooks[].command] == ["/foreign/hooks/log-prompt.sh", "$HOME/.claude/hooks/log-prompt.sh"]' "$HOME/.claude/settings.json" >/dev/null \
  || fail "managed Claude registration not added beside the look-alike"
jq -e '.added_registrations == ["claude", "zcode"]' "$HOME/.claude/clio-runtime.json" >/dev/null || fail "registrations not recorded in the receipt"
jq -e '[.hooks.events.UserPromptSubmit[].hooks[].command] == ["/foreign/clio-capture.sh --agent other", "$HOME/.claude/hooks/clio-capture.sh --agent zcode"]' "$HOME/.zcode/cli/config.json" >/dev/null \
  || fail "managed ZCode registration not added beside the look-alike"
bash "$RT" uninstall --apply >/dev/null || fail "case 9 uninstall failed"
jq -e '[.hooks.UserPromptSubmit[].hooks[].command] == ["/foreign/hooks/log-prompt.sh"]' "$HOME/.claude/settings.json" >/dev/null \
  || fail "uninstall removed or kept the wrong Claude registration"
jq -e '[.hooks.events.UserPromptSubmit[].hooks[].command] == ["/foreign/clio-capture.sh --agent other"]' "$HOME/.zcode/cli/config.json" >/dev/null \
  || fail "uninstall removed or kept the wrong ZCode registration"

# 10. ~/.zcode exists but has no config yet: the first install creates it with the managed hook
export HOME="$T/home5"; mkdir -p "$HOME/.claude" "$HOME/.zcode"
bash "$RT" install --apply >/dev/null || fail "case 10 install failed"
jq -e '.hooks.enabled == true and ([.hooks.events.UserPromptSubmit[].hooks[].command] == ["$HOME/.claude/hooks/clio-capture.sh --agent zcode"])' \
  "$HOME/.zcode/cli/config.json" >/dev/null || fail "ZCode config not created with the managed hook"

# 11. a pre-existing hook that already matches is not claimed, so uninstall leaves it (and capture) working
export HOME="$T/home6"; H="$HOME/.claude/hooks"; mkdir -p "$H"
awk -v q="'" '$0 == "cat > ~/.claude/hooks/log-prompt.sh << " q "EOF" q {f=1; next} f && /^EOF$/ {exit} f' \
  "$XYZ_SKILLS_ROOT/clio-capture/INSTALL.md" > "$H/log-prompt.sh"; chmod 755 "$H/log-prompt.sh"
echo '{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"$HOME/.claude/hooks/log-prompt.sh"}]}]}}' > "$HOME/.claude/settings.json"
bash "$RT" install --apply >/dev/null || fail "case 11 install failed"
jq -e --arg p "$H/log-prompt.sh" '.owned | has($p) | not' "$HOME/.claude/clio-runtime.json" >/dev/null || fail "matching pre-existing hook was claimed"
bash "$RT" uninstall --apply >/dev/null || fail "case 11 uninstall failed"
[ -f "$H/log-prompt.sh" ] || fail "uninstall deleted a pre-existing hook it never installed"
claude_cmds=$(jq -c '[.hooks.UserPromptSubmit[].hooks[].command]' "$HOME/.claude/settings.json")
[ "$claude_cmds" = '["$HOME/.claude/hooks/log-prompt.sh"]' ] || fail "pre-existing registration changed: $claude_cmds"

# 12. invalid settings.json: install stops (exit 2) with every applied change already in the receipt
export HOME="$T/home7"; H="$HOME/.claude/hooks"; mkdir -p "$H"
printf '#!/bin/bash\n# hand-made\n' > "$H/clio-capture.sh"; echo '{not json' > "$HOME/.claude/settings.json"
bash "$RT" install --apply >/dev/null 2>&1; rc=$?
[ "$rc" = 2 ] || fail "invalid settings.json: expected exit 2, got $rc"
[ "$(cat "$HOME/.claude/settings.json")" = '{not json' ] || fail "invalid settings.json was rewritten"
jq -e --arg p "$H/clio-capture.sh" '(.backups | has($p)) and (.owned | has($p)) and (.added_registrations == [])' \
  "$HOME/.claude/clio-runtime.json" >/dev/null || fail "receipt lost the backup/ownership after a failed config write"

if [ "$(uname -s)" = Darwin ]; then
  # 13. launchctl load fails: exit 1, receipt still records the plists it created
  export HOME="$T/home8"; mkdir -p "$HOME/.claude"
  LAUNCHCTL_FAIL=1 bash "$RT" install --apply >/dev/null 2>&1; rc=$?
  [ "$rc" = 1 ] || fail "failed launchctl load: expected exit 1, got $rc"
  jq -e '.created_plists | length == 2' "$HOME/.claude/clio-runtime.json" >/dev/null || fail "receipt lost created plists after a load failure"
  # 14. a created plist edited after install is left in place on uninstall
  export HOME="$T/home9"; LA="$HOME/Library/LaunchAgents"; mkdir -p "$HOME/.claude"
  bash "$RT" install --apply >/dev/null || fail "case 14 install failed"
  echo '<!-- local edit -->' >> "$LA/com.claude.clio-agy-tail.plist"
  bash "$RT" uninstall --apply > "$T/out"; rc=$?
  [ "$rc" = 1 ] && grep -q "drifted (left in place): $LA/com.claude.clio-agy-tail.plist" "$T/out" || fail "edited plist not reported as drifted"
  grep -q "local edit" "$LA/com.claude.clio-agy-tail.plist" || fail "uninstall removed an edited plist"
  [ ! -e "$LA/com.claude.clio-codex-tail.plist" ] || fail "unchanged created plist not removed"
fi

# 15. two adoptions within the same second keep the first original (unique backup folder per run)
export HOME="$T/home10"; H="$HOME/.claude/hooks"; mkdir -p "$H"
# Pin the backup-folder timestamp so both runs fall in "the same second" deterministically.
mkdir -p "$T/samesec"; printf '#!/bin/bash\ncase "$*" in *%%Y%%m%%dT%%H%%M%%SZ*) echo 20260101T000000Z ;; *) exec /bin/date "$@" ;; esac\n' > "$T/samesec/date"
chmod +x "$T/samesec/date"; PATH="$T/samesec:$PATH"
printf '#!/bin/bash\n# original A\n' > "$H/clio-agy-tail.sh"
bash "$RT" install --apply >/dev/null || fail "case 15 first install failed"
rm "$H/clio-agy-tail.sh"; printf '#!/bin/bash\n# later B\n' > "$H/clio-agy-tail.sh"
bash "$RT" install --apply >/dev/null || fail "case 15 second install failed"
bk=$(jq -r --arg p "$H/clio-agy-tail.sh" '.backups[$p]' "$HOME/.claude/clio-runtime.json")
grep -q "original A" "$bk" || fail "the first original backup was overwritten"
[ "$(grep -rl 'later B' "$HOME/.claude/clio-runtime-backups" | wc -l | tr -d ' ')" = 1 ] || fail "the second foreign file was not kept"
PATH="${PATH#"$T/samesec:"}"

echo "PASS: clio-runtime"
