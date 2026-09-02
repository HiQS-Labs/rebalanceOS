#!/usr/bin/env python3
"""Twice-daily progress digest — producer half (GH-142).

Collects today's signal from rebalance.db, synthesizes it with Gemini, and publishes
one markdown file into the shared pulse repo. AEGIS Sleuth's snapshot-relay polls that
directory and posts new files to Slack (AEGIS-Sleuth-Slackbot#157) — this script never
talks to Slack itself.

Design contract (mirrors utils/daily_synthesis.py, which this is modeled on):
  * Deterministic first  — the three collectors own the FACTS. They are plain SQL and one
                           subprocess; no model is involved in deciding what happened.
  * Gemini-only prose    — synthesis returns None on failure and the caller writes NOTHING.
                           No fallback model ever reaches the channel. Same rule as
                           synthesize_pulse() (daily_synthesis.py:197).
  * Honest collectors    — a collector that fails records its error IN the facts rather
                           than returning empty. A digest that says "github: unavailable"
                           is correct; one that silently says "0 commits" is a lie, and
                           this repo has been bitten three times by jobs reporting
                           success while doing nothing (see #157).
  * generated_at         — stamped in the payload and rendered at the top of the post.
                           This is the ENTIRE observability design: launchd runs a missed
                           job on next wake, so a digest produced at 23:40 announces that
                           in the channel. There is deliberately no watchdog.
  * Fixed slot labels    — hiqs-<date>-<slot>.md where slot is 1305 or 1705, NEVER the
                           raw clock. The relay's seen-set is filename-keyed, so a late
                           catch-up or a manual re-run must land on the SAME filename and
                           overwrite its own slot rather than minting a third name and
                           posting the day twice.
  * Single write path    — reuses pulse._commit_and_push_if_changed, and reports its real
                           result rather than assuming success.

Two things that look like details and are not:

  * Day bounds are computed in UTC from the LOCAL day, and every timestamp comparison goes
    through SQLite's datetime(). The tables mix formats — github_commits stores
    '...T23:55:26Z', github_direct_commits stores '...T16:45:05-07:00' — and a raw string
    compare against a local date silently drops or misattributes an evening's work for
    anyone not on UTC.
  * Commits come from BOTH github_commits (PR-attached) and github_direct_commits (pushes
    straight to a branch). Reading only the first makes the post contradict itself: an
    empty commit list beside per-repo counts of 14.

Semantic slot: source_filter=["github"] is REQUIRED, not tuning. A bake-off against live
data showed the unfiltered query returns near-duplicate vault prompt logs, because ~85%
of a day's index churn is vault writes. See AEGIS-Sleuth-Slackbot#157.

Requires the project venv (imports rebalance.*). Run via scripts/hiqs_digest.sh so launchd
inherits Full Disk Access.

Usage:
  hiqs_digest.py                  # produce and publish (the launchd job)
  hiqs_digest.py --dry-run        # print what would be published; no write, no push
  hiqs_digest.py --facts-only     # print the collected facts as JSON; no LLM call
  hiqs_digest.py --slot 1305      # override the slot label (default: bucketed from now)
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.paths import resolve_database_path

REPO_ROOT = Path(__file__).resolve().parent.parent

# CB-1 from scripts/health_issue_reporter.py:31-38 — the hard kill switch, and the only
# breaker this job takes. The quota and per-run caps there guard up to 8 LLM calls a day;
# this job makes 2. Add them when a third caller shares the budget.
LLM_DISABLE_ENV = "HIQS_DIGEST_LLM_DISABLE"

# The two scheduled slots. A run at any other time buckets to whichever it belongs to, so a
# launchd catch-up overwrites its own slot file instead of minting a new filename the
# relay's seen-set has nothing to match on.
SLOT_MIDDAY = "1305"
SLOT_EVENING = "1705"
SLOT_BOUNDARY_HOUR = 15

SEMANTIC_SOURCES = ["github"]
SEMANTIC_QUERY = "what work shipped today"
SEMANTIC_TOP_K = 8

# Caps on the DETAIL handed to the model. Totals are counted separately — reporting a
# capped list length as the day's total silently reads as a plateau on the busiest days.
COMMIT_DETAIL_LIMIT = 40
ITEM_DETAIL_LIMIT = 20

PROMPT_TEMPLATE = """You are writing a short progress update for an engineering team's Slack channel.

Below is a STRUCTURED snapshot of today's activity. Write a summary a teammate can skim in
about thirty seconds.

Cover all three, in this order, and nothing else:

1. SHIPPED — what actually landed today, grouped by repo or theme. Lead with merged work.
2. IN FLIGHT — one or two lines, only if `semantic.hits` shows themes that are NOT already
   covered by the shipped items. If it adds nothing new, omit this section entirely.
3. HEALTH — if `health.problem_count` is greater than zero, ONE line naming the problems.
   If it is zero, write nothing about health.

Hard rules:
- Do NOT invent anything. Every claim must trace to the data below.
- NEVER list a repository that shipped nothing. A repo with commits but no merged work is
  only worth a mention if it is the bulk of the day's activity.
- The `*_total` fields are the real counts. The lists beside them are truncated samples —
  never present a list's length as a total.
- No preamble, no sign-off, no restating the counts (a footer already carries them).
- Twelve lines is the ceiling. If the data is sparse, three lines is the correct answer.
- If a whole section's data is missing or has an `error` key, say so in a few words. Never
  imply a quiet day when the truth is that a collector failed.

DATA:
{data}
"""


def log(msg: str) -> None:
    print(f"[hiqs-digest] {msg}", file=sys.stderr, flush=True)


def _scrub(text: str) -> str:
    """Replace the home directory with ~ so absolute paths don't ride into Slack.

    Applied to EVERY string that can reach the prompt, not just doctor details: the prompt
    instructs the model to report failed sections, so a collector's error text is published
    verbatim-ish. A sqlite error carries the full database path, and with it a username.
    """
    if not text:
        return text
    return text.replace(str(Path.home()), "~")


def _fail(where: str, error: object) -> dict[str, Any]:
    """A collector failure, scrubbed. Never returns empty data alongside the error."""
    return {"error": _scrub(f"{where}: {error}")}


def slot_for(now: datetime) -> str:
    """Bucket a wall-clock time to one of the two scheduled slots.

    The filename-keyed dedupe in the Sleuth relay only works if the slot is one of two
    fixed values. A catch-up run at 14:12 must produce the 1305 file, not a 1412 file.
    """
    return SLOT_MIDDAY if now.hour < SLOT_BOUNDARY_HOUR else SLOT_EVENING


def _utc_day_bounds(now: datetime) -> tuple[str, str]:
    """UTC half-open bounds for the LOCAL calendar day containing *now*.

    Returned in SQLite's datetime() output format so they compare directly against
    `datetime(<column>)`, which normalizes both the 'Z' and '+HH:MM' forms in these tables.
    """
    start_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    fmt = "%Y-%m-%d %H:%M:%S"
    return (
        start_local.astimezone(timezone.utc).strftime(fmt),
        end_local.astimezone(timezone.utc).strftime(fmt),
    )


# --- Collectors ----------------------------------------------------------------
# Each returns a dict. On failure it returns {"error": "..."} rather than empty data,
# so the synthesizer can say "unavailable" instead of implying a quiet day.


def collect_github(db: Path, today: str, bounds: tuple[str, str]) -> dict[str, Any]:
    """Today's GitHub activity. No LLM, no parsing — the typed columns already carry it."""
    start_utc, end_utc = bounds
    try:
        with db_connection_readonly(db) as conn:
            conn.row_factory = sqlite3.Row

            # SUM/GROUP BY, not raw rows: github_activity is keyed (login, repo, scan_date),
            # so a multi-contributor repo has one row PER LOGIN. Selecting raw rows would
            # list the repo twice with split counts and inflate the active-repo count.
            # Operator choice (GH-142): count ALL contributors — this is a team channel.
            repos = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name,
                           SUM(commits)        AS commits,
                           SUM(prs_opened)     AS prs_opened,
                           SUM(prs_merged)     AS prs_merged,
                           SUM(issues_opened)  AS issues_opened,
                           SUM(reviews)        AS reviews,
                           COUNT(DISTINCT login) AS contributors
                    FROM github_activity
                    WHERE scan_date = ?
                    GROUP BY repo_full_name
                    HAVING SUM(commits + prs_opened + prs_merged
                               + issues_opened + issue_comments + reviews) > 0
                    ORDER BY commits DESC, prs_merged DESC
                    """,
                    (today,),
                )
            ]

            # Both commit tables. github_commits is PR-attached only; direct branch pushes
            # live in github_direct_commits. Reading one makes the post contradict itself.
            commit_sql = """
                SELECT repo_full_name, message, author_login, committed_at, source FROM (
                    SELECT repo_full_name, message, author_login, committed_at, 'pr' AS source
                    FROM github_commits
                    WHERE datetime(committed_at) >= ? AND datetime(committed_at) < ?
                    UNION ALL
                    SELECT repo_full_name, message, author_login, committed_at, 'push' AS source
                    FROM github_direct_commits
                    WHERE datetime(committed_at) >= ? AND datetime(committed_at) < ?
                )
                ORDER BY datetime(committed_at) DESC
            """
            commit_args = (start_utc, end_utc, start_utc, end_utc)
            commit_total = conn.execute(f"SELECT COUNT(*) FROM ({commit_sql})", commit_args).fetchone()[0]
            commits = [dict(r) for r in conn.execute(f"{commit_sql} LIMIT {COMMIT_DETAIL_LIMIT}", commit_args)]

            merged_total = conn.execute(
                "SELECT COUNT(*) FROM github_items WHERE datetime(merged_at) >= ? AND datetime(merged_at) < ?",
                (start_utc, end_utc),
            ).fetchone()[0]
            merged = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name, item_type, number, title, author_login
                    FROM github_items
                    WHERE datetime(merged_at) >= ? AND datetime(merged_at) < ?
                    ORDER BY datetime(merged_at) DESC
                    LIMIT ?
                    """,
                    (start_utc, end_utc, ITEM_DETAIL_LIMIT),
                )
            ]

            closed_total = conn.execute(
                "SELECT COUNT(*) FROM github_items "
                "WHERE datetime(closed_at) >= ? AND datetime(closed_at) < ? AND merged_at IS NULL",
                (start_utc, end_utc),
            ).fetchone()[0]
            closed = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name, item_type, number, title
                    FROM github_items
                    WHERE datetime(closed_at) >= ? AND datetime(closed_at) < ?
                      AND merged_at IS NULL
                    ORDER BY datetime(closed_at) DESC
                    LIMIT ?
                    """,
                    (start_utc, end_utc, ITEM_DETAIL_LIMIT),
                )
            ]
    except sqlite3.Error as e:
        return _fail("github collector failed", e)

    # First line of each commit message is the subject; the body is noise for a digest.
    for c in commits:
        c["message"] = (c.get("message") or "").splitlines()[0][:140] if c.get("message") else ""

    return {
        "by_repo": repos,
        "commit_total": commit_total,
        "commits": commits,
        "merged_total": merged_total,
        "merged": merged,
        "closed_not_merged_total": closed_total,
        "closed_not_merged": closed,
        "detail_capped_at": {"commits": COMMIT_DETAIL_LIMIT, "items": ITEM_DETAIL_LIMIT},
    }


def collect_health() -> dict[str, Any]:
    """Problems from `rebalance doctor --json`, by DISPOSITION rather than raw status.

    doctor emits both. `status` is the raw check result; `disposition` is the reconciler's
    verdict, where "suppressed" means a WARN it deliberately hid because the source
    recovered inside its stale window. Filtering on status republishes those to Slack as
    live problems while the same payload reports verdict: ok.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "rebalance", "doctor", "--json"],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return _fail("doctor failed to run", e)

    if not result.stdout.strip():
        return _fail("doctor produced no output", f"exit {result.returncode}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return _fail("doctor output was not JSON", e)

    problems = [
        {
            "name": c.get("name"),
            "status": c.get("status"),
            "disposition": c.get("disposition"),
            "detail": _scrub(c.get("detail") or "")[:200],
        }
        for c in payload.get("checks", [])
        if c.get("disposition") == "problem"
    ]
    return {
        "verdict": payload.get("verdict"),
        "problem_count": len(problems),
        "problems": problems,
    }


def collect_semantic(db: Path, today: str) -> dict[str, Any]:
    """Date-bounded semantic search over the BGE index, filtered to GitHub sources.

    source_filter is REQUIRED — see the module docstring. Titles are deduped because the
    index legitimately holds several near-identical chunks of the same document.
    """
    try:
        from rebalance.ingest import semantic_index
    except Exception as e:  # noqa: BLE001 — see below; ImportError is too narrow here
        # NOT `except ImportError`. This repo's own tests/conftest.py documents that the
        # embedding import chain raises ValueError ("mlx.__spec__ is None") via
        # transformers' is_mlx_available(), and a headless run raises RuntimeError
        # ("[metal::load_device] No Metal device available"). Either would otherwise
        # propagate out of run() and kill the whole digest over one degraded slot.
        return _fail("semantic index unavailable", e)

    try:
        rows = semantic_index.query(
            db,
            SEMANTIC_QUERY,
            top_k=SEMANTIC_TOP_K,
            updated_after=today,
            source_filter=SEMANTIC_SOURCES,
        )
    except Exception as e:  # noqa: BLE001 — any failure degrades this slot, never the run
        return _fail("semantic query failed", e)

    seen: set[str] = set()
    hits: list[dict[str, Any]] = []
    for r in rows:
        title = (r.get("title") or r.get("source_id") or "").strip()
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        hits.append({"title": title[:160], "source_type": r.get("source_type")})

    return {"query": SEMANTIC_QUERY, "sources": SEMANTIC_SOURCES, "hits": hits}


def build_facts(db: Path, now: datetime) -> dict[str, Any]:
    today = now.strftime("%Y-%m-%d")
    bounds = _utc_day_bounds(now)
    return {
        "date": today,
        "generated_at": now.isoformat(timespec="seconds"),
        "window": "midnight to now, local time",
        "window_utc": {"start": bounds[0], "end": bounds[1]},
        "github": collect_github(db, today, bounds),
        "health": collect_health(),
        "semantic": collect_semantic(db, today),
    }


# --- Synthesis -----------------------------------------------------------------


def synthesize(facts: dict[str, Any]) -> str | None:
    """Gemini-only. Returns None if unavailable or failed — the caller writes nothing.

    NO fallback model. A degraded summary posted to a team channel is worse than silence,
    because nobody can tell it apart from a good one.
    """
    # Belt and braces with run()'s check. run() owns the EXIT CODE decision (the kill
    # switch is an operator no-op, not a failure); this guard owns the API call, so any
    # future caller of synthesize() honours the switch too.
    if os.environ.get(LLM_DISABLE_ENV) == "1":
        log(f"SKIP: {LLM_DISABLE_ENV}=1 — refusing to synthesize.")
        return None

    try:
        from rebalance.ingest.config import get_gemini_api_key
        from rebalance.ingest.querier import _synthesize_gemini
    except Exception as e:  # noqa: BLE001 — same import-chain hazard as collect_semantic
        log(_scrub(f"SKIP: rebalance synthesis path not importable ({e})."))
        return None

    key = get_gemini_api_key()
    if not key:
        log("SKIP: no Gemini API key — refusing to write a fallback summary.")
        return None

    prompt = PROMPT_TEMPLATE.format(data=json.dumps(facts, indent=2, default=str))
    try:
        return _synthesize_gemini(prompt, api_key=key, thinking_budget=0, max_tokens=2048)
    except Exception as e:  # noqa: BLE001 — any failure means skip, never fall back
        log(_scrub(f"SKIP: Gemini synthesis failed ({e}) — nothing written."))
        return None


# --- Render and publish --------------------------------------------------------


def render(summary: str, facts: dict[str, Any], now: datetime) -> str:
    """The published markdown. generated_at is rendered, not just stored — see docstring."""
    gh = facts.get("github", {})
    counts = []
    if "error" not in gh:
        # Real totals, not len() of the truncated detail lists.
        counts.append(f"{gh.get('commit_total', 0)} commits")
        counts.append(f"{gh.get('merged_total', 0)} merged")
        counts.append(f"{len(gh.get('by_repo', []))} active repos")
    health = facts.get("health", {})
    if "error" not in health and health.get("problem_count"):
        counts.append(f"{health['problem_count']} health warnings")

    footer = " · ".join(counts) if counts else "no deterministic counts available"

    return (
        f"# Progress digest — {facts['date']}\n\n"
        f"_Generated {now:%Y-%m-%d %H:%M %Z}. Covers midnight to now._\n\n"
        f"{summary.strip()}\n\n"
        f"---\n"
        f"{footer}\n"
    )


def publish(content: str, now: datetime, slot: str, *, dry_run: bool, push: bool) -> dict[str, Any]:
    """Write + commit + push the digest, reporting the REAL outcome.

    _commit_and_push_if_changed never returns an "ok" key — it signals failure through
    committed/pushed/git_error. Spreading its result into {"ok": True, ...} would make the
    caller's failure gate unreachable, so a push that fails would exit 0 and every
    observability surface would report the job complete with nothing published.
    """
    try:
        from rebalance.ingest.config import get_pulse_config
        from rebalance.ingest.pulse import _commit_and_push_if_changed
    except Exception as e:  # noqa: BLE001 — same import-chain hazard as above
        return {"ok": False, "reason": _scrub(f"rebalance package not importable: {e}")}

    target_path = get_pulse_config().get("pulse_target_path")
    if not target_path:
        return {"ok": False, "reason": "pulse_target_path is not configured"}

    target_repo = Path(target_path).expanduser().resolve()
    if not (target_repo / ".git").exists():
        return {"ok": False, "reason": _scrub(f"pulse_target_path is not a git repo: {target_repo}")}

    # Read at call time, not import time, so the value is overridable and honestly named.
    subdir = os.environ.get("HIQS_DIGEST_SUBDIR", "digests")
    file_rel = f"{subdir}/hiqs-{now:%Y-%m-%d}-{slot}.md"

    if dry_run:
        log(f"DRY RUN — would write {file_rel} in the pulse repo:")
        print("-" * 72)
        print(content, end="")
        print("-" * 72)
        return {"ok": True, "dry_run": True, "file_rel": file_rel}

    result = _commit_and_push_if_changed(
        target_repo=target_repo,
        file_rel=file_rel,
        new_content=content,
        push=push,
        commit_message=f"hiqs-digest: {now:%Y-%m-%d} {slot}",
    )
    log(f"publish ({file_rel}): {result}")

    # Interpret the real keys. "no content change" is a legitimate success: a re-run of the
    # same slot with identical content has nothing to do.
    unchanged = result.get("reason") == "no content change"
    published = bool(result.get("committed")) and (bool(result.get("pushed")) or not push)
    if not (unchanged or published):
        return {
            "ok": False,
            "reason": _scrub(f"git publish failed: {result.get('git_error') or result}"),
            "file_rel": file_rel,
            **result,
        }
    return {"ok": True, "file_rel": file_rel, **result}


# --- Orchestration -------------------------------------------------------------


def run(
    *,
    dry_run: bool = False,
    facts_only: bool = False,
    slot: str | None = None,
    push: bool = True,
    now: datetime | None = None,
) -> int:
    now = now or datetime.now().astimezone()
    slot = slot or slot_for(now)

    try:
        db = resolve_database_path()
    except Exception as e:  # noqa: BLE001 — resolver raises its own error types
        log(_scrub(f"FATAL: could not resolve the database path: {e}"))
        return 1

    if not db.exists():
        log(_scrub(f"FATAL: database not found at {db}"))
        return 1

    facts = build_facts(db, now)

    for name in ("github", "health", "semantic"):
        err = facts[name].get("error")
        if err:
            log(f"WARN: {err}")

    if facts_only:
        print(json.dumps(facts, indent=2, default=str))
        return 0

    # Every collector failing means there is nothing to summarize. Say so and exit
    # non-zero so the wrapper records job_failed, rather than publishing an empty digest.
    if all(facts[n].get("error") for n in ("github", "health", "semantic")):
        log("FATAL: every collector failed — nothing to publish.")
        return 1

    # The documented kill switch is an operator-requested no-op, NOT a failure. Returning
    # non-zero here would make the dashboard show a red job twice a day forever,
    # indistinguishable from a Gemini outage.
    if os.environ.get(LLM_DISABLE_ENV) == "1":
        log(f"{LLM_DISABLE_ENV}=1 — synthesis disabled by operator; nothing published.")
        return 0

    summary = synthesize(facts)
    if summary is None:
        log("Nothing written (no synthesis).")
        return 1

    result = publish(render(summary, facts, now), now, slot, dry_run=dry_run, push=push)
    if not result.get("ok"):
        log(f"FATAL: publish failed — {result.get('reason')}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print the digest; write nothing")
    parser.add_argument("--facts-only", action="store_true", help="print collected facts as JSON; no LLM call")
    parser.add_argument("--slot", help=f"slot label (default: {SLOT_MIDDAY} or {SLOT_EVENING})")
    parser.add_argument("--no-push", action="store_true", help="commit locally but do not push")
    args = parser.parse_args()
    return run(
        dry_run=args.dry_run,
        facts_only=args.facts_only,
        slot=args.slot,
        push=not args.no_push,
    )


if __name__ == "__main__":
    sys.exit(main())
