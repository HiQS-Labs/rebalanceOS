#!/bin/bash
# rebalance OS — shared install flow for launchd jobs.
#
# Sourced by scripts/stack.sh, the ONE install path for the launchd fleet
# (`stack.sh up` for every policy job, `stack.sh install <job>...` for some).
# The 13 per-job install_*.sh scripts it replaced (GH-255) had drifted from
# `stack.sh up`: each carried job-specific steps the fleet path never ran. All
# job-specific install behaviour now lives HERE, so no path can skip it:
#
#     rb_install_launchd_job <label> [wrapper-relative-path]
#
# One flow for every job:
#   1. chmod +x the wrapper script (when one is named)
#   2. render scripts/<label>.plist.template into a temp file, substituting
#      {{REBALANCE_DIR}}, {{PYTHON}}, and {{HOME}}, and `plutil -lint` it
#      (RB_RENDER_CHECK=1 stops here — the caller's preflight)
#   3. job precondition (_rb_job_precondition) — may SKIP with exit 3, and
#      unloads/removes a previously installed copy whose precondition lapsed
#   4. warn if the installed plist carries hand-added secrets this render drops
#   5. create temp/logs and every directory the plist logs into (launchd opens
#      StandardOutPath/StandardErrorPath itself and does NOT create parents —
#      the redirect fails silently and the job's output goes nowhere)
#   6. ALWAYS `launchctl unload` first — `launchctl load` fails with an opaque
#      "Input/output error" if the job is already registered
#   7. `launchctl load`, verify the label registered (failure if it never does)
#   8. only then retire any label this job replaced (RB_RETIRED_LABELS)
#
# The job inventory, cadences, and scopes live in SCHEDULER.md (the policy
# table); tests/test_scheduler_policy.py enforces that templates stay in sync.

# Exit code for "precondition not met, job deliberately not installed".
RB_INSTALL_SKIPPED=3

# <successor-label>:<retired-label>. A rename in git is not a rename on the
# machine: the old plist stays loaded until something unloads it, and once it
# leaves SCHEDULER.md stack.sh treats it as unmanaged and will not touch it.
# GH-81 renamed vault-sync; left alone both fire at :15 doing the same
# vault+semantic write — the same-minute collision SCHEDULER.md forbids (GH-175).
RB_RETIRED_LABELS=(
    "com.rebalance-os.obsidian-vault-embeddings:com.rebalance-os.vault-sync"
)

# Test seam. `launchctl unload <path>` resolves the job from the Label INSIDE
# the plist, not from where the file sits, so a fixture plist under a redirected
# HOME still unloads the REAL job (observed, GH-59). Any test that exercises the
# install path must be able to substitute a stub. Unset in normal use.
LAUNCHCTL_BIN="${STACK_LAUNCHCTL_BIN:-${LAUNCHCTL_BIN:-launchctl}}"

RB_INSTALL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(cd "$RB_INSTALL_LIB_DIR/.." && pwd)"
REBALANCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "${HOME:-}/.config/rebalance/runtime-root" ]; then
    # Preserve spaces inside a valid checkout path; remove only a CR left by
    # a CRLF line ending. Doctor applies the same whitespace-preserving rule.
    _declared_root="$(sed -n '1{s/\r$//;p;}' "${HOME:-}/.config/rebalance/runtime-root")"
    if [ -n "$_declared_root" ] && [ -d "$_declared_root" ]; then
        REBALANCE_DIR="$_declared_root"
    fi
fi
PYTHON_BIN="$REBALANCE_DIR/.venv/bin/python"

# Job-specific install gates. Return 0 to install, $RB_INSTALL_SKIPPED (with
# a reason on stdout) to skip. Keep this the only per-label branch in the flow.
_rb_job_precondition() {
    case "$1" in
        com.rebalance-os.daily-work-synthesis)
            # GH-210: opt-in canary. Without its local config it has no call,
            # token or cost ceilings, so it is not installed at all.
            if [ ! -f "$REBALANCE_DIR/temp/daily-work-synthesis.json" ]; then
                echo "  SKIPPED: opt-in job — create temp/daily-work-synthesis.json (see SCHEDULER.md) to enable it"
                return "$RB_INSTALL_SKIPPED"
            fi
            ;;
    esac
    return 0
}

# The checkout a rendered plist is bound to. Every template substitutes
# {{REBALANCE_DIR}} at least once, so this is defined for all of them.
bound_root() {
    [ -f "$1" ] || return 0
    # `|| true` is load-bearing: with `set -o pipefail`, a plist containing no
    # <string> makes grep exit 1, which propagates out of the function and, via
    # `root=$(bound_root ...)` under `set -e`, kills the whole script.
    { /usr/bin/grep -o '<string>[^<]*</string>' "$1" 2>/dev/null || true; } \
        | /usr/bin/sed 's|<string>||; s|</string>||' \
        | /usr/bin/sed -nE 's#^(/.+)/(scripts|utils|\.venv|temp)/.*#\1#p' \
        | head -1
}

# Called only AFTER the successor has loaded and registered, so a failed
# replacement never leaves the machine with neither job. Touches a legacy
# plist only when it is bound to this checkout (same guard as stack.sh's
# target-root check), and deletes it only once launchd confirms it is gone.
# Returns 1 when a legacy job this checkout owns is still loaded.
_rb_retire_legacy_labels() {
    local label="$1" entry legacy legacy_plist legacy_root rc=0
    for entry in "${RB_RETIRED_LABELS[@]}"; do
        [ "${entry%%:*}" = "$label" ] || continue
        legacy="${entry#*:}"
        legacy_plist="$HOME/Library/LaunchAgents/$legacy.plist"
        "$LAUNCHCTL_BIN" list "$legacy" > /dev/null 2>&1 || [ -f "$legacy_plist" ] || continue
        legacy_root="$(bound_root "$legacy_plist")"
        if [ "$legacy_root" != "$REBALANCE_DIR" ]; then
            echo "  WARNING: left retired $legacy alone — bound to ${legacy_root:-an unreadable or missing plist}, not $REBALANCE_DIR" >&2
            continue
        fi
        "$LAUNCHCTL_BIN" unload "$legacy_plist" 2>/dev/null || true
        if "$LAUNCHCTL_BIN" list "$legacy" > /dev/null 2>&1; then
            echo "  ERROR: retired $legacy is still loaded; kept $legacy_plist — run: launchctl remove $legacy" >&2
            rc=1
        else
            rm -f "$legacy_plist"
            echo "  Retired $legacy (replaced by $label)"
        fi
    done
    return "$rc"
}

# Secret-shaped keys (…_API_KEY / …_TOKEN / …_SECRET) are never in a tracked
# template; an operator may hand-add them to the RENDERED plist. Re-rendering
# drops them, so say so instead of silently breaking the job's next run.
# XML comments are stripped first: several templates document the key in a
# comment, which a plain grep would count as "still present" and stay silent.
_rb_plist_live_keys() {
    perl -0pe 's/<!--.*?-->//gs' "$1" 2>/dev/null \
        | grep -oE '<key>[A-Z0-9_]*(API_KEY|TOKEN|SECRET)</key>' \
        | sed 's/<[^>]*>//g' | sort -u
}

_rb_warn_dropped_secrets() {
    local installed="$1" staged="$2" key staged_keys
    [ -f "$installed" ] || return 0
    staged_keys="$(_rb_plist_live_keys "$staged" || true)"
    for key in $(_rb_plist_live_keys "$installed" || true); do
        if ! printf '%s\n' "$staged_keys" | grep -qx "$key"; then
            echo "  WARNING: $installed had a hand-added $key that this reinstall drops —" >&2
            echo "           re-add it to the rendered plist's EnvironmentVariables, or rely on the keyring lookup." >&2
        fi
    done
}

# Every directory the plist writes logs into. Read from the rendered plist so a
# template that moves its logs needs no second edit here.
_rb_plist_log_dirs() {
    grep -A1 -E '<key>Standard(Out|Error)Path</key>' "$1" 2>/dev/null \
        | sed -n 's|.*<string>\(.*\)</string>.*|\1|p' \
        | while IFS= read -r path; do dirname "$path"; done \
        | sort -u
}

# Escape '/' and '&' so a path is safe as a sed replacement string.
_rb_sed_escape() {
    printf '%s\n' "$1" | sed 's/[\/&]/\\&/g'
}

rb_install_launchd_job() {
    local label="$1"
    local wrapper="${2:-}"
    local template="$SCRIPT_DIR/$label.plist.template"
    local dest="$HOME/Library/LaunchAgents/$label.plist"

    if [ ! -f "$template" ]; then
        echo "ERROR: missing plist template: $template" >&2
        return 1
    fi
    if grep -q "{{PYTHON}}" "$template" && [ ! -x "$PYTHON_BIN" ]; then
        echo "ERROR: expected virtualenv python at $PYTHON_BIN" >&2
        return 1
    fi
    if [ -n "$wrapper" ]; then
        if [ ! -f "$REBALANCE_DIR/$wrapper" ]; then
            echo "ERROR: wrapper script not found: $REBALANCE_DIR/$wrapper" >&2
            return 1
        fi
        if [ ! -x "$REBALANCE_DIR/$wrapper" ]; then
            chmod +x "$REBALANCE_DIR/$wrapper"
            echo "  Made $wrapper executable"
        fi
    fi

    # Render and lint into a temp file BEFORE unloading anything (GH-59).
    # Rendering straight to $dest meant a malformed template overwrote a good
    # plist and, because the unload came first, left the job down with no valid
    # file to reload from. Validate, then unload, then swap.
    local staged
    staged="$(mktemp "${TMPDIR:-/tmp}/$label.plist.XXXXXX")"
    sed \
        -e "s/{{REBALANCE_DIR}}/$(_rb_sed_escape "$REBALANCE_DIR")/g" \
        -e "s/{{PYTHON}}/$(_rb_sed_escape "$PYTHON_BIN")/g" \
        -e "s/{{HOME}}/$(_rb_sed_escape "$HOME")/g" \
        "$template" > "$staged"

    if ! plutil -lint -- "$staged" > /dev/null; then
        echo "ERROR: rendered plist for $label failed plutil -lint; $dest left untouched" >&2
        rm -f "$staged"
        return 1
    fi

    # Dry run for the caller's preflight: prove every template renders and lints
    # before any job is taken down. Nothing is unloaded, moved or loaded.
    if [ "${RB_RENDER_CHECK:-0}" = "1" ]; then
        rm -f "$staged"
        return 0
    fi

    local gate=0
    _rb_job_precondition "$label" || gate=$?
    if [ "$gate" -ne 0 ]; then
        rm -f "$staged"
        # A job installed earlier whose precondition no longer holds must not
        # stay scheduled behind a SKIPPED report. First installs are untouched.
        if [ -f "$dest" ]; then
            "$LAUNCHCTL_BIN" unload "$dest" 2>/dev/null || true
            if "$LAUNCHCTL_BIN" list "$label" > /dev/null 2>&1; then
                echo "  ERROR: $label is still loaded; kept $dest — run: launchctl remove $label" >&2
                return 1
            fi
            rm -f "$dest"
            echo "  Unloaded and removed the previously installed $label"
        fi
        return "$gate"
    fi

    _rb_warn_dropped_secrets "$dest" "$staged"

    mkdir -p "$REBALANCE_DIR/temp/logs"
    local log_dir
    while IFS= read -r log_dir; do
        [ -n "$log_dir" ] && mkdir -p "$log_dir"
    done < <(_rb_plist_log_dirs "$staged")

    "$LAUNCHCTL_BIN" unload "$dest" 2>/dev/null || true
    mv "$staged" "$dest"
    chmod 644 "$dest"
    echo "  Rendered plist to $dest"

    "$LAUNCHCTL_BIN" load "$dest"

    # Exposed for the caller's uninstall/status hints.
    RB_PLIST_DEST="$dest"

    # Registration can lag the load by a moment — poll briefly before failing.
    local _i
    for _i in 1 2 3 4 5; do
        if "$LAUNCHCTL_BIN" list "$label" > /dev/null 2>&1; then
            echo "  Loaded $label"
            _rb_retire_legacy_labels "$label"
            return
        fi
        sleep 1
    done
    # A job that never registered is not installed: report it as a failure so
    # stack.sh does not print OK (and nothing it replaced is retired).
    echo "  ERROR: $label did not appear in launchctl list after load" >&2
    return 1
}
