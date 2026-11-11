---
name: clio
description: Install, verify, or uninstall prompt capture for Claude Code, ZCode, Codex, and Agy — one shared writer logs every submitted prompt to a centralized JSONL and optionally renders it into a readable Markdown note.
---

# CLIO

CLIO installs a shared capture writer and per-agent registrations that append every
submitted prompt — from Claude Code, ZCode, Codex (VS Code / CLI), and Agy — to one
centralized JSONL: `~/.claude/prompt-log.jsonl` (the `~/.claude` name is historical;
it is the cross-agent log). An optional exporter renders that JSONL as Markdown at a
location you choose. Capture stays fast; formatting happens later, on demand or on a
schedule.

## What gets logged

One line per prompt, from every registered agent:

```json
{"timestamp":"2026-07-09T18:42:11Z","repo":"hypercart","branch":"main","machine":"fixture","agent":"claude-code","session_id":"abc123","prompt":"..."}
```

`agent` is one of `claude-code`, `zcode`, `codex`, `agy`. Rows written before the
`agent` field existed render as `claude-code` (display only — the stored rows are
never rewritten). The dedup ID stays `session_id:timestamp` for every agent.

## Install

> **Automated install (recommended on a fleet Mac):** once Skills Army HQ has deployed the
> `clio-capture` skill, run `clio-runtime.sh status` and then `clio-runtime.sh install --apply`
> from the deployed folder. It performs this block's steps, plus the Codex and Agy tailer jobs, from
> the deployed bytes: helpers become symlinks, the writer and shim are generated from the heredocs
> below, and existing files are backed up with a receipt. This manual block remains the reference
> it follows.

Run once (macOS/Linux), either from the root of a CLIO checkout or from an installed
`clio-capture` skill directory — the resolver below finds CLIO's source files in both layouts.
CLIO requires `jq` (the Codex and Agy tailers additionally use `python3`):

```bash
command -v jq >/dev/null 2>&1 || { echo "jq is required. Install it: brew install jq (macOS) / apt install jq (Linux)"; return 1 2>/dev/null || exit 1; }

# --- resolve CLIO's source files (checkout OR installed skill dir) ----------
# In a checkout the scripts live under utils/clio-capture/; in an installed skill they
# sit beside INSTALL.md with no prefix. Export CLIO_SRC yourself to override.
if [ -z "${CLIO_SRC:-}" ]; then
  for c in "$PWD/utils/clio-capture" "$PWD" \
           "$HOME/.claude/skills/clio-capture" \
           "$(git rev-parse --show-toplevel 2>/dev/null)/utils/clio-capture" \
           "$(git rev-parse --show-toplevel 2>/dev/null)/.claude/skills/clio-capture"; do
    [ -f "$c/prompt-log-to-md.sh" ] && { CLIO_SRC="$c"; break; }
  done
fi
[ -n "${CLIO_SRC:-}" ] || { echo "CLIO source not found — set CLIO_SRC to the folder holding prompt-log-to-md.sh"; return 1 2>/dev/null || exit 1; }

mkdir -p ~/.claude/hooks

# --- shared capture writer (one append path for every agent) ----------------
cat > ~/.claude/hooks/clio-capture.sh << 'EOF'
#!/bin/bash
# CLIO shared capture writer (GH-139): one append path for every agent adapter.
#
# Usage:
#   clio-capture.sh --agent <claude-code|zcode|codex|agy>            # hook mode: one JSON object on stdin
#   clio-capture.sh --agent <name> --record                          # tailer mode: one complete JSON row on stdin
#
# Legacy contract (SQLite mode returns nonzero if no durable receipt is possible):
#   exit 0 — row appended, or deliberately skipped (filters, validation, ID
#            collision). Capture NEVER blocks the calling agent.
#   exit 2 — usage error (missing/invalid --agent or unknown option).
#   exit 3 — append lock busy (tailer mode only; the caller must NOT advance
#            its cursor — retry next tick).
#
# Every row is normalized to UTC second precision before its ID is derived:
#   clio:id = session_id:timestamp   (timestamp = YYYY-MM-DDTHH:MM:SSZ)
# A same-session, same-second collision suppresses the second append and logs
# a content-free trace — a permanent drop with an audit line, never a duplicate.
set -euo pipefail

errlog="$HOME/.claude/prompt-log-errors.log"
LOG="$HOME/.claude/prompt-log.jsonl"
LOCK="$HOME/.claude/prompt-log.lock"
mkdir -p "$HOME/.claude" 2>/dev/null || true
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
minchars="${CLIO_MIN_PROMPT_CHARS:-20}"

AGENT=""; RECORD=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --agent) [ "$#" -ge 2 ] || { echo "$ts clio-capture: --agent requires a value" >> "$errlog"; exit 2; }; AGENT="$2"; shift 2 ;;
    --record) RECORD=1; shift ;;
    --*) echo "clio-capture: unknown option $1" >&2; exit 2 ;;
    *) echo "clio-capture: unexpected argument $1" >&2; exit 2 ;;
  esac
done

diag() { echo "$ts clio-capture[$AGENT]: $*" >> "$errlog"; }

case "$AGENT" in
  claude-code|zcode|codex|agy) ;;
  *) echo "$ts clio-capture: missing or invalid --agent (got '$AGENT')" >> "$errlog"; exit 2 ;;
esac

if ! command -v jq >/dev/null 2>&1; then diag "jq not found — row not logged"; exit 0; fi

machine=$(scutil --get ComputerName 2>/dev/null || hostname -s 2>/dev/null || hostname)
project_dir="${CLAUDE_PROJECT_DIR:-${ZCODE_PROJECT_DIR:-$PWD}}"
repo=$(basename "$(git -C "$project_dir" rev-parse --show-toplevel 2>/dev/null || echo "$project_dir")")
branch=$(git -C "$project_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

input=$(cat)

# Adapter + cleaning + capture filters + validation, in one jq pass.
# Hook mode accepts the documented key plus likely client variants and falls
# back to the session-id environment variable; tailer (--record) rows carry
# their own timestamp/repo/branch/machine. Wrong-typed or missing keys never
# produce a row with an empty prompt or session id — they are dropped here.
# (The jq result is captured via a plain assignment + rc check: bash 3.2
# cannot parse a multi-line command substitution inside an if condition, and
# a backslash-newline inside $() breaks it too — the defect class GH-156
# documented. CLIO must parse on the stock macOS interpreter.)
jq_rc=0
row=$(printf '%s' "$input" | jq -rc --arg ts "$ts" --arg agent "$AGENT" --arg min "$minchars" --arg env_sid "${CLAUDE_SESSION_ID:-}" --arg machine "$machine" --arg repo "$repo" --arg branch "$branch" --argjson record "$RECORD" '
  def clean_prompt:
    gsub("(?i)<(ide_selection|ide_opened_file|system-reminder|task-notification|local-command-stdout|local-command-caveat|command-name|command-message|command-args|command-contents|function_results|ADDITIONAL_METADATA|USER_SETTINGS_CHANGE|tool-use-id|status|output-file|event|cross-session-message|job|usage|tool_uses|SYSTEM_MESSAGE|CONTEXT_SUMMARY|ARTIFACT)[^>]*>.*?</\\1>"; ""; "gms")
    | gsub("(?i)</?USER_REQUEST>"; ""; "g")
    | gsub("(?im)^>?[ \\t]*\"?(Ran command:|Viewed |Used tool:|The user has approved this document\\.)[^\\n]*\\n?"; ""; "g")
    | gsub("\\n[ \\t]*\\n[ \\t]*\\n+"; "\n\n")
    | sub("^\\s+"; "") | sub("\\s+$"; "");
  def textval: (if type == "string" then . else "" end);
  (if $record == 1 then ((.prompt // "") | textval) else (((.prompt // .message // .user_prompt) // "") | textval) end) as $raw
  | (if $record == 1 then ((.session_id // "") | textval) else (((.session_id // "") | textval) as $s | (if ($s | length) > 0 then $s else $env_sid end)) end) as $sid
  | ($raw | clean_prompt) as $cleaned
  | ($min | tonumber) as $minn
  | select($raw | test("<task-notification>|\\[SYSTEM NOTIFICATION - NOT USER INPUT\\]|RELAY AUTOMATION"; "i") | not)
  | select(($cleaned | length) >= $minn)
  | select(($sid | length) > 0)
  | select(($cleaned | length) > 0)
  | (if $record == 1 then ((.timestamp // "") | textval) else $ts end) as $rts
  | ($rts | sub("\\.[0-9]+"; "") | (if endswith("Z") then .[0:19] + "Z" else . end)) as $nts
  | select(($nts | length) == 20)
  | ((if $record == 1 then ((.machine // "") | textval) else "" end) as $rm
     | (if ($rm | length) > 0 then $rm else $machine end)) as $mm
  | {timestamp: $nts,
     repo: (if $record == 1 then ((.repo // "") | textval) else $repo end),
     branch: (if $record == 1 then ((.branch // "") | textval) else $branch end),
     machine: $mm,
     agent: $agent,
     session_id: $sid,
     prompt: $cleaned}
') || jq_rc=$?
if [ "$jq_rc" -ne 0 ]; then
  diag "malformed input — row not logged"
  exit 0
fi

if [ -z "$row" ]; then
  diag "row dropped (capture filter, validation, or unusable payload)"
  exit 0
fi

# --- serialized scan-suppress-append (one writer at a time) -----------------
# CLIO_SQLITE_V1: a switched writer never appends to the legacy authority.
sqlite_capture() {
  local cfg="${CLIO_CONFIG:-$HOME/.claude/clio-storage.json}"
  [ -f "$cfg" ] || return 1
  local helper="$(dirname "$0")/clio-store.py"
  # Preserve optional source context without changing the legacy seven-field row.
  local sqlite_row
  sqlite_row=$(printf '%s' "$input" | jq -c --argjson base "$row" \
    --arg cwd "$project_dir" --argjson record "$RECORD" '
    $base + {checkout:(if $record == 1 then (.cwd // .checkout // "") else $cwd end),
      source_event_id:(.source_event_id // ""), repo_slug:(.repo_slug // ""), references:(.references // []), extras:(.extras // {})}')
  if printf '%s' "$sqlite_row" | python3 "$helper" capture >/dev/null; then
    return 0
  else
    local rc=$?
    diag "SQLite capture failed (rc=$rc); no success receipt"
    return "$rc"
  fi
}
if [ -f "${CLIO_CONFIG:-$HOME/.claude/clio-storage.json}" ]; then
  sqlite_capture
  exit $?
fi

acquire_lock() {
  # Give up after ~10s (tailers then defer the chunk; hooks never block).
  # The stale-break threshold (60s) MUST far exceed the give-up window, and
  # the give-up check runs FIRST — otherwise a writer that waited the full
  # window would break a legitimately held lock the moment it crossed the
  # staleness boundary.
  waited=0
  while ! mkdir "$LOCK" 2>/dev/null; do
    if [ "$waited" -ge 50 ]; then return 3; fi
    now=$(date +%s)
    # A lock without a readable born file falls back to the dir mtime, so a
    # SIGKILLed holder (or a failed born write) can never deadlock capture.
    born=$(cat "$LOCK/born" 2>/dev/null || stat -f %m "$LOCK" 2>/dev/null || stat -c %Y "$LOCK" 2>/dev/null || echo "$now")
    if [ $((now - born)) -gt 60 ]; then
      rm -rf "$LOCK"
      diag "broke a stale append lock"
      continue
    fi
    sleep 0.2
    waited=$((waited + 1))
  done
  date +%s > "$LOCK/born" 2>/dev/null || true
  return 0
}
release_lock() { rm -rf "$LOCK"; }

if ! acquire_lock; then
  # The lock belongs to another writer — leave it exactly as found.
  diag "append lock busy — row not logged"
  if [ "$RECORD" -eq 1 ]; then exit 3; fi
  exit 0
fi

# A writer may have waited while activation held this lock. Recheck before append.
if [ -f "${CLIO_CONFIG:-$HOME/.claude/clio-storage.json}" ]; then
  release_lock
  sqlite_capture
  exit $?
fi

row_id=$(printf '%s' "$row" | jq -r '(.session_id) + ":" + (.timestamp)')
if [ -s "$LOG" ]; then
  # Capture the full ID set BEFORE matching: grep -q early-exit would SIGPIPE
  # jq under pipefail and a real collision would read as "no collision".
  log_ids=$(jq -Rr 'fromjson? | ((.session_id // "") + ":" + (.timestamp // ""))' "$LOG" 2>/dev/null || true)
  case $'\n'"$log_ids"$'\n' in *$'\n'"$row_id"$'\n'*)
    diag "id-collision suppressed: $row_id"
    release_lock
    exit 0
    ;;
  esac
fi
printf '%s\n' "$row" >> "$LOG"
release_lock
exit 0
EOF
chmod +x ~/.claude/hooks/clio-capture.sh

# --- Claude Code shim (thin; keeps the existing settings.json registration) -
cat > ~/.claude/hooks/log-prompt.sh << 'EOF'
#!/bin/bash
# Claude Code shim — delegates to the shared CLIO writer. The registration in
# ~/.claude/settings.json still names this path, so upgrades need no settings
# change and the uninstall procedure is unchanged.
exec "$(dirname "$0")/clio-capture.sh" --agent claude-code
EOF
chmod +x ~/.claude/hooks/log-prompt.sh

SETTINGS=~/.claude/settings.json
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

if grep -q "log-prompt.sh" "$SETTINGS" 2>/dev/null; then
  echo "Hook already registered in $SETTINGS — skipping."
else
  jq '.hooks.UserPromptSubmit = ((.hooks.UserPromptSubmit // []) + [{"hooks":[{"type":"command","command":"$HOME/.claude/hooks/log-prompt.sh"}]}])' \
    "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
  echo "Hook registered in $SETTINGS."
fi

# --- ZCode registration (config-file hooks; disabled unless enabled: true) --
ZCONFIG="$HOME/.zcode/cli/config.json"
if [ -d "$HOME/.zcode" ] || [ "${1:-}" = "--with-zcode" ]; then
  mkdir -p "$HOME/.zcode/cli"
  [ -f "$ZCONFIG" ] || echo '{}' > "$ZCONFIG"
  if grep -q "clio-capture.sh" "$ZCONFIG" 2>/dev/null; then
    echo "ZCode hook already registered in $ZCONFIG — skipping."
  else
    if jq '.hooks = ((.hooks // {}) + (if (.hooks | has("enabled") | not) then {enabled: true} else {} end))
         | .hooks.events = ((.hooks.events // {}) + {UserPromptSubmit: (((.hooks.events.UserPromptSubmit // [])
             + [{hooks: [{type: "command", command: "$HOME/.claude/hooks/clio-capture.sh --agent zcode"}]}]))})' \
      "$ZCONFIG" > "$ZCONFIG.tmp" && mv "$ZCONFIG.tmp" "$ZCONFIG"; then
      echo "ZCode hook registered in $ZCONFIG."
    else
      echo "ZCode registration failed — config untouched." >&2
    fi
  fi
fi

install -m 0755 "$CLIO_SRC/clio-store.py" ~/.claude/hooks/clio-store.py
install -m 0755 "$CLIO_SRC/prompt-log-to-md.sh" ~/.claude/hooks/prompt-log-to-md.sh

echo "✅ Installed. Smoke test (uses the Claude shim; expects agent=claude-code):"
echo '{"prompt":"a substantive session-opening prompt that runs well past the twenty character capture threshold on its own","session_id":"install-check"}' | ~/.claude/hooks/log-prompt.sh
tail -1 ~/.claude/prompt-log.jsonl
```

The ZCode registration fires only when a `~/.zcode` directory already exists (or you
pass `--with-zcode`), so installing CLIO on a machine without ZCode changes nothing
there.

**Pinning the live ZCode payload (one-shot probe).** The writer accepts the documented
`prompt`/`session_id` keys plus likely variants and falls back to the session-id
environment variable, so capture works even if the client's payload drifts. To pin the
exact payload a client posts, register this diagnostic hook for one prompt, submit any
prompt, then remove it:

```bash
cat > ~/.claude/hooks/clio-hook-probe.sh << 'EOF'
#!/bin/bash
umask 077
input=$(cat); printf '%s' "$input" > "$HOME/clio-hook-payload.json"
exit 0
EOF
chmod +x ~/.claude/hooks/clio-hook-probe.sh
jq '.hooks.events.UserPromptSubmit = (((.hooks.events // {}).UserPromptSubmit // [])
  + [{hooks: [{type: "command", command: "$HOME/.claude/hooks/clio-hook-probe.sh"}]}])' \
  ~/.zcode/cli/config.json > /tmp/probe-config.json && mv /tmp/probe-config.json ~/.zcode/cli/config.json
# …submit one prompt in the client, then read ~/clio-hook-payload.json and unregister the probe…
```

## Verify (real session)

Start a new Claude Code or ZCode session anywhere, submit any prompt, then:

```bash
tail -f ~/.claude/prompt-log.jsonl
```

Each captured line carries `"agent":"claude-code"` or `"agent":"zcode"`.

## SQLite history and seven-day view (opt-in pilot)

Python **3.8+** is required for this mode. The installer above copies `clio-store.py`
beside the shared writer. Existing capture remains JSONL until explicit activation;
installing these scripts alone does not migrate private history. Migration reuses
the **same Obsidian path, filename and existing exporter schedule**. A verified
backup and complete coverage of the existing note are required before that file
becomes the rolling view; tailer states and full history are retained.

The database defaults to `~/.claude/prompt-log.sqlite3`; pass `--db /private/path/history.sqlite3`
**before** a subcommand to use another local path. Files are private. Never put a live
SQLite database, its WAL, or its pending directory in a synchronized folder.

For a local installation where historical gaps are accepted but other Macs still
publish the shared note, use `activate --capture-only` after import/verification.
New captures use SQLite. The unchanged scheduled exporter drains receipts and
refreshes `~/.claude/prompt-log-compat.jsonl`, reporting `note_publication: paused`;
it does not touch the Obsidian note or create another Markdown note. Existing
sources/backups remain intact. Point existing downstream readers at this full-history
compatibility file; the original JSONL stops growing after activation. Other Macs
remain unchanged until individually installed. This is not a rolling-note cutover
or proof of complete fleet coverage. `migrate-view` still requires its explicit
single-publisher and historical-coverage checks before the same note can be replaced.
An explicit `project --jsonl PATH --jsonl-only` uses the same guarded export path.

### Per-Mac installation and retry

Use this existing procedure per device; do not assume another Mac's paths, jobs,
available agents or history. Inspect the actual source, helper/writer versions,
storage config, exporter plist and tailer cursor paths before replacing anything.
Back them up privately, verify hashes, install the helper before enabling capture,
and preserve existing job arguments and intervals. Install only the adapters that
the device uses. A missing collector source is not permission to reset its cursor.

If a valid CLIO config already exists, retain its database and owner, query/drain it
and upgrade the runtime files; do not initialize or activate a second store. If a
database exists without config, inspect its schema, owner and import receipts before
resuming the interrupted install; never delete/reinitialize it just to make retry
pass. Keep incomplete backups and pending receipts until accounted for. A busy lock,
changed source or failed verification should leave the current capture mode intact.
Use `--db` and `activate --source` for a device's inspected alternate paths; use
`--fresh` only when the legacy source genuinely does not exist.

Prefer `--capture-only` while shared-note ownership or historical reconciliation is
unresolved. Verify the installed shared writer, receipt draining and full-history
compatibility export before pointing downstream readers at the new source. Keep
unavailable historical data in its verified original backups without claiming it is
in SQLite. Imported laptop adoption stores are private history namespaces, not proof
of installed device identities; inspect their retained mapping before a later device
installation to avoid importing the same historical log under a second origin.

After each install, verify the routes actually present on that Mac, inspect pending
receipts and exporter status, and confirm source/note/plist preservation. On failure,
retain diagnostics and SQLite-era arrivals, use the rollback below, and adapt the
existing procedure to the observed device rather than adding another job or writer.

1. Pause the Markdown exporter on **every device writing the shared note**, and
   designate one publisher. Install the updated shared writer/helper, exporter and
   tailers; verify all registrations use them. Preserve source JSONL, registrations
   and tailer states. Capture can continue during backfill. A fresh installation
   should run its legacy exporter once before activation to establish the normal
   note/header. For an existing installation, keep its current note and job unchanged.
2. Initialize and import while legacy capture continues:

   ```bash
   python3 ~/.claude/hooks/clio-store.py init
   python3 ~/.claude/hooks/clio-store.py import-jsonl ~/.claude/prompt-log.jsonl
   ```

   Import commits at most 1,000 complete lines per invocation. Repeat until
   `remaining_bytes` is zero; investigate after ten batches instead of leaving an
   unbounded retry loop. `--max-records` selects a different explicit batch size.
   Complete invalid lines are retained privately in `source_lines.quarantine`, with
   line/hash/reason accounting; an unterminated tail stays pending. Replaced or altered
   sources fail closed; use an explicit new `--source label` only after inspecting
   the replacement. Repeated valid rows are deduplicated while every occurrence is counted.
3. Verify nonempty source parity, then activate. Activation takes the existing append
   lock without breaking another owner's lock, imports at most 100 final arrivals,
   verifies parity/integrity, saves an untouched source backup and atomically writes
   `~/.claude/clio-storage.json`. If backlog remains, repeat online import first.
   Import, parity and backup loops check a five-second cutover deadline. Slow storage
   may extend an individual I/O call; a budget failure leaves legacy mode active.
   If a large source repeatedly exceeds the budget, pause submissions for an offline
   migration review instead of bypassing the gate. A failed backup may leave a private
   partial `.pre-sqlite-*` file; activation has not completed unless config exists.

   ```bash
   python3 ~/.claude/hooks/clio-store.py verify-import ~/.claude/prompt-log.jsonl
   python3 ~/.claude/hooks/clio-store.py activate
   ```

   For a genuinely fresh installation with **no legacy source file**, initialize then
   use `activate --fresh`; this does not bypass migration checks on an existing file.
   A busy lock or invalid source prevents activation. A queued legacy writer rechecks
   activation after obtaining its lock. Do not manually create the configuration to
   bypass these gates.
4. Import other devices' histories using the existing JSONL/device import commands,
   then register the **existing note** for rolling publication:

   ```bash
   python3 ~/.claude/hooks/clio-store.py migrate-view --publishers-paused
   ```

   This reads `~/Library/LaunchAgents/com.claude.prompt-log-to-md.plist` to discover
   its existing destination. It never rewrites that plist: filename, vault location,
   interval, label, arguments and logs stay unchanged. For a cron/manual setup with
   no plist, pass `--markdown "/the/existing/Obsidian note.md"`; otherwise the legacy
   `~/.claude/prompt-log.md` default applies. Conflicting explicit/detected paths or
   unsupported job arguments stop migration instead of guessing a new file.

   The command verifies every historical entry against SQLite, including prompt and
   device/branch/agent metadata, and saves an exclusive, hash-verified backup beside
   the local DB under `<database>.view-backups/` (outside the vault when the DB is
   correctly local). Your header, frontmatter and personal notes above the historical
   marker are preserved verbatim. Unrecognized content below it, unsupported older
   entry formats or missing device records stop migration for reconciliation. No
   entries are guessed or discarded. The note itself is unchanged until publication.

   If the operator explicitly accepts unrecoverable historical gaps or repeated
   sections, use `migrate-view --publishers-paused --archive-unreconciled-note`.
   This preserves the entire original note in the same exclusive verified backup
   and keeps the exact header through the first historical marker. Remaining
   original content is archived, not claimed imported into SQLite: the receipt
   reports `coverage: archived-not-reconciled` and `covered_entries: null`.
   Default migration still requires full entry parity. This option retains the
   single-publisher assertion, destination checks, backup verification, and
   rejection of later foreign edits. It never guesses lost prompt metadata.

   `--publishers-paused` asserts that you paused all shared-note writers and selected
   this publisher; it does not discover or control other Macs. Verify fleet convergence
   and resolve the existing Pulse ownership dependency before shared deployment.
   Resume **only this publisher's existing job**, using its unchanged command/path.
   That command now drains receipts and atomically renders the rolling view to the
   same note, plus `~/.claude/prompt-log-compat.jsonl`. No new timer, new note or changed
   bookmark is needed. Other devices keep capturing but must not publish this file.

   For manual publication after registration, `prompt-log-to-md.sh --sqlite` uses
   the registered path automatically. `clio-store.py project` does too. An explicit
   `project --markdown /scratch/preview.md` is only a preview, not migration. Activation
   without `migrate-view` makes the scheduled exporter report a migration-required
   error; it does not silently create a separate recent note.

   Hook capture waits at most 500 ms for SQLite contention; durable queued rows
   survive in `<database>.pending/`. Inspect `drain`'s pending count if a backlog
   persists across two runs. A failed note replacement retains the prior file; the
   next job can retry. Unexpected edits/foreign arrivals or a changed backup stop
   publication rather than overwrite them. Preserve and reconcile those bytes before
   continuing; don't manually edit hashes in `clio-storage.json`. Diagnostics use
   `~/.claude/prompt-log-errors.log` and existing job stderr.
5. Point Rebalance/Daily's existing source configuration (`clio_prompt_log_path` or
   `REBALANCE_CLIO_PROMPT_LOG` in the **scheduled process's** environment) to the full
   chronological compatibility JSONL. Verify that effective configuration in Rebalance.
   Do not substitute the rolling Markdown or snapshot transport file. The old local
   JSONL stops growing after activation and remains a migration/rollback source.

The rolling view uses UTC, newest timestamp first with record-ID tie-breaking. Its
inclusive window is `[cutoff - 168 hours, cutoff]`; future-dated rows remain in the
DB but are omitted. `project --cutoff 2026-09-30T00:00:00Z` provides repeatable output.
Stdout reports row/byte counts; large prompts are not truncated. Legacy exporter
`--status`, `--backfill`, `--repair` and reconciliation are refused in activated
SQLite mode; use `query`, `drain` and `project`. Old cursors/receipts remain preserved.
Path compatibility does not make the new rolling entry format identical to the
legacy journey-replay format; that consumer upgrade remains separately tracked.

### T3 Code prompt capture (opt-in, SQLite mode)

After installing the current CLIO runtime and activating SQLite capture, register
the database of the local T3 environment you use:

If you sync CLIO history across devices, upgrade CLIO on every participating
reader before enabling this source: older helpers cannot validate the new T3
producer's stable record identities.

```bash
python3 ~/.claude/hooks/clio-store.py configure-t3 ~/.t3/userdata/statev2.sqlite
python3 ~/.claude/hooks/clio-store.py capture-t3
```

For a custom T3 home or development environment, pass its actual
`userdata/statev2.sqlite` path. Registration starts at the current committed end;
it does not import historical conversations. Repeating registration preserves the
source identity and position. Each invocation reads at most 1,000 events. The
existing SQLite export schedule also captures one page before exporting; if you
have no exporter scheduled, run `capture-t3` yourself. No new job is installed.

All providers share this path. Direct web/desktop and mobile text submissions,
including short prompts and steering, retain their original text and UTC time.
Imported/automated/server/MCP input is excluded; a fresh human submission within
an imported or child thread remains eligible. Attachment contents are excluded.
Rows carry `extras.ide=t3-code`, T3 message/thread IDs, instance and model.
Agent names use the driver when available (`claude-code` and `agy` retain CLIO's
existing names), otherwise the provider instance. Project, branch and driver
labels describe the projections observed at capture time, not historical state.
Missing project metadata is explicitly marked; missing run metadata stops that
page for retry. A provider's native hook/tailer may independently record the
same text; this feature deduplicates T3 retries, not cross-harness observations.

The reader supports T3's unified version-2 application thread events. Unknown
layouts/versions, replaced databases or a regressed cursor refuse capture with
an error. The exporter still publishes existing CLIO history and exits nonzero
when T3 capture refuses; inspect `prompt-log-errors.log` and run `capture-t3` to
see the error. T3 is opened read-only. First accepted text and metadata win for
each T3 message, including queued writes and replay after interruption.

To stop capture while preserving history and its private `.t3.json` sidecar:

```bash
python3 ~/.claude/hooks/clio-store.py configure-t3 --disable
```

Registering the same path again resumes from its preserved position, including
submissions made while scans were disabled. To change environments, disable
capture first, then register the new source path. For a deliberately replaced or
rebuilt database at the same path, also disable before registering again. The
previous sidecar is archived beside it with its source UUID; existing history is
retained, while the new source gets a new UUID and starts at its current end.
Active registrations refuse replacement; no capture scan resets a cursor.

### Read-only agent lookup

```bash
python3 ~/.claude/hooks/clio-store.py query --repo rebalanceOS \
  --since 2026-09-23T00:00:00Z --until 2026-09-30T00:00:00Z \
  --text 'frozen packet' --limit 20
python3 ~/.claude/hooks/clio-store.py query --device 'MBP 14"' --agent codex
python3 ~/.claude/hooks/clio-store.py query --session SESSION --offset 20 --limit 20
python3 ~/.claude/hooks/clio-store.py query --record-id clio1-RECORD_HASH
python3 ~/.claude/hooks/clio-store.py query \
  --reference https://github.com/HiQS-Labs/XYZ-CLIO/issues/3 --explain
```

Queries open the existing CLIO DB with SQLite `mode=rw` and enforce SQL
`query_only` before reading. This permits WAL/SHM bookkeeping across SQLite
runtimes while refusing changes to event data. Queries never initialize a missing
DB and use bound parameters. Text is a literal, case-sensitive substring. Results include
prompt, time, device (`machine`), agent, session, branch, checkout, canonical repo
when supplied, identity, references and extras. `--origin` filters the stable store
owner rather than a mutable human device label. Tailers include `source_event_id`
(raw source-line hash plus byte offset, scoped by origin/agent/session). Its retry
identity excludes repo/branch/device/checkout labels resolved at poll time; the
first committed labels remain stored even if those labels change before a retry.
Imports reject conflicting payloads; they do not silently rewrite provenance. Pagination is timestamp/ID descending;
concurrent new arrivals can shift offsets, so fix a time range for stable paging.

References are **explicit producer metadata**, not inferred task status. A capture
record can include `repo_slug`, `checkout` (or a tailer's `cwd`), `extras`, and:

```json
{"references":[{"type":"issue","url":"https://github.com/HiQS-Labs/XYZ-CLIO/issues/3","relation":"task-context"},{"type":"ledger","repo_slug":"HiQS-Labs/XYZ-forge","row_id":"ROW_ID","relation":"mentioned"}]}
```

Use `type:"pr"` with a qualified `/pull/N` URL. Only `mentioned` and `task-context`
relations are accepted. No status or accepted-start writes occur. Existing client
payloads need not provide these optional fields; unknown historical values remain
unknown. Rebalance's consumer upgrade will carry this provenance through its existing
semantic provider and readonly XYZ status adapter; it is not installed by CLIO.

### Device snapshots and coverage

```bash
python3 ~/.claude/hooks/clio-store.py export-device /private/staging/clio.jsonl
python3 ~/.claude/hooks/clio-store.py import-device /private/received/clio.jsonl
```

A snapshot is one atomic file: versioned first-line manifest (owner UUID, generation
UTC, count and content hash), followed by source records. The caller can stage it at
`devices/<owner-uuid>/clio.jsonl` for the existing Git Pulse Sync publisher. CLIO never
commits, pushes or creates a timer. That integration uses Rebalance #282's
file ownership/publisher work; a local query is **not** proof of complete fleet coverage.
Read accepted snapshot receipts from `device_imports` to see the source generation and
receipt time. Expected/missing device reporting belongs in the downstream consumer.

Export selects only this store's owner UUID; receiving a snapshot never changes its
origin or ID, and foreign rows are not re-exported as local. `legacy-adopted` denotes
ownership assigned during import, **not** recovered historical hardware identity.
Identical legacy files separately adopted by different stores may have different IDs;
the old data cannot prove whether they were retries or separate submissions. Original
machine/agent values and namespaced extra metadata remain intact. No live WAL sync.

### Backup, restore and rollback

```bash
python3 ~/.claude/hooks/clio-store.py drain
python3 ~/.claude/hooks/clio-store.py backup /private/backups/clio-snapshot.sqlite3
```

`backup` uses SQLite's online backup API and refuses an existing destination. It is a
snapshot of committed history: pause submissions/maintenance and require zero pending
receipts for a complete cutover recovery point. Preserve the private config and any
pending receipts too. Restore to a **new** local DB path, inspect it with `--db ... query`
and `PRAGMA integrity_check`, reconcile any later arrivals, then update the private
configuration atomically while writers are quiesced. Never replace a live database
with a raw copy of its main file while WAL is active. A restored backup retains its owner UUID:
use it only as recovery for the same logical device, never as a second live device.
Initialize a fresh store for another device and import the original device snapshot;
self-owned snapshots are rejected to prevent history from being echoed as local.

For rollback, first pause submissions and all scheduled tailers/shared exporters.
Preserve the view receipt and its verified original-note backup. After reconciling
SQLite-era history as described below, restore that backup to the **same note path**,
retaining the current rolling note as another recovery copy. Restore the preserved
configuration with SQLite disabled only while writers are stopped; resume the
unchanged job with the legacy writer/readers. Restoring the old note alone is not
a complete history rollback.

With writers stopped, drain receipts,
back up SQLite/config/source state, and generate a full chronological rollback JSONL
at a **new** path using `project --markdown /private/rollback-preview.md --jsonl /private/rollback.jsonl`. Verify nonempty
row counts and identities before selecting that complete file as the legacy log.
Preserve the original log under its backup name; disable the SQLite config only while
writers are stopped. Resume the legacy writer and its matching consumers together.
Keep the SQLite store and tailer cursors so SQLite-era events are not discarded.
Legacy same-second ID suppression remains a legacy limitation; the preserved SQLite
backup is the authoritative recovery copy for those collisions. Do not retire it
until all writers/readers/queued work and the rollback window are accounted for.

## Optional: export to human-readable Markdown

The exporter appends only entries not already identified in the note, with newest
ones immediately below `<!-- CLIO:ENTRIES -->`. It preserves everything above that
marker, reconciles full entries found in matching conflict siblings, and quarantines
those siblings under `.clio-reconciled/`. Each entry's metadata line reads
`machine · branch · agent` (rows without a stored `agent` render as `claude-code`).

Its cursor (`~/.claude/prompt-log-to-md.state`) is only a scan optimization. The
source-owned `~/.claude/prompt-log-manifest.txt` is an append-only delivery receipt:
one rendered `clio:id` per line, no prompt text. It remains if the cursor is deleted.

**Run it** — default location:

```bash
~/.claude/hooks/prompt-log-to-md.sh
```

**Run it** — custom location, for example an Obsidian vault:

```bash
~/.claude/hooks/prompt-log-to-md.sh ~/vault/_meta/prompt-log/prompt-log.md
```

**Preview conflict recovery without changing the note or moving files:**

```bash
CLIO_RECONCILE_DRY_RUN=1 ~/.claude/hooks/prompt-log-to-md.sh ~/vault/_meta/prompt-log/prompt-log.md
```

The first run creates a fixed header and marker, then one `## <REPO>` block per
prompt. To sync on a schedule, point a launchd job (macOS) or cron entry at the
same exporter command and output path. **In legacy JSONL mode only**, each device
can append its local prompts to the shared note. SQLite rolling publication uses
one designated publisher after the same-path migration above.

### Auto-sync every 1 minute (macOS launchd)

This example creates a **new** one-minute job. During SQLite migration, do not
run this block over an existing job: keep its plist bytes, arguments and interval
unchanged, including a deployment configured for 300 seconds. Migration reads
the existing destination; it does not install or rewrite the schedule.

Replace `OUT_PATH` with your chosen output file:

```bash
OUT_PATH="$HOME/vault/_meta/prompt-log/prompt-log.md"
PLIST=~/Library/LaunchAgents/com.claude.prompt-log-to-md.plist

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.prompt-log-to-md</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/.claude/hooks/prompt-log-to-md.sh</string>
        <string>$OUT_PATH</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.claude/prompt-log-to-md.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.claude/prompt-log-to-md.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST"
```

Check it is running:

```bash
launchctl list | grep com.claude.prompt-log-to-md
```

Stop and remove it:

```bash
launchctl unload ~/Library/LaunchAgents/com.claude.prompt-log-to-md.plist
rm ~/Library/LaunchAgents/com.claude.prompt-log-to-md.plist
rm -f ~/.claude/prompt-log-to-md.out.log ~/.claude/prompt-log-to-md.err.log
```

## Optional: Codex capture (VS Code / CLI)

Codex has no prompt-submit hook, so a read-only tailer turns user prompts from Codex
session rollouts into CLIO history. It accepts legacy `event_msg`/`user_message`
and Desktop 0.165 `event_msg`/`item_completed` records whose item is `UserMessage`,
joining string text parts in order and ignoring image/nontext parts. It
never takes prompt text from `response_item` entries (where injected context can be
combined with user input), and never writes to the source. Run once from a CLIO checkout
or an installed `clio-capture` skill directory (requires `jq` and `python3`). This is a separate
shell from the main install, so it re-resolves `CLIO_SRC` unless you exported it:

```bash
if [ -z "${CLIO_SRC:-}" ]; then
  for c in "$PWD/utils/clio-capture" "$PWD" "$HOME/.claude/skills/clio-capture"; do
    [ -f "$c/clio-codex-tail.sh" ] && { CLIO_SRC="$c"; break; }
  done
fi
[ -n "${CLIO_SRC:-}" ] || { echo "CLIO source not found — set CLIO_SRC to the folder holding clio-codex-tail.sh"; return 1 2>/dev/null || exit 1; }

install -m 0755 "$CLIO_SRC/clio-codex-tail.sh" ~/.claude/hooks/clio-codex-tail.sh
```

First run starts **now** and persists that capture boundary, even before a sessions
folder exists. Later polls capture eligible first prompts from newly discovered root
sessions, including prompts completed between polls. Existing pre-boundary history
and inherited subagent prompts are excluded. Set `CLIO_TAIL_BACKFILL=1` for an
explicit history replay of **root files, including already-scanned files**. The
per-file rewind and history eligibility are checkpointed before delivery; if a writer
fails, the next ordinary tick retries that replay without requiring the flag again.
Only files reached by that invocation have durable replay intent. Repeat the explicit
flag after an interrupted whole-history scan to include files it never reached.
The global capture boundary stays unchanged. Stable source IDs suppress already-captured
rows; the printed `delivered` count means writer acceptance (including dedup/filtering),
so verify actual SQLite rows to establish recovery. Source timestamps must be valid
and timezone-aware. Child-file inherited prompts remain excluded during replay.

Upgrading preserves legacy pending records on their original file. Replacement or
truncation switches those legacy files to the capture boundary, so previously
skipped history is not imported; older pending records cannot be recovered
automatically once that file provenance is lost. Clean polling delays retain the
boundary. An abandoned tailer lock (a run killed mid-tick) is reaped by the next
tick once it is older than 300 seconds; reaping is serialized behind
`<lock>.reap` and rechecked. This is an age check, not an owner-liveness check:
a run lasting more than 300 seconds can have its lock displaced. Only a kill inside that
millisecond reap step can leave `<lock>.reap` behind, which disables reaping (not
capture of a healthy lock); remove it after verifying no tailer is running.

The existing state also records a bounded zero-capture streak. After three consecutive
ticks that consume complete root-rollout data without any writer acceptance or deferred
file, one content-free warning is appended to `prompt-log-errors.log`. Idle ticks,
accepted rows, deferred writes and explicit replay reset the streak. Assistant output
also modifies rollouts: this warning asks you to inspect the event schema and capture
filters; it does not establish that a prompt was lost.

Schedule it every minute:

```bash
PLIST=~/Library/LaunchAgents/com.claude.clio-codex-tail.plist
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.clio-codex-tail</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/.claude/hooks/clio-codex-tail.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.claude/clio-codex-tail.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.claude/clio-codex-tail.err.log</string>
</dict>
</plist>
EOF
launchctl unload "$PLIST" 2>/dev/null; launchctl load "$PLIST"
```

### Recover missed Codex history

First land the reviewed upstream fix, publish it to XYZ-CLIO, and deploy through Skills
Army HQ. Do not point installed hooks at a task checkout. For manual replay, record
whether `com.claude.clio-codex-tail` is currently loaded and keep its existing plist.
Temporarily boot out only that job, then verify no scheduled or manual Codex tailer
invocation remains before backing up `prompt-log-codex-tail.state` and running
`CLIO_TAIL_BACKFILL=1 "$HOME/.claude/hooks/clio-codex-tail.sh"`. Keep other invocations stopped
throughout replay: the age-only lock is insufficient for a long backfill.

Restore the identical previously loaded job from its existing plist in a cleanup/finally
path on both success and failure. Leave a previously unloaded job unloaded. Do not change
its interval, command or exporter job. Preserve the state backup; a failed replay leaves
a durable rewind for each file already visited, so the restored normal schedule retries
those files. Files not yet visited retain their previous cursors; after an interrupted
whole-history scan, pause the job again and repeat the explicit backfill flag to cover
them. A completed full scan, followed by per-session SQLite checks, establishes recovery. Do not rewind the canonical SQLite database to undo a replay.

Use `clio-store.py query --agent codex --session SESSION --limit 100` for each requested
session and compare stable record IDs before/after a repeated replay. Timestamp a
substantive new Desktop submission and observe its matching SQLite row within 120
seconds to establish live acceptance. Report sessions with no legacy or modern
submitted events as unrecoverable from this source; never substitute response-item
context. A launchd configuration or a nonzero `delivered` count alone does not prove
that the intended row reached SQLite.

## Optional: Agy capture (Antigravity CLI)

Agy has no prompt-submit hook either; the same tailer pattern reads its per-conversation
FULL transcript JSONLs (`brain/<id>/.system_generated/logs/transcript_full.jsonl` — the
plain `transcript.jsonl` truncates large text), capturing only rows where `source` is
`USER_EXPLICIT` and `type` is `USER_INPUT`:

```bash
if [ -z "${CLIO_SRC:-}" ]; then
  for c in "$PWD/utils/clio-capture" "$PWD" "$HOME/.claude/skills/clio-capture"; do
    [ -f "$c/clio-agy-tail.sh" ] && { CLIO_SRC="$c"; break; }
  done
fi
[ -n "${CLIO_SRC:-}" ] || { echo "CLIO source not found — set CLIO_SRC to the folder holding clio-agy-tail.sh"; return 1 2>/dev/null || exit 1; }

install -m 0755 "$CLIO_SRC/clio-agy-tail.sh" ~/.claude/hooks/clio-agy-tail.sh
```

Then schedule it like the Codex tailer (label `com.claude.clio-agy-tail`, script
`$HOME/.claude/hooks/clio-agy-tail.sh`, logs `clio-agy-tail.*.log`).

## Uninstall

SQLite users: preserve the database, private configuration and pending receipts;
finish or explicitly preserve pending recovery before removing the helper.

This removes only CLIO's own registrations and installed files; unrelated hooks in
either client's config are untouched.

```bash
# Claude Code: remove the shim registration
tmp=$(mktemp)
jq 'if (.hooks // null) == null then . else
      (.hooks.UserPromptSubmit //= [])
      | .hooks.UserPromptSubmit = (.hooks.UserPromptSubmit
          | map(.hooks = ((.hooks // []) | map(select(((.command // "") == "$HOME/.claude/hooks/log-prompt.sh") | not))))
          | map(select((.hooks // []) | length > 0)))
      | if (.hooks.UserPromptSubmit // []) == [] then del(.hooks.UserPromptSubmit) else . end
    end' \
  ~/.claude/settings.json > "$tmp" && mv "$tmp" ~/.claude/settings.json

# ZCode: remove the writer registration and drop the enabled gate if CLIO set it
if [ -f ~/.zcode/cli/config.json ]; then
  tmp=$(mktemp)
  jq 'if (.hooks // null) == null then . else
        if (.hooks.events // null) == null then . else
          (.hooks.events.UserPromptSubmit //= [])
          | .hooks.events.UserPromptSubmit = (.hooks.events.UserPromptSubmit
              | map(.hooks = ((.hooks // []) | map(select(((.command // "") | contains("clio-capture.sh")) | not))))
              | map(select((.hooks // []) | length > 0)))
          | if (.hooks.events.UserPromptSubmit // []) == [] then del(.hooks.events.UserPromptSubmit) else . end
          | if ((.hooks.events // {}) == {}) then del(.hooks.events) else . end
        end
      end' \
    ~/.zcode/cli/config.json > "$tmp" && mv "$tmp" ~/.zcode/cli/config.json
fi

# launchd jobs (only if installed)
for label in com.claude.clio-codex-tail com.claude.clio-agy-tail; do
  plist=~/Library/LaunchAgents/$label.plist
  [ -f "$plist" ] && { launchctl unload "$plist" 2>/dev/null; rm "$plist"; }
done

rm ~/.claude/hooks/log-prompt.sh
rm -f ~/.claude/hooks/clio-capture.sh ~/.claude/hooks/clio-store.py ~/.claude/hooks/clio-hook-probe.sh \
      ~/.claude/hooks/clio-codex-tail.sh ~/.claude/hooks/clio-agy-tail.sh \
      ~/.claude/hooks/prompt-log-to-md.sh ~/.claude/prompt-log-to-md.state \
      ~/.claude/prompt-log-codex-tail.state ~/.claude/prompt-log-agy-tail.state \
      ~/.claude/prompt-log-manifest.txt ~/.claude/prompt-log-errors.log \
      ~/clio-hook-payload.json
```

## Notes

- **Scope:** both registrations are user-level, so one log covers every project and every registered agent.
- **Machine, branch, and agent:** all three are recorded with each prompt for later context; the agent app is the new field (GH-139), the device name is unchanged.
- **Legacy timestamps:** the raw JSONL and every `clio:id` stay **UTC** — the ID is `session_id:timestamp`, so localizing it would change all IDs, break dedup, and re-emit the note as duplicates. Only the *displayed* line is localized (`2026-07-19 14:27:50 PDT`). Conversion uses `python3` (`datetime.astimezone()`), **not** jq. Without `python3` the display falls back to UTC.
- **Capture filtering (permanent):** the writer skips two classes of prompt outright, for every agent:
  - *Automated turns* — anything containing `<task-notification>` or the `[SYSTEM NOTIFICATION - NOT USER INPUT]` preamble (background-task and monitor events). Matched on the raw prompt before tag stripping.
  - *Short prompts* — under `CLIO_MIN_PROMPT_CHARS` (default **20**) after injected blocks are stripped, so `yes` / `push it` are dropped while substantive session-opening prompts are kept. Set `CLIO_MIN_PROMPT_CHARS=0` to capture everything again.

  This is a **drop, not a hide** — unlike `PROMPT_LOG_EXCLUDE` below, a skipped prompt is unrecoverable. Prefer the render-side filter if you might want the text back later. Covered by `test/clio-capture.sh`.
- **Legacy same-second collisions:** two substantive prompts in the same session within one second share an ID; the second is suppressed and traced to the error log (content-free) rather than written as a duplicate.
- **Legacy render filtering (reversible):** `PROMPT_LOG_EXCLUDE` defaults to `file-based relay|cross-agent dependency drift`; matching text stays in raw JSONL but is omitted from the Markdown (reported as `state: excluded` by `--status`). Set it empty to render all prompts.
- **Legacy resetting:** deleting the state file rescans JSONL, but ID-based note deduplication prevents a duplicate rendered entry. The manifest is intentionally independent of that cursor.
- **Errors:** legacy hooks skip invalid/filtered prompts; tailers return nonzero on retryable failures. SQLite capture acknowledges only committed or durably queued rows and returns nonzero when no receipt can be saved. Failures and drop diagnostics go to `~/.claude/prompt-log-errors.log`; tailers surface lock/parse failures there too and never advance a cursor over undelivered rows; a manifest receipt failure is reported but never rolls back a successful export.

### Device-independent replica integration (source capability; rollout pending)

The existing capture scripts, SQLite schema and five-minute exporter stay in place. Git Pulse/Rebalance #282 must call CLIO's snapshot interface within its existing schedule; CLIO does not fetch, push or install another timer. Each device has a unique persistent origin UUID and an independent full-history SQLite replica. Only committed `devices/<origin-UUID>/clio.jsonl` snapshots from the configured private checkout are imported; dirty files are ignored.

After registering the same existing note with `migrate-view`, configure a trusted inventory including this device and every preserved origin:

```bash
python3 ~/.claude/hooks/clio-store.py configure-fleet /path/to/private/pulse-checkout \
  --origin <this-origin-UUID> --origin <other-origin-UUID> --repair-generated-note
python3 ~/.claude/hooks/clio-store.py reconcile-fleet
python3 ~/.claude/hooks/clio-store.py export-device /path/to/private/pulse-checkout/devices/<this-origin-UUID>/clio.jsonl
```

Use real canonical UUIDs, not the placeholders above. The checkout must have a committed HEAD. A one-time `export-device ... --origin <known-legacy-origin>` can seed preserved adoption history. Normal exports contain only the local origin, and reconcile runs before serialization to restore committed own history after backup recovery. Generic `import-device` still refuses self-import. Query output includes last reconciliation and note status; a local committed snapshot is not proof that another Mac received it.

`--repair-generated-note` explicitly makes the content below `<!-- CLIO:ENTRIES -->` machine-owned. Keep personal edits above that marker. Exact header and verified original backup remain protected. Unknown or merged bodies are archived completely and verified before replacement; unknown record IDs defer replacement for at most two hours while capture, imports and compatibility JSONL continue. Archives are private, deduplicated, limited to 128 files/256 MiB total (64 MiB each), and never automatically deleted. Capacity exhaustion refuses replacement and appears in status. A missing derived note can rebuild in this mode. Without opt-in, the original foreign-edit refusal remains.

Obsidian Sync can merge Markdown. Compare-before-replace cannot fence an edit arriving after its final comparison; archive protects observed bytes, not an unseen concurrent write. Before enabling a second Mac, native #282 must land and a disconnected/rejoin pilot must cover at least three existing Pulse intervals, expiry, source parity, header preservation and conflict archival. Record archive growth and stop rollout if projected capacity is below 180 days. No fleet runtime or Sync setting is changed by this PR.

### Studio activation milestone — 2026-10-02

This supersedes the pre-landing wording above for the Studio only.

CLIO #5 and Rebalance #303 are merged. The Studio has the canonical helper installed and
its three known preserved origins bootstrapped once into the private Git Pulse checkout.
Normal exports carry only its own origin; imported history remains in the full local SQLite
replica. Actual render, collector delivery, committed-history reconcile and the SAME seven-day
Obsidian note/header passed. Existing capture hooks and the five-minute exporter were left
running; five delivery jobs were briefly unloaded and restored with identical plist hashes.
The verified database/note/script/config backups remain private. Historical gaps stay accepted.

Lessons: update a copied collector separately from its source checkout; use the metadata owner
UUID rather than a hostname; bootstrap known preserved origins explicitly once, then prevent
normal foreign-origin echo; check exact backup record payloads as well as counts. An old heartbeat
uses legacy health until the upgraded collector first advertises fleet mode. Verify queued output
becomes delivered output after that first check-in. Keep SQLite/WAL private and local.

Other Macs remain disabled. This local milestone does not qualify complete four-Mac source
coverage, actual disconnected/rejoin behavior over three scheduled Pulse intervals, observed
Sync conflicts/archive capacity or seven-day delivery rates. The final filesystem comparison
cannot fence an unseen concurrent Obsidian Sync edit. Track those gates in native
[Rebalance #282](https://github.com/HiQS-Labs/rebalanceOS/issues/282), alongside the committed
local deployment receipt and configuration-error hardening. No further history collection is required.

Rebalance #304 configuration-error hardening is also merged and deployed as 0.97.1. The
[final local recheck](https://github.com/HiQS-Labs/rebalanceOS/blob/535bb7a/TESTS-RESULTS/2026-10-02%2BGH-282/deployment-recheck.json) records committed-origin reconcile, the enabled capture hook with natural arrivals after the helper upgrade, owner-only delivery, preserved backup payloads and the same note/header. These are local observations, not four-device qualification.

### Joining without a central device (GH-11)

No Mac controls the fleet. A device joins by delivering its own snapshot, and any Mac with the converged replica can publish the same note.

**Discovery (opt-in per device).** With `--discover-origins`, `reconcile-fleet` also imports every committed `devices/<canonical-UUID>/clio.jsonl` at the pinned HEAD. Your own origin is implied, so `--origin` becomes optional. Any `--origin` you still pass stays pinned, and a pinned origin with no snapshot still reports `missing`. Discovered snapshots get the same digest, owner, size and regression checks as configured ones. Pulse's own non-UUID `devices/<name>` entries are ignored. The result lists new origins under `discovered`.

**One-time upgrade.** This is the last step you ever run on a peer. `configure-fleet` rebuilds the fleet settings from the flags it is given, so repeat the flags you rely on:

```bash
# Capture-only device:
python3 ~/.claude/hooks/clio-store.py configure-fleet /path/to/private/pulse-checkout --discover-origins
# Device that already publishes the note: keep repair mode (and any --origin pins you still want).
python3 ~/.claude/hooks/clio-store.py configure-fleet /path/to/private/pulse-checkout --discover-origins --repair-generated-note
```

**Join a new device, or turn a capture-only device into a publisher.** Nothing runs on any other Mac:

1. Run `init`, import and verify, then `activate --capture-only`, as described above.
2. Run `configure-fleet <checkout> --discover-origins`. The existing collector delivers `devices/<this-UUID>/clio.jsonl`, and each peer imports it on its next scheduled export.
3. Run `reconcile-fleet` once the checkout holds the peers' snapshots.
4. Run `migrate-view --join-fleet-note` against the existing synced note. It registers the note only if this replica reproduces it byte for byte, with every record ID known and the same header. It refuses with "not yet in this replica" until reconcile has caught up, and refuses a hand-edited body. It cannot be combined with `--publishers-paused` or `--archive-unreconciled-note`.
5. Run `configure-fleet <checkout> --discover-origins --repair-generated-note`. From now on `scheduled-export` publishes, and the other publishers accept this device's render as `peer_generated`.

**Retirement** needs no change anywhere. A device that stops delivering just stops changing, and its committed snapshot and imported rows remain as history.

**Rollback:** rerun `configure-fleet` without `--discover-origins` to return to an explicit list. Restore a pre-join `clio-storage.json` backup to return a joined device to capture-only.
