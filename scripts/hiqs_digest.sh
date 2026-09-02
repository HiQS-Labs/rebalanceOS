#!/bin/bash
# rebalance OS — twice-daily progress digest (GH-142)
#
# Runs at 13:05 and 17:05 local time via launchd (com.rebalance-os.hiqs-digest).
# Collects today's signal from rebalance.db, synthesizes it with Gemini, and
# git-pushes one markdown file into the shared pulse repo. AEGIS Sleuth's
# snapshot-relay polls that directory and posts new files to Slack — this job
# never talks to Slack itself. Plan of record: AEGIS-Sleuth-Slackbot#157.
#
# WHY A WRAPPER (not launchd -> python directly, unlike health-check-triage):
# the health collector shells out to `rebalance doctor`, which reads the vault
# under ~/Documents. That folder is TCC-protected and a directly-launched
# interpreter is denied (Operation not permitted). Running through /bin/bash
# inherits the Full Disk Access grant the other rebalance launchd jobs already
# hold, so no new Full Disk Access entry is needed. Same reason as
# utils/daily_synthesis.sh and utils/obsidian_rollover.sh.
#
# Freshness policy: read-only derived stage — summarizes whatever the ingest
# jobs (daily-sync, github-sync, vault embeddings) last wrote. It never
# refreshes sources, so a stale digest means an upstream ingest job is behind,
# not that this one failed.
#
# Observability: the digest stamps its own generated_at and the Slack post
# renders it, so a launchd catch-up run after a sleep announces its own
# lateness in the channel. There is deliberately no watchdog — see #157.
#
# LLM cost: 2 Gemini calls per day. Set HIQS_DIGEST_LLM_DISABLE=1 in the
# RENDERED plist to stop them without a code change.
#
# Policy: SCHEDULER.md (job com.rebalance-os.hiqs-digest).

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib/scheduler_common.sh"
rb_job_init "hiqs-digest" 14

# Don't print a slot here — the slot label is the Python script's to decide
# (it defaults to local HHMM but --slot overrides it), and a wrapper that
# guesses it logs a different value than the filename actually uses.
log "=== rebalance hiqs-digest starting ${*:+(args: $*)} ==="

# tee, not >>: --dry-run print()s the rendered digest so the operator can read it before
# publishing, and the installer tells them to run exactly that through this wrapper. With a
# plain redirect they saw only the two timestamped lines here and concluded nothing ran.
# Under launchd stdout goes to the plist's StandardOutPath, so the log still gets it twice.
#
# set +e around the pipeline, and PIPESTATUS read on the very next line: with `pipefail`
# and `errexit` a non-zero python would abort the script before the log line below, and
# PIPESTATUS is reset by the NEXT command to run — including a bare `[ ... ]` test — so it
# has to be captured before anything else touches it.
set +e
"$PYTHON" utils/hiqs_digest.py "$@" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE="${PIPESTATUS[0]}"
set -e

if [ "$EXIT_CODE" -eq 0 ]; then
    log "=== hiqs-digest complete ==="
else
    # Exit 1 is also how the script reports "synthesis unavailable, nothing
    # written" — a deliberate skip, not a crash. The log line above it in
    # $LOG_FILE says which. Both are surfaced as job_failed so a silent
    # no-publish streak is visible in temp/logs/auth_activity.jsonl.
    log "=== hiqs-digest FAILED or SKIPPED (exit $EXIT_CODE) — see $LOG_FILE ==="
fi

rb_trim_logs

exit $EXIT_CODE
