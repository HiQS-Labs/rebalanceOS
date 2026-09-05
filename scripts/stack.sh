#!/bin/bash
# ==============================================================================
# rebalance OS — Unified Stack Orchestrator (scripts/stack.sh)
#
# One control plane for the launchd fleet. Replaces "which of the 12 installer
# scripts do I run?" with a single command that can also answer "is it up?".
#
# Usage:
#   bash scripts/stack.sh up [--force]  # render, lint and load every policy job
#   bash scripts/stack.sh down          # unload every managed job (plists kept)
#   bash scripts/stack.sh restart       # down, then up
#   bash scripts/stack.sh status        # per-job PID / last exit / state
#   bash scripts/stack.sh drift         # how far the runtime trails origin/development (exit 1 if behind)
#   bash scripts/stack.sh doctor        # rebalance doctor (exits with its code)
#   bash scripts/stack.sh verify        # preflight only — changes nothing
#   bash scripts/stack.sh purge         # unload AND delete managed plists
#
# The job list is read from SCHEDULER.md, which is already the enforced source
# of truth (tests/test_scheduler_policy.py). This script deliberately does NOT
# keep its own copy: a second list is a second thing to forget to update, and
# that is exactly how git-pulse-daily-synthesis went missing from the first
# draft of this file.
#
# Anything not in SCHEDULER.md is UNMANAGED. `down` and `purge` refuse to touch
# it, which is what keeps the three preserved 3-Eyes plists safe.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REBALANCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$REBALANCE_DIR/.venv/bin/python"
REBALANCE_CLI="$REBALANCE_DIR/.venv/bin/rebalance"
# STACK_POLICY_DOC is a test seam: it lets the suite drive the parser and the
# preflight with a policy table it controls, without editing the repo's real
# SCHEDULER.md. Unset in normal use.
POLICY_DOC="${STACK_POLICY_DOC:-$REBALANCE_DIR/SCHEDULER.md}"
AGENTS_DIR="$HOME/Library/LaunchAgents"
LABEL_PREFIX="com.rebalance-os."

source "$SCRIPT_DIR/lib/install_common.sh"

log_info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
log_ok()    { echo -e "\033[1;32m[OK]\033[0m    $*"; }
log_warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

# ------------------------------------------------------------------------------
# Policy — the managed job set, read from SCHEDULER.md
# ------------------------------------------------------------------------------
JOB_NAMES=()
JOB_WRAPPERS=()

load_policy() {
    if [ ! -f "$POLICY_DOC" ]; then
        log_error "policy document not found: $POLICY_DOC"
        exit 1
    fi

    # Column 1 is the backticked label suffix, column 3 the backticked wrapper
    # path ("— (python direct)" for jobs launchd invokes without one).
    local parsed
    parsed=$(/usr/bin/sed -n '/^| Job (label suffix) |/,/^$/p' "$POLICY_DOC" \
        | /usr/bin/sed '1,2d' \
        | /usr/bin/awk -F'|' 'NF>3 {
              lbl=$2; wrp=$4;
              gsub(/^[ \t]+|[ \t]+$/,"",lbl); gsub(/^[ \t]+|[ \t]+$/,"",wrp);
              if (lbl !~ /^`[a-z0-9-]+`$/) next;
              gsub(/`/,"",lbl);
              if (wrp ~ /^`[^`]+`$/) { gsub(/`/,"",wrp) } else { wrp="" }
              print lbl "|" wrp;
          }')

    if [ -z "$parsed" ]; then
        log_error "could not read the job policy table from $POLICY_DOC"
        exit 1
    fi

    local line
    while IFS= read -r line; do
        JOB_NAMES+=("${line%%|*}")
        JOB_WRAPPERS+=("${line#*|}")
    done <<< "$parsed"
}

is_managed() {
    local needle="$1" name
    for name in "${JOB_NAMES[@]}"; do
        [ "$name" = "$needle" ] && return 0
    done
    return 1
}

plist_path() { echo "$AGENTS_DIR/${LABEL_PREFIX}$1.plist"; }

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

# Exact third-field match. A substring grep for "health-check" also matches
# "health-check-triage", which silently returns two rows and corrupts the parse.
launchctl_row() {
    local label="${LABEL_PREFIX}$1"
    echo "${LAUNCHCTL_CACHE:-}" | /usr/bin/awk -v want="$label" -F'\t' '$3 == want {print; exit}'
}

# STACK_LAUNCHCTL_BIN is a test seam, and it is load-bearing for safety:
# `launchctl unload <path>` resolves the job from the Label INSIDE the file, not
# from where the file sits. A test writing a fixture plist labelled
# com.rebalance-os.vault-sync into a temp HOME therefore unloads the REAL
# vault-sync. (Observed, GH-59 — the tests took the live job down.) Tests point
# this at a stub; it also lets the suite run on a box with no launchctl.
LAUNCHCTL_BIN="${STACK_LAUNCHCTL_BIN:-launchctl}"

# STACK_LAUNCHCTL_OUTPUT lets the tests feed a fixed `launchctl list` table (and lets
# this script run at all on a non-macOS CI box). Unset in normal use.
refresh_launchctl_cache() {
    if [ -n "${STACK_LAUNCHCTL_OUTPUT:-}" ]; then
        LAUNCHCTL_CACHE="$STACK_LAUNCHCTL_OUTPUT"
    else
        LAUNCHCTL_CACHE="$("$LAUNCHCTL_BIN" list 2>/dev/null || true)"
    fi
}

# ------------------------------------------------------------------------------
# Preflight
# ------------------------------------------------------------------------------
validate_environment() {
    log_info "Validating environment and runtime prerequisites..."
    local errors=0

    if [ ! -x "$PYTHON_BIN" ]; then
        log_error "Virtualenv Python not found at: $PYTHON_BIN"
        log_error "Run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
        errors=$((errors + 1))
    else
        log_ok "Virtualenv Python present ($("$PYTHON_BIN" --version 2>&1))"
    fi

    if [ ! -x "$REBALANCE_CLI" ]; then
        log_warn "rebalance CLI not found at $REBALANCE_CLI — 'stack.sh doctor' will not work"
    fi

    if [ -x "$PYTHON_BIN" ]; then
        local db_res
        db_res=$("$PYTHON_BIN" -c "
from rebalance.paths import resolve_database_path
try:
    p = resolve_database_path()
    print(f'OK:{p}:{p.exists()}')
except Exception as e:
    print(f'ERR:{e}')
" 2>/dev/null || echo "ERR:Failed to execute python")

        if [[ "$db_res" == OK:* ]]; then
            local db_path db_exists
            db_path=$(echo "$db_res" | cut -d: -f2)
            db_exists=$(echo "$db_res" | cut -d: -f3)
            if [ "$db_exists" = "True" ]; then
                log_ok "Resolved database at $db_path"
            else
                log_warn "Database path does not exist yet ($db_path) — created on first sync"
            fi
        else
            log_error "Database resolution failed: $db_res"
            errors=$((errors + 1))
        fi

        local token_res src len
        token_res=$("$PYTHON_BIN" -c "
from rebalance.ingest.config import get_github_token_with_source
token, src = get_github_token_with_source()
print(f'{src}:{len(token) if token else 0}')
" 2>/dev/null || echo "error:0")
        src=$(echo "$token_res" | cut -d: -f1)
        len=$(echo "$token_res" | cut -d: -f2)
        if [ "${len:-0}" -gt 0 ] && [ "$src" != "None" ]; then
            log_ok "GitHub token reachable via '$src'"
        else
            log_warn "No GitHub token reachable. Some background sync jobs will fail."
        fi
    fi

    # Prove every template renders and lints BEFORE `up` unloads anything.
    # Checking mere existence let a malformed template fail mid-apply, with the
    # jobs already processed left down (Codex branch review).
    local bad=0 name i
    for i in "${!JOB_NAMES[@]}"; do
        name="${JOB_NAMES[$i]}"
        if ! out=$(RB_RENDER_CHECK=1 rb_install_launchd_job "${LABEL_PREFIX}$name" "${JOB_WRAPPERS[$i]}" 2>&1); then
            log_error "policy job $name will not render/lint:"
            echo "$out" | /usr/bin/sed 's/^/      /' >&2
            bad=$((bad + 1))
        fi
    done
    if [ "$bad" -eq 0 ]; then
        log_ok "All ${#JOB_NAMES[@]} policy jobs render and lint cleanly"
    else
        errors=$((errors + bad))
    fi

    mkdir -p "$REBALANCE_DIR/temp/logs"
    log_ok "Logs directory ready at $REBALANCE_DIR/temp/logs"

    if [ "$errors" -gt 0 ]; then
        log_error "Preflight validation failed with $errors error(s)."
        return 1
    fi
    return 0
}

# Refuse to silently migrate the whole fleet between checkouts. rb_install_launchd_job
# derives REBALANCE_DIR from its own location, so running `up` from a dev clone
# repoints every plist at that clone — a fleet-wide change with no prompt.
check_target_root() {
    local force="$1" verb="${2:-adopt}"
    log_info "Target root: $REBALANCE_DIR"

    local conflicts=() name root
    for name in "${JOB_NAMES[@]}"; do
        local dest
        dest=$(plist_path "$name")
        [ -f "$dest" ] || continue
        root=$(bound_root "$dest")
        if [ -z "$root" ]; then
            # Unreadable binding. Treating "unknown" as "ours" would let a guard
            # against fleet migration fail open, which is the one direction a
            # safety check must never fail.
            conflicts+=("$name -> (binding unreadable)")
        elif [ "$root" != "$REBALANCE_DIR" ]; then
            conflicts+=("$name -> $root")
        fi
    done

    [ "${#conflicts[@]}" -eq 0 ] && return 0

    if [ "$force" = "1" ]; then
        log_warn "Rebinding ${#conflicts[@]} job(s) to $REBALANCE_DIR (--force)"
        return 0
    fi

    log_error "${#conflicts[@]} installed job(s) are bound to a different checkout:"
    local c
    for c in "${conflicts[@]}"; do echo "    $c" >&2; done
    case "$verb" in
        adopt) log_error "Running 'up' here would move the whole fleet to $REBALANCE_DIR." ;;
        *)     log_error "These jobs belong to another checkout — $verb would stop jobs this clone does not own." ;;
    esac
    log_error "Re-run from the intended checkout, or pass --force to act on them deliberately."
    return 1
}

# ------------------------------------------------------------------------------
# up
# ------------------------------------------------------------------------------
# Preflight is idempotent and remembers it passed, so `restart` can run it
# BEFORE tearing anything down without paying for it twice.
PREFLIGHT_DONE=0
run_preflight() {
    [ "$PREFLIGHT_DONE" = "1" ] && return 0
    # Ownership BEFORE readiness. "Am I allowed to touch this fleet?" does not
    # depend on a virtualenv or on plutil, and answering it second meant the
    # environment check spoke first: on a Linux CI runner `up` reported a missing
    # .venv for a fleet it was never entitled to adopt, and the guard never ran.
    # Wrong message on any machine, and untestable off macOS.
    check_target_root "${1:-0}" || return 1
    echo
    validate_environment || return 1
    PREFLIGHT_DONE=1
    return 0
}

stack_up() {
    local force="${1:-0}"
    echo "================================================================================"
    echo "                rebalance OS — Bootstrapping Background Stack                   "
    echo "================================================================================"

    run_preflight "$force" || exit 1
    echo

    log_info "Installing and loading ${#JOB_NAMES[@]} LaunchAgents..."
    local failed=0 loaded=0 i
    for i in "${!JOB_NAMES[@]}"; do
        local name="${JOB_NAMES[$i]}" wrapper="${JOB_WRAPPERS[$i]}" out
        printf "  • %-28s " "$name"
        if out=$(rb_install_launchd_job "${LABEL_PREFIX}$name" "$wrapper" 2>&1); then
            echo -e "\033[32mOK\033[0m"
            loaded=$((loaded + 1))
        else
            echo -e "\033[31mFAILED\033[0m"
            echo "$out" | /usr/bin/sed 's/^/      /' >&2
            failed=$((failed + 1))
        fi
    done

    echo
    if [ "$failed" -gt 0 ]; then
        log_error "Stack bootstrap encountered $failed failure(s); $loaded job(s) loaded."
        exit 1
    fi
    log_ok "Successfully bootstrapped $loaded job(s)."
    echo
    stack_status
}

# ------------------------------------------------------------------------------
# down / purge
#
# `down` unloads and LEAVES the plist. `restart` is down-then-up, so if `down`
# deleted the files a failed `up` would leave the machine with no agents at all
# — the exact silent outage this script exists to prevent. Deleting is `purge`,
# which you have to ask for by name.
# ------------------------------------------------------------------------------
stack_down() {
    local remove="${1:-0}" force="${2:-0}"
    # The binding guard belongs on the DESTRUCTIVE commands too. It used to run
    # only via `up`/`restart`, so a dev clone would correctly refuse to adopt the
    # runtime's fleet while still being free to unload or delete it (Codex
    # branch review). Unloading someone else's jobs is the worse outcome.
    local verb="teardown"; [ "$remove" = "1" ] && verb="purge"
    check_target_root "$force" "$verb" || exit 1
    echo "================================================================================"
    if [ "$remove" = "1" ]; then
        echo "                rebalance OS — Purging Background Stack                         "
    else
        echo "                rebalance OS — Tearing Down Background Stack                    "
    fi
    echo "================================================================================"

    local count=0 failed=0 name
    refresh_launchctl_cache
    for name in "${JOB_NAMES[@]}"; do
        local dest
        dest=$(plist_path "$name")
        [ -f "$dest" ] || continue
        printf "  • %-28s " "$name"
        local unloaded_ok=0
        "$LAUNCHCTL_BIN" unload "$dest" 2>/dev/null && unloaded_ok=1
        # An unload can fail while the job stays live. Deleting the plist then
        # orphans a running job from its only installation record, and doctor
        # reads it as "never installed" — the job disappears from the health
        # report while still running (Codex branch review).
        if [ "$unloaded_ok" = "0" ] && launchctl_row "$name" >/dev/null && [ -n "$(launchctl_row "$name")" ]; then
            echo -e "\033[31mSTILL LOADED — not purged\033[0m"
            failed=$((failed + 1))
            continue
        fi
        if [ "$remove" = "1" ]; then
            rm -f "$dest"
            echo -e "\033[33mPURGED\033[0m"
        else
            echo -e "\033[32mUNLOADED\033[0m"
        fi
        count=$((count + 1))
    done

    echo
    if [ "$remove" = "1" ]; then
        log_ok "Purge complete: $count managed job(s) unloaded and removed."
    else
        log_ok "Teardown complete: $count managed job(s) unloaded (plists kept)."
    fi
    log_info "Unmanaged ${LABEL_PREFIX}* plists were not touched."
    if [ "$failed" -gt 0 ]; then
        log_error "$failed job(s) could not be unloaded and were left installed."
        return 1
    fi
}

# ------------------------------------------------------------------------------
# status
# ------------------------------------------------------------------------------
# Runtime drift: how far the deployed checkout ($REBALANCE_DIR) trails
# origin/development. The fleet runs from THAT folder, not from wherever a PR
# was merged; a merge is not a deploy until someone pulls it there (AGENTS.md
# § "Deploy runtime folder", SOP.md § 7). Returns 1 when behind so a git hook
# or a health job can act on it. Never blocks: an unreadable or offline
# runtime reports "unknown" and returns 0, because a drift check that fails
# closed would turn every flaky network into a red `status`.
runtime_drift() {
    local behind head_desc
    # Git hooks export GIT_DIR/GIT_WORK_TREE. With those set, `git -C <runtime>`
    # ignores -C for repository discovery and quietly measures the DEV checkout
    # instead — the first probe of the post-merge hook reported "up to date" while
    # the runtime was 51 commits behind. Clear them so the runtime is always what
    # gets measured, whoever calls this.
    unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
    if ! git -C "$REBALANCE_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "RUNTIME: $REBALANCE_DIR is not a git checkout — drift unknown"
        return 0
    fi
    if ! git -C "$REBALANCE_DIR" fetch --quiet origin development 2>/dev/null; then
        echo "RUNTIME: fetch failed — drift unknown (offline, or no origin/development)"
        return 0
    fi
    behind=$(git -C "$REBALANCE_DIR" rev-list --count HEAD..origin/development)
    head_desc=$(git -C "$REBALANCE_DIR" log -1 --format='%h from %cs' HEAD)
    if [ "$behind" -eq 0 ]; then
        echo "RUNTIME: up to date with origin/development ($head_desc)"
        return 0
    fi
    echo "RUNTIME: $behind commit(s) BEHIND origin/development — fleet is running $head_desc"
    echo "         deploy: git -C \"$REBALANCE_DIR\" pull --ff-only origin development"
    return 1
}

stack_status() {
    refresh_launchctl_cache
    echo "================================================================================"
    echo "                     rebalance OS — Stack Status                                "
    echo "================================================================================"
    echo "Target root: $REBALANCE_DIR"
    echo
    printf "%-28s %-8s %-10s %-14s %s\n" "JOB" "PID" "LAST EXIT" "STATE" "BOUND TO"
    echo "--------------------------------------------------------------------------------"

    local unloaded=0 broken=0 name
    for name in "${JOB_NAMES[@]}"; do
        local dest row pid status state color root note
        dest=$(plist_path "$name")
        row=$(launchctl_row "$name")
        root=$(bound_root "$dest")
        note=""
        [ -n "$root" ] && [ "$root" != "$REBALANCE_DIR" ] && note="$root"

        if [ -z "$row" ]; then
            if [ -f "$dest" ]; then
                state="UNLOADED"; color="\033[1;33m"; unloaded=$((unloaded + 1))
            else
                state="NOT INSTALLED"; color="\033[90m"
            fi
            printf "%-28s %-8s %-10s ${color}%-14s\033[0m %s\n" "$name" "-" "-" "$state" "$note"
            continue
        fi

        pid=$(echo "$row" | /usr/bin/awk -F'\t' '{print $1}')
        status=$(echo "$row" | /usr/bin/awk -F'\t' '{print $2}')
        if [ "$pid" != "-" ]; then
            state="RUNNING"; color="\033[1;32m"
        elif [ "$status" != "0" ] && [ "$status" != "-" ]; then
            state="ERROR ($status)"; color="\033[1;31m"; broken=$((broken + 1))
        else
            state="IDLE (OK)"; color="\033[32m"
        fi
        printf "%-28s %-8s %-10s ${color}%-14s\033[0m %s\n" "$name" "$pid" "$status" "$state" "$note"
    done

    echo "--------------------------------------------------------------------------------"
    printf "managed: %d   unloaded: %d   failing: %d\n" "${#JOB_NAMES[@]}" "$unloaded" "$broken"

    # Unmanaged agents are shown, never hidden and never touched. The 3-Eyes
    # plists live here: deferred, preserved, out of this script's reach.
    local unmanaged=() f base suffix
    for f in "$AGENTS_DIR/${LABEL_PREFIX}"*.plist; do
        [ -f "$f" ] || continue
        base=$(basename "$f" .plist)
        suffix="${base#$LABEL_PREFIX}"
        is_managed "$suffix" || unmanaged+=("$suffix")
    done

    if [ "${#unmanaged[@]}" -gt 0 ]; then
        echo
        echo "Unmanaged ${LABEL_PREFIX}* plists (not in SCHEDULER.md — never loaded, unloaded or"
        echo "deleted by this script):"
        for suffix in "${unmanaged[@]}"; do
            local row state
            row=$(launchctl_row "$suffix")
            [ -n "$row" ] && state="loaded" || state="not loaded"
            printf "  · %-40s %s\n" "$suffix" "$state"
        done
    fi
    echo
    runtime_drift || true   # informational here; `stack.sh drift` carries the exit code
    echo "================================================================================"
}

# ------------------------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------------------------
load_policy
refresh_launchctl_cache

cmd="${1:-status}"
shift || true
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        *) log_error "unknown option: $arg"; exit 2 ;;
    esac
done

case "$cmd" in
    up|boot|start)  stack_up "$FORCE" ;;
    down|stop)      stack_down 0 "$FORCE" ;;
    purge)          stack_down 1 "$FORCE" ;;
    restart|reload)
        # Preflight FIRST. `restart` used to unload everything and only then
        # discover that `up` could not run, leaving the machine with no agents
        # at all — the exact silent outage this script exists to prevent.
        run_preflight "$FORCE" || exit 1
        echo
        stack_down 0 1   # preflight already passed the guard above
        echo
        stack_up "$FORCE"
        ;;
    status|ps)      stack_status ;;
    drift)          runtime_drift ;;
    doctor)
        if [ ! -x "$REBALANCE_CLI" ]; then
            log_error "rebalance CLI not found at $REBALANCE_CLI"
            log_error "Run: .venv/bin/pip install -e '.[dev]'"
            exit 1
        fi
        exec "$REBALANCE_CLI" doctor
        ;;
    verify|test)    validate_environment ;;
    *)
        echo "Usage: $0 {up [--force]|down|restart|status|drift|doctor|verify|purge}"
        exit 2
        ;;
esac
