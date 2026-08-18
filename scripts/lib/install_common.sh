#!/bin/bash
# rebalance OS — shared install flow for launchd jobs.
#
# Source this from an install_*.sh (after `set -euo pipefail`) and call:
#
#     rb_install_launchd_job <label> [wrapper-relative-path]
#
# e.g. rb_install_launchd_job "com.rebalance-os.vault-sync" "scripts/vault_sync.sh"
#
# One flow for every job:
#   1. chmod +x the wrapper script (when one is named)
#   2. ALWAYS `launchctl unload` first — `launchctl load` fails with an opaque
#      "Input/output error" if the job is already registered, and a grep of
#      `launchctl list` can miss a job that is loaded but momentarily absent
#   3. render scripts/<label>.plist.template into ~/Library/LaunchAgents/,
#      substituting {{REBALANCE_DIR}}, {{PYTHON}}, and {{HOME}}
#   4. `plutil -lint` the rendered plist before loading it
#   5. ensure temp/logs exists, `launchctl load`, verify the label registered
#
# The job inventory, cadences, and scopes live in SCHEDULER.md (the policy
# table); tests/test_scheduler_policy.py enforces that installers stay in sync.

# Test seam. `launchctl unload <path>` resolves the job from the Label INSIDE
# the plist, not from where the file sits, so a fixture plist under a redirected
# HOME still unloads the REAL job (observed, GH-59). Any test that exercises the
# install path must be able to substitute a stub. Unset in normal use.
LAUNCHCTL_BIN="${STACK_LAUNCHCTL_BIN:-${LAUNCHCTL_BIN:-launchctl}}"

RB_INSTALL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(cd "$RB_INSTALL_LIB_DIR/.." && pwd)"
REBALANCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$REBALANCE_DIR/.venv/bin/python"

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

    "$LAUNCHCTL_BIN" unload "$dest" 2>/dev/null || true
    mv "$staged" "$dest"
    chmod 644 "$dest"
    echo "  Rendered plist to $dest"

    mkdir -p "$REBALANCE_DIR/temp/logs"

    "$LAUNCHCTL_BIN" load "$dest"

    # Exposed for the caller's uninstall/status hints.
    RB_PLIST_DEST="$dest"

    # Registration can lag the load by a moment — poll briefly before warning.
    local _i
    for _i in 1 2 3 4 5; do
        if "$LAUNCHCTL_BIN" list "$label" > /dev/null 2>&1; then
            echo "  Loaded $label"
            return 0
        fi
        sleep 1
    done
    echo "  WARNING: $label did not appear in launchctl list after load" >&2
}
