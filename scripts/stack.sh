#!/bin/bash
# ==============================================================================
# rebalance OS — Unified Stack Orchestrator (scripts/stack.sh)
#
# Single deterministic control plane for the entire Rebalance OS launchd fleet.
# Replaces fragmented per-job install scripts with an atomic bootstrap & monitor.
#
# Usage:
#   bash scripts/stack.sh up       # Validate config, render plists, lint, and load all jobs
#   bash scripts/stack.sh down     # Gracefully unload and purge all launchd agents
#   bash scripts/stack.sh restart  # Atomic reload of all agents
#   bash scripts/stack.sh status   # Formatted tabular status, PIDs, and exit codes
#   bash scripts/stack.sh doctor   # Run full system health check
#   bash scripts/stack.sh test     # Dry-run validation of plists and environment
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REBALANCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$REBALANCE_DIR/.venv/bin/python"

source "$SCRIPT_DIR/lib/install_common.sh"

# Canonical list of core jobs managed by the stack:
# Format: "label|wrapper_rel_path|required_flag"
JOBS=(
    "com.rebalance-os.pulse-server|scripts/pulse_server.sh|required"
    "com.rebalance-os.daily-sync|scripts/daily_sync.sh|required"
    "com.rebalance-os.github-sync|scripts/github_sync.sh|required"
    "com.rebalance-os.vault-sync|scripts/vault_sync.sh|required"
    "com.rebalance-os.pulse-sync|scripts/pulse_sync.sh|required"
    "com.rebalance-os.pulse-web-sync|scripts/pulse_web_sync.sh|required"
    "com.rebalance-os.pulse-warning-watch||required"
    "com.rebalance-os.health-check||required"
    "com.rebalance-os.health-check-triage||optional"
    "com.rebalance-os.obsidian-daily-sync|utils/obsidian_daily_sync.sh|optional"
    "com.rebalance-os.obsidian-rollover|utils/obsidian_rollover.sh|optional"
)

log_info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
log_ok()    { echo -e "\033[1;32m[OK]\033[0m    $*"; }
log_warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

# ------------------------------------------------------------------------------
# Preflight Validation
# ------------------------------------------------------------------------------
validate_environment() {
    log_info "Validating environment and runtime prerequisites..."
    local errors=0

    # 1. Virtualenv Python
    if [ ! -x "$PYTHON_BIN" ]; then
        log_error "Virtualenv Python not found at: $PYTHON_BIN"
        log_error "Run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
        errors=$((errors + 1))
    else
        log_ok "Virtualenv Python present ($("$PYTHON_BIN" --version 2>&1))"
    fi

    # 2. Database resolution
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
            local db_path=$(echo "$db_res" | cut -d: -f2)
            local db_exists=$(echo "$db_res" | cut -d: -f3)
            if [ "$db_exists" = "True" ]; then
                log_ok "Resolved database at $db_path"
            else
                log_warn "Resolved database path does not exist yet ($db_path) — will be initialized on first sync"
            fi
        else
            log_error "Database resolution failed: $db_res"
            errors=$((errors + 1))
        fi
    fi

    # 3. GitHub Token reachability
    if [ -x "$PYTHON_BIN" ]; then
        local token_res
        token_res=$("$PYTHON_BIN" -c "
from rebalance.ingest.config import get_github_token_with_source
token, src = get_github_token_with_source()
print(f'{src}:{len(token) if token else 0}')
" 2>/dev/null || echo "error:0")
        local src=$(echo "$token_res" | cut -d: -f1)
        local len=$(echo "$token_res" | cut -d: -f2)
        if [ "$len" -gt 0 ] && [ "$src" != "None" ]; then
            log_ok "GitHub token reachable via '$src'"
        else
            log_warn "No GitHub token reachable. Some background sync jobs will fail."
        fi
    fi

    # 4. Logs directory
    mkdir -p "$REBALANCE_DIR/temp/logs"
    log_ok "Logs directory ready at $REBALANCE_DIR/temp/logs"

    if [ "$errors" -gt 0 ]; then
        log_error "Preflight validation failed with $errors error(s)."
        return 1
    fi
    return 0
}

# ------------------------------------------------------------------------------
# Boot / Up Command
# ------------------------------------------------------------------------------
stack_up() {
    echo "================================================================================"
    echo "                rebalance OS — Bootstrapping Background Stack                   "
    echo "================================================================================"
    
    validate_environment || exit 1
    echo

    log_info "Installing and loading all LaunchAgents..."
    local failed=0
    local loaded=0

    for item in "${JOBS[@]}"; do
        local label=$(echo "$item" | cut -d'|' -f1)
        local wrapper=$(echo "$item" | cut -d'|' -f2)
        local req=$(echo "$item" | cut -d'|' -f3)
        local short_name=${label#"com.rebalance-os."}

        echo -n "  • Loading $short_name... "
        if rb_install_launchd_job "$label" "$wrapper" > /dev/null 2>&1; then
            echo -e "\033[32mOK\033[0m"
            loaded=$((loaded + 1))
        else
            if [ "$req" = "required" ]; then
                echo -e "\033[31mFAILED\033[0m"
                log_error "Failed to load required job: $label"
                failed=$((failed + 1))
            else
                echo -e "\033[33mSKIPPED (optional)\033[0m"
            fi
        fi
    done

    echo
    if [ "$failed" -gt 0 ]; then
        log_error "Stack bootstrap encountered $failed failure(s)."
        exit 1
    fi

    log_ok "Successfully bootstrapped $loaded job(s)."
    echo
    stack_status
}

# ------------------------------------------------------------------------------
# Teardown / Down Command
# ------------------------------------------------------------------------------
stack_down() {
    echo "================================================================================"
    echo "                rebalance OS — Tearing Down Background Stack                    "
    echo "================================================================================"
    local unloaded=0

    for item in "${JOBS[@]}"; do
        local label=$(echo "$item" | cut -d'|' -f1)
        local dest="$HOME/Library/LaunchAgents/$label.plist"
        local short_name=${label#"com.rebalance-os."}

        if [ -f "$dest" ]; then
            echo -n "  • Unloading $short_name... "
            launchctl unload "$dest" 2>/dev/null || true
            rm -f "$dest"
            echo -e "\033[32mUNLOADED\033[0m"
            unloaded=$((unloaded + 1))
        fi
    done

    echo
    log_ok "Teardown complete: $unloaded job(s) removed from launchd."
}

# ------------------------------------------------------------------------------
# Status Command
# ------------------------------------------------------------------------------
stack_status() {
    echo "================================================================================"
    echo "                     rebalance OS — Stack Status                                "
    echo "================================================================================"
    printf "%-26s %-12s %-10s %-10s %-12s\n" "JOB" "TYPE" "PID" "LAST EXIT" "STATE"
    echo "--------------------------------------------------------------------------------"

    local launch_list
    launch_list=$(launchctl list 2>/dev/null || true)

    for item in "${JOBS[@]}"; do
        local label=$(echo "$item" | cut -d'|' -f1)
        local short_name=${label#"com.rebalance-os."}
        local req=$(echo "$item" | cut -d'|' -f3)

        local line
        line=$(echo "$launch_list" | grep "$label" || true)

        if [ -z "$line" ]; then
            if [ -f "$HOME/Library/LaunchAgents/$label.plist" ]; then
                printf "%-26s %-12s %-10s %-10s \033[33m%-12s\033[0m\n" "$short_name" "$req" "-" "-" "UNLOADED"
            else
                printf "%-26s %-12s %-10s %-10s \033[90m%-12s\033[0m\n" "$short_name" "$req" "-" "-" "NOT INSTALLED"
            fi
        else
            local pid=$(echo "$line" | awk '{print $1}')
            local status=$(echo "$line" | awk '{print $2}')
            local state="IDLE (OK)"
            local color="\033[32m"

            if [ "$pid" != "-" ]; then
                state="RUNNING"
                color="\033[1;32m"
            elif [ "$status" != "0" ] && [ "$status" != "-" ]; then
                state="ERROR ($status)"
                color="\033[1;31m"
            fi

            printf "%-26s %-12s %-10s %-10s ${color}%-12s\033[0m\n" "$short_name" "$req" "$pid" "$status" "$state"
        fi
    done
    echo "================================================================================"
}

# ------------------------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------------------------
cmd="${1:-status}"

case "$cmd" in
    up|boot|start)
        stack_up
        ;;
    down|stop)
        stack_down
        ;;
    restart|reload)
        stack_down
        echo
        stack_up
        ;;
    status|ps)
        stack_status
        ;;
    doctor)
        exec "$PYTHON_BIN" -m rebalance.doctor
        ;;
    test|verify)
        validate_environment
        ;;
    *)
        echo "Usage: $0 {up|down|restart|status|doctor|verify}"
        exit 1
        ;;
esac
