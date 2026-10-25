#!/usr/bin/env bash
# clio-runtime.sh — install, repair, upgrade, check or remove CLIO prompt capture on this device (GH-364).
#
#   clio-runtime.sh [status]                       read-only report; exit 1 when install would change something
#   clio-runtime.sh install|repair|upgrade [--apply]   converge to the deployed copy (one idempotent operation)
#   clio-runtime.sh uninstall [--apply]            reverse only what this tool's receipt says it did
#
# Runs only from the Skills Army deployed copy, ${XYZ_SKILLS_ROOT:-~/git-pulse-sync/Deployed Skills}/clio-capture.
# The helpers in ~/.claude/hooks become symlinks into that copy, so a Pulse pull upgrades them. The writer
# and Claude shim are generated from INSTALL.md (the same extraction the tests use) and flagged when stale.
# Never touches app skill links, the SQLite store or its config, or the exporter's launchd job.
# Exit: 0 ok / nothing to do · 1 status found changes to make · 2 refused or usage error.
set -euo pipefail

die() { echo "clio-runtime: $*" >&2; exit 2; }
SRC=$(cd "$(dirname "$0")" && pwd -P)
COL="${XYZ_SKILLS_ROOT:-$HOME/git-pulse-sync/Deployed Skills}"
DEPLOYED=$(cd "$COL/clio-capture" 2>/dev/null && pwd -P || true)
[ -n "$DEPLOYED" ] && [ "$SRC" = "$DEPLOYED" ] \
  || die "run me from the Skills Army deployed copy ($COL/clio-capture), not from $SRC"
command -v jq >/dev/null 2>&1 || die "jq is required (brew install jq)"

CMD="${1:-status}"; APPLY=0
case "${2:-}" in --apply) APPLY=1 ;; "") ;; *) die "unknown option: $2" ;; esac
case "$CMD" in status|install|repair|upgrade|uninstall) ;; *) die "usage: clio-runtime.sh [status|install|repair|upgrade|uninstall] [--apply]" ;; esac

H="$HOME/.claude/hooks"; RECEIPT="$HOME/.claude/clio-runtime.json"; LA="$HOME/Library/LaunchAgents"
SETTINGS="$HOME/.claude/settings.json"; ZCONFIG="$HOME/.zcode/cli/config.json"
LINKS="clio-store.py prompt-log-to-md.sh clio-codex-tail.sh clio-agy-tail.sh"
GENERATED="clio-capture.sh log-prompt.sh"
TAILERS="codex agy"
DARWIN=0; [ "$(uname -s)" = Darwin ] && DARWIN=1

sha() { shasum -a 256 | cut -c1-64; }
extract() { # $1 = hook name; the INSTALL.md heredoc, by the same marker test/clio-capture.sh uses
  awk -v n="$1" -v q="'" '$0 == "cat > ~/.claude/hooks/" n " << " q "EOF" q {f=1; next} f && /^EOF$/ {exit} f' "$SRC/INSTALL.md"
}
for g in $GENERATED; do [ -n "$(extract "$g")" ] || die "INSTALL.md has no $g heredoc"; done
digest=$(cat "$SRC/INSTALL.md" $(for f in $LINKS; do echo "$SRC/$f"; done) | sha)
hq_commit=$(jq -r '.skills["clio-capture"].commit // empty' "$COL/.deploy-skills.json" 2>/dev/null || true)
rget() { [ -f "$RECEIPT" ] && jq -r "$1 // empty" "$RECEIPT" 2>/dev/null || true; }

item_state() { # $1 = hook name -> ok | missing | stale | wrong-target | foreign
  local p="$H/$1"
  case " $LINKS " in *" $1 "*)
    if [ -L "$p" ] && [ "$(readlink "$p")" = "$SRC/$1" ]; then echo ok
    elif [ -L "$p" ] && [ "$(rget ".owned[\"$p\"]")" = link ]; then echo wrong-target
    elif [ -e "$p" ] || [ -L "$p" ]; then echo foreign; else echo missing; fi; return ;;
  esac
  if [ -f "$p" ] && [ ! -L "$p" ]; then
    local have; have=$(sha < "$p")
    if [ "$have" = "$(extract "$1" | sha)" ]; then echo ok
    elif [ "$have" = "$(rget ".generated[\"$p\"]")" ]; then echo stale
    else echo foreign; fi
  elif [ -e "$p" ] || [ -L "$p" ]; then echo foreign; else echo missing; fi
}
claude_reg() { grep -q 'hooks/log-prompt.sh' "$SETTINGS" 2>/dev/null; }
zcode_wanted() { [ -d "$HOME/.zcode" ]; }
zcode_reg() { grep -q 'clio-capture.sh' "$ZCONFIG" 2>/dev/null; }
plist_of() { echo "$LA/com.claude.clio-$1-tail.plist"; }
loaded() { launchctl list 2>/dev/null | awk '{print $3}' | grep -qx "$1"; }

# ---- status / plan ---------------------------------------------------------------------------
todo=()
for f in $LINKS $GENERATED; do st=$(item_state "$f"); [ "$st" = ok ] || todo+=("$f:$st"); done
claude_reg || todo+=("claude-registration:missing")
if zcode_wanted && ! zcode_reg; then todo+=("zcode-registration:missing"); fi
if [ "$DARWIN" = 1 ]; then
  for t in $TAILERS; do
    if [ ! -f "$(plist_of "$t")" ]; then todo+=("$t-tailer-plist:missing")
    elif ! loaded "com.claude.clio-$t-tail"; then todo+=("$t-tailer-plist:not-loaded"); fi
  done
fi
[ "$(rget .digest)" = "$digest" ] || todo+=("receipt:$([ -f "$RECEIPT" ] && echo outdated || echo missing)")

if [ "$CMD" = status ]; then
  echo "source: $SRC${hq_commit:+ (HQ ${hq_commit:0:12})} digest ${digest:0:12}"
  for f in $LINKS $GENERATED; do printf '  %-20s %s\n' "$f" "$(item_state "$f")"; done
  printf '  %-20s %s\n' claude-registration "$(claude_reg && echo ok || echo missing)"
  printf '  %-20s %s\n' zcode-registration "$(zcode_wanted || { echo 'n/a (no ~/.zcode)'; exit 0; }; zcode_reg && echo ok || echo missing)"
  if [ "$DARWIN" = 1 ]; then
    for t in $TAILERS; do l="com.claude.clio-$t-tail"
      printf '  %-20s %s\n' "$t-tailer-plist" "$([ -f "$(plist_of "$t")" ] && { loaded "$l" && echo loaded || echo not-loaded; } || echo missing)"; done
    printf '  %-20s %s\n' exporter-plist "$([ -f "$LA/com.claude.prompt-log-to-md.plist" ] && echo "present (not managed)" || echo "absent (not managed; see INSTALL.md Auto-sync)")"
  fi
  printf '  %-20s %s\n' receipt "$( [ -f "$RECEIPT" ] && { [ "$(rget .digest)" = "$digest" ] && echo current || echo outdated; } || echo missing)"
  [ ${#todo[@]} -eq 0 ] && { echo "nothing to do"; exit 0; }
  echo "run: $SRC/clio-runtime.sh install --apply"; exit 1
fi

# ---- uninstall -------------------------------------------------------------------------------
if [ "$CMD" = uninstall ]; then
  [ -f "$RECEIPT" ] || { echo "nothing to uninstall: no receipt at $RECEIPT"; exit 0; }
  owned=$(jq -r '.owned | keys[]' "$RECEIPT")
  regs=$(jq -r '.added_registrations[]?' "$RECEIPT"); plists=$(jq -r '.created_plists[]?' "$RECEIPT")
  echo "uninstall would: remove owned hooks (restoring backups), remove registrations [${regs//$'\n'/ }], remove plists [${plists//$'\n'/ }], delete the receipt"
  [ "$APPLY" = 1 ] || { echo "preview only; add --apply"; exit 0; }
  # Remove (and restore the backup of) only what still matches the receipt; keep anything changed since.
  drifted=()
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$(rget ".owned[\"$p\"]")" in
      link) [ -L "$p" ] && [ "$(readlink "$p")" = "$SRC/$(basename "$p")" ] && match=1 || match=0 ;;
      *) [ -f "$p" ] && [ ! -L "$p" ] && [ "$(sha < "$p")" = "$(rget ".generated[\"$p\"]")" ] && match=1 || match=0 ;;
    esac
    if [ ! -e "$p" ] && [ ! -L "$p" ]; then match=1; fi   # already gone: nothing of the user's to lose
    if [ "$match" = 0 ]; then drifted+=("$p"); echo "  drifted (left in place): $p"; continue; fi
    rm -f "$p"; b=$(rget ".backups[\"$p\"]")
    if [ -n "$b" ] && { [ -e "$b" ] || [ -L "$b" ]; }; then mv "$b" "$p"; fi
  done <<< "$owned"
  if grep -qx claude <<< "$regs"; then
    jq 'if (.hooks // null) == null then . else (.hooks.UserPromptSubmit //= []) | .hooks.UserPromptSubmit = (.hooks.UserPromptSubmit
          | map(.hooks = ((.hooks // []) | map(select(((.command // "") == "$HOME/.claude/hooks/log-prompt.sh") | not))))
          | map(select((.hooks // []) | length > 0)))
        | if (.hooks.UserPromptSubmit // []) == [] then del(.hooks.UserPromptSubmit) else . end end' \
      "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
  fi
  if grep -qx zcode <<< "$regs" && [ -f "$ZCONFIG" ]; then
    jq 'if (.hooks.events.UserPromptSubmit // null) == null then . else .hooks.events.UserPromptSubmit = (.hooks.events.UserPromptSubmit
          | map(.hooks = ((.hooks // []) | map(select(((.command // "") | contains("clio-capture.sh")) | not))))
          | map(select((.hooks // []) | length > 0)))
        | if .hooks.events.UserPromptSubmit == [] then del(.hooks.events.UserPromptSubmit) else . end end' \
      "$ZCONFIG" > "$ZCONFIG.tmp" && mv "$ZCONFIG.tmp" "$ZCONFIG"
  fi
  while IFS= read -r p; do [ -n "$p" ] || continue; launchctl unload "$p" 2>/dev/null || true; rm -f "$p"; done <<< "$plists"
  if [ ${#drifted[@]} -gt 0 ]; then
    # Keep a receipt naming only the drifted paths (with their backups) so nothing is forgotten.
    keep=$(printf '%s\n' "${drifted[@]}" | jq -R . | jq -s .)
    jq --argjson keep "$keep" '.owned |= with_entries(select(.key as $k | $keep | index($k)))
      | .generated |= with_entries(select(.key as $k | $keep | index($k)))
      | .backups |= with_entries(select(.key as $k | $keep | index($k)))
      | .added_registrations = [] | .created_plists = []' "$RECEIPT" > "$RECEIPT.tmp" && mv "$RECEIPT.tmp" "$RECEIPT"
    echo "uninstalled except ${#drifted[@]} changed path(s); review them, then remove by hand or reinstall"; exit 1
  fi
  rm -f "$RECEIPT"; echo "uninstalled"; exit 0
fi

# ---- install / repair / upgrade (one converge) -----------------------------------------------
if [ ${#todo[@]} -eq 0 ]; then echo "nothing to do"; exit 0; fi
echo "install would change: ${todo[*]}"
foreign=(); for f in $LINKS $GENERATED; do [ "$(item_state "$f")" = foreign ] && foreign+=("$H/$f"); done
[ ${#foreign[@]} -eq 0 ] || echo "existing files to back up and replace: ${foreign[*]}"
[ "$APPLY" = 1 ] || { echo "preview only; add --apply"; exit 0; }

mkdir -p "$H"
BK="$HOME/.claude/clio-runtime-backups/$(date -u +%Y%m%dT%H%M%SZ)"
backups=$( [ -f "$RECEIPT" ] && jq -c '.backups // {}' "$RECEIPT" || echo '{}')
for p in ${foreign[@]+"${foreign[@]}"}; do
  mkdir -p "$BK"; mv "$p" "$BK/"
  # Keep the oldest backup: it is the pre-install original.
  backups=$(jq -c --arg p "$p" --arg b "$BK/$(basename "$p")" 'if has($p) then . else .[$p] = $b end' <<< "$backups")
done
for f in $LINKS; do [ "$(item_state "$f")" = ok ] || { rm -f "$H/$f"; ln -s "$SRC/$f" "$H/$f"; }; done
generated='{}'
for f in $GENERATED; do
  [ "$(item_state "$f")" = ok ] || { extract "$f" > "$H/$f.tmp.$$"; chmod 755 "$H/$f.tmp.$$"; mv "$H/$f.tmp.$$" "$H/$f"; }
  generated=$(jq -c --arg p "$H/$f" --arg s "$(sha < "$H/$f")" '.[$p] = $s' <<< "$generated")
done
added=$( [ -f "$RECEIPT" ] && jq -c '.added_registrations // []' "$RECEIPT" || echo '[]')
if ! claude_reg; then
  [ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
  jq '.hooks.UserPromptSubmit = ((.hooks.UserPromptSubmit // []) + [{"hooks":[{"type":"command","command":"$HOME/.claude/hooks/log-prompt.sh"}]}])' \
    "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
  added=$(jq -c '. + ["claude"] | unique' <<< "$added")
fi
if zcode_wanted && ! zcode_reg; then
  mkdir -p "$HOME/.zcode/cli"; [ -f "$ZCONFIG" ] || echo '{}' > "$ZCONFIG"
  jq '.hooks = ((.hooks // {}) + (if (.hooks | has("enabled") | not) then {enabled: true} else {} end))
      | .hooks.events = ((.hooks.events // {}) + {UserPromptSubmit: (((.hooks.events.UserPromptSubmit // [])
          + [{hooks: [{type: "command", command: "$HOME/.claude/hooks/clio-capture.sh --agent zcode"}]}]))})' \
    "$ZCONFIG" > "$ZCONFIG.tmp" && mv "$ZCONFIG.tmp" "$ZCONFIG"
  added=$(jq -c '. + ["zcode"] | unique' <<< "$added")
fi
created=$( [ -f "$RECEIPT" ] && jq -c '.created_plists // []' "$RECEIPT" || echo '[]')
if [ "$DARWIN" = 1 ]; then
  mkdir -p "$LA"
  for t in $TAILERS; do
    p=$(plist_of "$t"); l="com.claude.clio-$t-tail"
    if [ ! -f "$p" ]; then
      cat > "$p" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$l</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/.claude/hooks/clio-$t-tail.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.claude/clio-$t-tail.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.claude/clio-$t-tail.err.log</string>
</dict>
</plist>
EOF
      created=$(jq -c --arg p "$p" '. + [$p] | unique' <<< "$created")
    fi
    loaded "$l" || launchctl load "$p"
  done
fi
owned=$(for f in $LINKS; do printf '%s\tlink\n' "$H/$f"; done; for f in $GENERATED; do printf '%s\tgenerated\n' "$H/$f"; done)
jq -n --arg src "$SRC" --arg hq "$hq_commit" --arg digest "$digest" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson generated "$generated" --argjson backups "$backups" --argjson added "$added" --argjson created "$created" \
  --arg owned "$owned" '{source: $src, hq_commit: $hq, digest: $digest, installed_at: $at,
     owned: ($owned | split("\n") | map(select(length > 0) | split("\t") | {(.[0]): .[1]}) | add),
     generated: $generated, backups: $backups, added_registrations: $added, created_plists: $created}' \
  > "$RECEIPT.tmp" && mv "$RECEIPT.tmp" "$RECEIPT"
echo "installed from $SRC${hq_commit:+ (HQ ${hq_commit:0:12})}; receipt $RECEIPT"
