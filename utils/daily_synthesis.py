#!/usr/bin/env python3
"""Daily vault synthesis — merged 18:20 launchd consumer (GH-74).

Replaces the separately-scheduled ``obsidian_daily_sync.py`` (GH-112, 18:20) and
``git_pulse_daily_synthesis.py`` (GH-114, 18:30). Both wrote sentinel-bracketed
blocks to the SAME file ("0. Today's Notes.md"), and the second had to fire
after the first purely so its block landed below — an ordering dependency
enforced only by two independent launchd fire times (SCHEDULER.md), which a
sleep/wake catch-up could invert. Running both syntheses in one process makes
the order a property of the code, not the scheduler.

Design contract (unchanged from both predecessors — see their original GH-112 /
GH-114 docs for the full history):
  * Pulse summary   — Gemini-only synthesis of collect_pulse_snapshot() STRUCTURED
                       output. Gemini unavailable/fails -> SKIP that block, write
                       NOTHING for it. No Qwen fallback ever reaches the vault.
  * Git Pulse summary — shells out to experimental/git-pulse/view.sh --today.
                       Zero-row activity synthesizes a fixed fallback string
                       rather than skipping (FALLBACK_SUMMARY); a no-clobber
                       guard stops a transient zero-row rerun from overwriting
                       an earlier real summary the same day. Optional second
                       destination: a growing, git-committed CLIO log, decoupled
                       from vault_ready() so it works with no Obsidian vault at
                       all (git_pulse_clio_enabled, see rebalance.ingest.config).
  * Vault target    — derived from obsidian_daily_rollover.TODAY_FILE (never
                       hardcoded).
  * Block markers   — each summary keeps its OWN markers/heading, unchanged from
                       its predecessor script, so an existing vault file with
                       either block already in it continues to upsert in place:
                         pulse:     <!-- AI Daily Summary Start/End -->
                         git pulse: <!-- Git Pulse Daily Summary Start/End -->
  * Ordering        — the pulse block is upserted first, then the git-pulse
                       block, in one read-modify-write of TODAY_FILE. The git
                       pulse block always lands below the pulse block.
  * Late-run rule   — a post-midnight launchd catch-up (local hour < 18, after
                       the 00:00 rollover moved Today->Yesterday) SKIPS entirely.

Requires the rebalance venv (imports rebalance.*). Run via the bash wrapper
utils/daily_synthesis.sh so launchd inherits Full Disk Access.

Usage:
  daily_synthesis.py            # do the sync (the 18:20 job)
  daily_synthesis.py --dry-run  # print the blocks that would be written; no write
  daily_synthesis.py --status   # show vault/CLIO/block state, then exit
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# utils/ is not a package — add it so we reuse the rollover module's vault config
# (TODAY_FILE / vault_ready) rather than hardcoding the vault path a second time.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from obsidian_daily_rollover import TODAY_FILE, vault_ready  # noqa: E402

# The 18:20 job's valid window is same-day 18:00 -> 23:59. A launchd catch-up
# that wakes the Mac after midnight fires in the small hours (local hour
# 0-17); by then the 00:00 rollover has moved Today -> Yesterday, so appending
# would pollute the fresh day. Below this floor, skip.
RUN_HOUR_FLOOR = 18

# Structured job-event logging — optional; silent if rebalance isn't importable.
try:
    from rebalance.ingest.auth_log import (
        log_job_completed,
        log_job_failed,
        log_job_started as _ljs,
    )

    _JOB_LOG = True
except ImportError:
    _JOB_LOG = False

JOB_NAME = "daily-synthesis"


def _log_job(event: str, elapsed: float | None = None, exit_code: int | None = None) -> None:
    if not _JOB_LOG:
        return
    if event == "started":
        _ljs(JOB_NAME)
    elif event == "completed":
        log_job_completed(JOB_NAME, elapsed)
    elif event == "failed":
        log_job_failed(JOB_NAME, exit_code or 1, elapsed)


def log(msg: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {msg}", flush=True)


def is_late_run(now: datetime) -> bool:
    """True if this fired as a post-midnight launchd catch-up (past the rollover)."""
    return now.hour < RUN_HOUR_FLOOR


# --- Shared sentinel-block logic (unit-tested, no I/O) ------------------------
def _format_time(dt: datetime) -> str:
    """12-hour clock like '6:00 PM' (no leading zero) for the reminder line."""
    return dt.strftime("%I:%M %p").lstrip("0")


def build_marked_block(heading: str, marker_start: str, marker_end: str, summary: str, generated_at: datetime) -> str:
    """A sentinel-bracketed block: heading, auto-generated stamp, then the summary."""
    stamp = f"*Auto-generated at {_format_time(generated_at)}.*"
    return f"{marker_start}\n{heading}\n{stamp}\n\n{summary.strip()}\n{marker_end}\n"


def upsert_marked_block(content: str, block: str, marker_start: str, marker_end: str) -> str:
    """Replace an existing sentinel block in-place, else append one at the bottom.

    Idempotent: rerunning always yields exactly ONE block with the markers intact
    and every byte of surrounding human markdown untouched. Uses first-start /
    last-end so an accidental duplicate pair collapses back to a single block.
    An empty ``content`` (a brand-new file, e.g. the CLIO log's first run)
    returns the block with no leading blank lines.
    """
    if marker_start in content and marker_end in content:
        before = content.split(marker_start, 1)[0]
        # Strip leading blank lines the old block left behind so trailing newlines
        # don't accumulate one-per-run (breaks the byte-stable fixed point). The
        # block already ends in "\n"; re-separate only if real content follows it.
        tail = content.rsplit(marker_end, 1)[1].lstrip("\n")
        return before + block + (f"\n{tail}" if tail else "")
    if not content:
        return block
    # Append at the bottom, separated from prior content by exactly one blank line.
    body = content if content.endswith("\n") else content + "\n"
    if not body.endswith("\n\n"):
        body += "\n"
    return body + block


def _extract_block_text(content: str, start_marker: str, end_marker: str) -> str | None:
    """Return the text between start/end markers in content, or None if either
    marker is absent (i.e. no block exists yet at this location)."""
    if start_marker not in content or end_marker not in content:
        return None
    return content.split(start_marker, 1)[1].split(end_marker, 1)[0]


# ===============================================================================
# Pulse summary — GH-112 (structured pulse snapshot -> Gemini -> vault block)
# ===============================================================================

PULSE_MARKER_START = "<!-- AI Daily Summary Start -->"
PULSE_MARKER_END = "<!-- AI Daily Summary End -->"
PULSE_BLOCK_HEADING = "## 🤖 AI Daily Summary"


def build_pulse_block(summary: str, generated_at: datetime) -> str:
    return build_marked_block(PULSE_BLOCK_HEADING, PULSE_MARKER_START, PULSE_MARKER_END, summary, generated_at)


def upsert_pulse_block(content: str, summary: str, generated_at: datetime) -> str:
    return upsert_marked_block(content, build_pulse_block(summary, generated_at), PULSE_MARKER_START, PULSE_MARKER_END)


PULSE_PROMPT_TEMPLATE = """You are an AI assistant summarizing the daily activity of a software engineer.
Based on the following structured snapshot of today's activity, write a concise daily summary.
Keep it casual but informative. Group by project or theme where possible. Do NOT hallucinate data.
If activity is sparse, say so briefly rather than padding.

Activity data:
{data}
"""


def collect_pulse_activity() -> dict:
    """Today's structured pulse activity as a plain dict (never rendered markdown)."""
    from dataclasses import asdict

    from rebalance.ingest.pulse import collect_pulse_snapshot
    from rebalance.ingest.config import get_pulse_config, get_github_token

    default_db = Path(os.environ["HOME"]) / "Library/Application Support/rebalance-os/rebalance.db"
    db_path = Path(os.environ.get("REBALANCE_DB", default_db))
    config = get_pulse_config()
    snapshot = collect_pulse_snapshot(
        database_path=db_path,
        github_login=config["github_login"],
        slack_user_id=config.get("slack_user_id"),
        timezone_name=config.get("pulse_timezone", "UTC"),
        github_token=get_github_token(),
    )
    return asdict(snapshot.today)


def synthesize_pulse(activity: dict) -> str | None:
    """Gemini-only synthesis. Returns text, or None if Gemini is unavailable/fails.

    NO Qwen fallback — a fallback-quality summary must never reach the vault, so
    both "no key" and "call failed" return None and the caller writes nothing.
    """
    from rebalance.ingest.config import get_gemini_api_key
    from rebalance.ingest.querier import _synthesize_gemini

    key = get_gemini_api_key()
    if not key:
        log("SKIP pulse: no Gemini API key available — refusing to write a fallback summary.")
        return None
    prompt = PULSE_PROMPT_TEMPLATE.format(data=json.dumps(activity, indent=2, default=str))
    try:
        return _synthesize_gemini(prompt, api_key=key, thinking_budget=0, max_tokens=2048)
    except Exception as e:  # noqa: BLE001 — any failure means skip, never fall back
        log(f"SKIP pulse: Gemini synthesis failed ({e}) — no fallback written to vault.")
        return None


# ===============================================================================
# Git Pulse summary — GH-114 (view.sh --today TSV -> Gemini -> vault block + CLIO)
# ===============================================================================

GIT_PULSE_MARKER_START = "<!-- Git Pulse Daily Summary Start -->"
GIT_PULSE_MARKER_END = "<!-- Git Pulse Daily Summary End -->"
GIT_PULSE_BLOCK_HEADING = "## 📊 Git Pulse Daily Summary"

# The zero-row fallback synthesize_git_pulse() returns. Named so the no-clobber
# guard below can recognize "the summary about to be written is itself a
# fallback" without string-literal duplication.
FALLBACK_SUMMARY = "No git activity found today."

# CLIO log: one block per calendar day, so the markers are date-scoped — this is
# what lets today's rerun replace only today's block while every prior day's
# block in the same growing file stays untouched.
CLIO_BLOCK_HEADING = "Git Pulse Daily Summary"

GIT_PULSE_PROMPT_TEMPLATE = """You are an AI assistant summarizing the git commit activity of a software engineer for the day.
Based on the following structured snapshot of today's git pulse activity, write a concise daily summary.
Keep it casual but informative. Group by repository or theme where possible. Do NOT hallucinate data.
If activity is sparse, say so briefly rather than padding.

Activity data:
{data}
"""


def build_git_pulse_block(summary: str, generated_at: datetime) -> str:
    return build_marked_block(
        GIT_PULSE_BLOCK_HEADING, GIT_PULSE_MARKER_START, GIT_PULSE_MARKER_END, summary, generated_at
    )


def upsert_git_pulse_block(content: str, summary: str, generated_at: datetime) -> str:
    return upsert_marked_block(
        content, build_git_pulse_block(summary, generated_at), GIT_PULSE_MARKER_START, GIT_PULSE_MARKER_END
    )


def _extract_full_block(content: str, marker_start: str, marker_end: str) -> str | None:
    """The full sentinel block (markers + body) verbatim, including its
    trailing newline, or None if either marker is absent."""
    if marker_start not in content or marker_end not in content:
        return None
    start = content.index(marker_start)
    end = content.index(marker_end, start) + len(marker_end)
    if content[end : end + 1] == "\n":
        end += 1
    return content[start:end]


def _strip_marked_block(content: str, marker_start: str, marker_end: str) -> str:
    """Remove an existing sentinel block (markers + body) entirely. Companion
    to upsert_marked_block's in-place replace, used only to normalize a
    pre-existing block ordering (see normalize_block_order) before the
    extracted block text is re-appended in the correct position."""
    if marker_start not in content or marker_end not in content:
        return content
    before = content.split(marker_start, 1)[0].rstrip("\n")
    tail = content.rsplit(marker_end, 1)[1].lstrip("\n")
    if before and tail:
        return f"{before}\n\n{tail}"
    return before or tail


def normalize_block_order(content: str) -> str:
    """If both vault blocks already exist but the git-pulse block sits ABOVE
    the pulse block — a stale ordering inherited from the old two-launchd-job
    system, or the exact sleep/wake inversion GH-74 exists to eliminate —
    move the EXISTING block bytes (verbatim; no fabricated new timestamp) so
    they land pulse-then-git-pulse, the same fixed point a brand-new day's
    note converges to. upsert_marked_block only ever replaces a block IN
    PLACE, so without this pass an already-reversed pair stays reversed
    forever, and it must actively relocate them (not merely delete) since a
    run that generates no new summary content would otherwise never
    re-append what it stripped (Codex GH-74 QA r1 Blocker 1). No-op when
    either block is absent or they're already in order."""
    pulse_at = content.find(PULSE_MARKER_START)
    git_pulse_at = content.find(GIT_PULSE_MARKER_START)
    if pulse_at == -1 or git_pulse_at == -1 or git_pulse_at >= pulse_at:
        return content
    pulse_block = _extract_full_block(content, PULSE_MARKER_START, PULSE_MARKER_END)
    git_pulse_block = _extract_full_block(content, GIT_PULSE_MARKER_START, GIT_PULSE_MARKER_END)
    # Both markers were just confirmed present above (pulse_at/git_pulse_at != -1).
    assert pulse_block is not None and git_pulse_block is not None
    stripped = _strip_marked_block(content, PULSE_MARKER_START, PULSE_MARKER_END)
    stripped = _strip_marked_block(stripped, GIT_PULSE_MARKER_START, GIT_PULSE_MARKER_END)
    # Neither marker remains in `stripped`, so both calls take the tested
    # append-at-bottom path in upsert_marked_block — pulse first, git-pulse second.
    fixed = upsert_marked_block(stripped, pulse_block, PULSE_MARKER_START, PULSE_MARKER_END)
    return upsert_marked_block(fixed, git_pulse_block, GIT_PULSE_MARKER_START, GIT_PULSE_MARKER_END)


def _clio_markers(date_str: str) -> tuple[str, str]:
    return (
        f"<!-- Git Pulse Daily Summary {date_str} Start -->",
        f"<!-- Git Pulse Daily Summary {date_str} End -->",
    )


def build_clio_block(summary: str, generated_at: datetime) -> str:
    """The dated, sentinel-bracketed block appended to the CLIO log file."""
    date_str = generated_at.strftime("%Y-%m-%d")
    start, end = _clio_markers(date_str)
    heading = f"## {date_str} — {CLIO_BLOCK_HEADING}"
    return build_marked_block(heading, start, end, summary, generated_at)


def upsert_clio_block(content: str, summary: str, generated_at: datetime) -> str:
    """Upsert *today's* dated block into a growing multi-day log.

    Idempotent per day: rerunning the same day replaces only that day's block.
    Every other day's block already in the file is left byte-for-byte intact,
    so the file accumulates one block per day instead of being overwritten.
    """
    date_str = generated_at.strftime("%Y-%m-%d")
    start, end = _clio_markers(date_str)
    block = build_clio_block(summary, generated_at)
    return upsert_marked_block(content, block, start, end)


def _would_clobber_real_summary(existing_block_text: str | None, new_summary: str) -> bool:
    """True only when writing new_summary would replace an earlier real summary
    with the zero-row fallback: new_summary IS the fallback, a block already
    exists, and that existing block is non-empty and is not itself the
    fallback."""
    if new_summary != FALLBACK_SUMMARY:
        return False
    if existing_block_text is None:
        return False
    stripped = existing_block_text.strip()
    if not stripped:
        return False
    if FALLBACK_SUMMARY in stripped:
        return False
    return True


def collect_git_pulse_activity() -> tuple[str | None, int]:
    """Shells out to view.sh --today and returns the TSV stdout string and exit code."""
    repo_root = Path(__file__).resolve().parent.parent
    view_script = repo_root / "experimental" / "git-pulse" / "view.sh"

    if not view_script.exists():
        log(f"SKIP git-pulse: view.sh not found at {view_script}")
        return None, 1

    cmd = [str(view_script), "--today"]

    try:
        env = os.environ.copy()
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
        if result.returncode != 0:
            log(f"SKIP git-pulse: view.sh failed with exit code {result.returncode}. Is config missing?")
            if result.stderr:
                log(f"view.sh stderr: {result.stderr.strip()}")
            return None, result.returncode
        return result.stdout.strip(), 0
    except Exception as e:
        log(f"SKIP git-pulse: failed to execute view.sh: {e}")
        return None, 1


def synthesize_git_pulse(activity_tsv: str) -> str | None:
    from rebalance.ingest.config import get_gemini_api_key
    from rebalance.ingest.querier import _synthesize_gemini

    lines = activity_tsv.splitlines()
    if len(lines) <= 1:
        # Zero-row case (only headers or empty)
        return FALLBACK_SUMMARY

    key = get_gemini_api_key()
    if not key:
        log("SKIP git-pulse: no Gemini API key available — refusing to write a fallback summary.")
        return None

    prompt = GIT_PULSE_PROMPT_TEMPLATE.format(data=activity_tsv)
    try:
        return _synthesize_gemini(prompt, api_key=key, thinking_budget=0, max_tokens=2048)
    except Exception as e:
        log(f"SKIP git-pulse: Gemini synthesis failed ({e}) — no fallback written to vault.")
        return None


def sync_to_clio(summary: str, now: datetime, dry_run: bool = False) -> dict:
    """Upsert today's block into pulse_target_path/<subdir>/<filename>, commit+push.

    Opt-in via git_pulse_clio_enabled (see rebalance.ingest.config.get_pulse_config).
    Does NOT depend on vault_ready() — this is the path for users running Git Pulse
    Sync without an Obsidian vault configured at all. Reuses pulse.py's
    _commit_and_push_if_changed so this gets the same write/commit/push + push-repair
    behavior as the primary live-pulse.md writer, rather than a second implementation.
    """
    from rebalance.ingest.config import get_pulse_config
    from rebalance.ingest.pulse import _commit_and_push_if_changed

    cfg = get_pulse_config()
    if not cfg.get("git_pulse_clio_enabled"):
        return {"enabled": False}

    target_path = cfg.get("pulse_target_path")
    if not target_path:
        log("SKIP CLIO: git_pulse_clio_enabled is set but pulse_target_path is not configured.")
        return {"enabled": True, "ok": False, "reason": "pulse_target_path not configured"}

    target_repo = Path(target_path).expanduser().resolve()
    if not (target_repo / ".git").exists():
        log(f"SKIP CLIO: pulse_target_path is not a git repo: {target_repo}")
        return {"enabled": True, "ok": False, "reason": f"not a git repo: {target_repo}"}

    subdir = cfg.get("git_pulse_clio_subdir") or "CLIO"
    filename = cfg.get("git_pulse_clio_filename") or "git-pulse-daily-log.md"
    file_rel = f"{subdir}/{filename}"

    target_file = target_repo / file_rel
    existing = target_file.read_text(encoding="utf-8") if target_file.exists() else ""

    clio_start, clio_end = _clio_markers(now.strftime("%Y-%m-%d"))
    existing_clio_block = _extract_block_text(existing, clio_start, clio_end)
    if _would_clobber_real_summary(existing_clio_block, summary):
        log(f"SKIP: zero-row rerun would clobber an existing non-empty summary ({file_rel})")
        return {"enabled": True, "ok": True, "skipped": "would_clobber"}

    new_content = upsert_clio_block(existing, summary, now)

    if dry_run:
        log(f"DRY RUN — would upsert CLIO block into {file_rel}:")
        print("-" * 60)
        print(build_clio_block(summary, now), end="")
        print("-" * 60)
        return {"enabled": True, "ok": True, "dry_run": True, "file_rel": file_rel}

    result = _commit_and_push_if_changed(
        target_repo=target_repo,
        file_rel=file_rel,
        new_content=new_content,
        push=True,
        commit_message=f"git-pulse: {now:%Y-%m-%d} daily summary",
    )
    log(f"CLIO sync ({file_rel}): {result}")
    return {"enabled": True, "ok": True, "file_rel": file_rel, **result}


# --- Orchestration -------------------------------------------------------------
def run(dry_run: bool = False, now: datetime | None = None, force: bool = False) -> int:
    now = now or datetime.now()

    if not force and is_late_run(now):
        log(
            f"SKIP: late catch-up run at {now:%H:%M} (< {RUN_HOUR_FLOOR:02d}:00) — the 00:00 "
            f"rollover has already moved Today->Yesterday. Writing nothing."
        )
        return 0

    vault_write_ready = vault_ready() and TODAY_FILE.exists()
    if not vault_ready():
        log("Obsidian vault not ready (no sentinel found) — skipping both vault writes.")
    elif not TODAY_FILE.exists():
        log(f"{TODAY_FILE.name} missing — the rollover owns file creation. Skipping both vault writes.")

    from rebalance.ingest.config import get_pulse_config

    clio_enabled = bool(get_pulse_config().get("git_pulse_clio_enabled"))

    if not vault_write_ready and not clio_enabled:
        log("SKIP: no destination available (vault not ready, CLIO not enabled). Writing nothing.")
        return 0

    content = TODAY_FILE.read_text(encoding="utf-8") if vault_write_ready else ""
    original_content = content
    if vault_write_ready:
        # Repair a pre-existing reversed block pair BEFORE the change-check below, so
        # the fix persists even on a run that generates no new summary content itself
        # (content != original_content must see the repair, not just new synthesis).
        content = normalize_block_order(content)

    # --- Step 1: pulse summary (must land FIRST — see module docstring) --------
    # Vault-only destination (unlike git-pulse below, it has no CLIO alternate) —
    # skip collecting and synthesizing entirely when there's nowhere to write it.
    if vault_write_ready:
        pulse_activity = collect_pulse_activity()
        pulse_summary = synthesize_pulse(pulse_activity)
        if pulse_summary is not None:
            if dry_run:
                log("DRY RUN — would write this pulse block to the bottom of Today's Notes:")
                print("-" * 60)
                print(build_pulse_block(pulse_summary, now), end="")
                print("-" * 60)
            else:
                content = upsert_pulse_block(content, pulse_summary, now)

    # --- Step 2: git-pulse summary (lands AFTER the pulse block, same write) ---
    activity_tsv, exit_code = collect_git_pulse_activity()
    if exit_code == 0 and activity_tsv is not None:
        git_pulse_summary = synthesize_git_pulse(activity_tsv)
        if git_pulse_summary is not None:
            if clio_enabled:
                sync_to_clio(git_pulse_summary, now, dry_run=dry_run)

            if vault_write_ready:
                existing_block = _extract_block_text(content, GIT_PULSE_MARKER_START, GIT_PULSE_MARKER_END)
                if _would_clobber_real_summary(existing_block, git_pulse_summary):
                    log("SKIP: zero-row rerun would clobber an existing non-empty summary")
                elif dry_run:
                    log("DRY RUN — would write this git-pulse block to the bottom of Today's Notes:")
                    print("-" * 60)
                    print(build_git_pulse_block(git_pulse_summary, now), end="")
                    print("-" * 60)
                else:
                    content = upsert_git_pulse_block(content, git_pulse_summary, now)

    if not vault_write_ready or dry_run:
        return 0

    if content != original_content:
        TODAY_FILE.write_text(content, encoding="utf-8")
        log(f"wrote daily synthesis block(s) to {TODAY_FILE.name}")
    else:
        log("no block changes — no write needed.")
    return 0


def show_status() -> int:
    from rebalance.ingest.config import get_pulse_config

    now = datetime.now()
    log(f"vault ready: {vault_ready()}")
    log(f"Today's Notes exists: {TODAY_FILE.exists()}")
    if TODAY_FILE.exists():
        content = TODAY_FILE.read_text(encoding="utf-8")
        pulse_present = PULSE_MARKER_START in content and PULSE_MARKER_END in content
        git_pulse_present = GIT_PULSE_MARKER_START in content and GIT_PULSE_MARKER_END in content
        log(f"pulse summary block present: {pulse_present}")
        log(f"git-pulse summary block present: {git_pulse_present}")

    cfg = get_pulse_config()
    clio_enabled = bool(cfg.get("git_pulse_clio_enabled"))
    log(f"CLIO export enabled: {clio_enabled}")
    if clio_enabled:
        target_path = cfg.get("pulse_target_path")
        subdir = cfg.get("git_pulse_clio_subdir") or "CLIO"
        filename = cfg.get("git_pulse_clio_filename") or "git-pulse-daily-log.md"
        if target_path:
            clio_file = Path(target_path).expanduser().resolve() / subdir / filename
            log(f"CLIO target: {clio_file} (exists: {clio_file.exists()})")
        else:
            log("CLIO target: pulse_target_path not configured — CLIO write would SKIP")

    log(f"would run now ({now:%H:%M}): {not is_late_run(now)} (hour floor {RUN_HOUR_FLOOR:02d}:00)")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the blocks that would be written; change nothing")
    parser.add_argument(
        "--force", action="store_true", help="bypass the 18:00 floor guard for manual runs (uses real current time)"
    )
    parser.add_argument("--status", action="store_true", help="show vault/CLIO/block state, then exit")
    args = parser.parse_args(argv)

    if args.status:
        return show_status()

    _log_job("started")
    t0 = time.monotonic()
    try:
        code = run(dry_run=args.dry_run, force=args.force)
    except Exception as e:  # noqa: BLE001
        elapsed = time.monotonic() - t0
        log(f"ERROR: {e}")
        _log_job("failed", elapsed=elapsed, exit_code=1)
        return 1
    elapsed = time.monotonic() - t0
    _log_job("completed" if code == 0 else "failed", elapsed=elapsed, exit_code=code)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
