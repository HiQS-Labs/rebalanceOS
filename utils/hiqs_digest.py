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
                           posting the day twice. --slot is choices-constrained, because
                           an unvalidated one defeats the whole scheme.
  * Single write path    — reuses pulse._commit_and_push_if_changed, and reports its real
                           result rather than assuming success.

Four things that look like details and are not:

  * Day bounds are computed in UTC from the LOCAL day — resolved through time_ops.local_tz()
    so REBALANCE_TZ and the configured zone are honoured, and each boundary resolved
    independently (a DST day is 23 or 25 hours long, so start + 1 day is not its end).
    Every SQL timestamp comparison goes through SQLite's datetime(). The tables mix formats
    — github_commits stores '...T23:55:26Z', github_direct_commits stores
    '...T16:45:05-07:00' — and a raw string compare against a local date silently drops or
    misattributes an evening's work for anyone not on UTC. The one filter that CANNOT use
    datetime() is the semantic index (db/semantic.py compares updated_at raw), and that
    column mixes both forms too, so no string bound is correct for both: it gets a widened
    prefilter and the real window is applied in Python on parsed instants.
  * Commits come from BOTH github_commits (PR-attached) and github_direct_commits (pushes
    straight to a branch), DEDUPED on (repo, sha). Reading only the first makes the post
    contradict itself: an empty commit list beside per-repo counts of 14. Reading both
    without the dedupe overstates the day, because a commit pushed to a branch and later
    attached to a PR is in both tables — see _day_commits_cte.
  * by_repo is derived from those same day-bounded tables, NOT from github_activity.
    github_activity has a scan_date column and looks per-day; it is not. Every row holds a
    14-to-30-day event-window total stamped with today's date, for watched-repo rollups
    (github_watch.py:118) and owned-login scans (github_scan.py:259) alike. Sourcing
    by_repo there published a repo's fortnight as its day.
  * A run before the 13:05 slot is a post-midnight catch-up of a job that was missed, not
    a digest of the new day, and it skips — same rule daily-synthesis already carries.
    Nothing downstream could tell that post apart from a quiet morning.

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
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.lib.time_ops import local_tz
from rebalance.paths import resolve_database_path, resolve_project_root

# AGENTS.md → "Use the shared resolvers […] no parents[N] repo-root walks". This is the
# cwd for the `rebalance doctor` subprocess, so a parents[N] walk would silently run
# doctor against the wrong tree if this file ever moves or is vendored a level deeper.
# resolve_project_root also honours ~/.config/rebalance/runtime-root, the mechanism
# install_common.sh uses to bind the launchd job to one checkout (GH-36, GH-59).
REPO_ROOT = resolve_project_root(Path(__file__))

# CB-1 from scripts/health_issue_reporter.py:31-38 — the hard kill switch, and the only
# breaker this job takes. The quota and per-run caps there guard up to 8 LLM calls a day;
# this job makes 2. Add them when a third caller shares the budget.
LLM_DISABLE_ENV = "HIQS_DIGEST_LLM_DISABLE"

# The two scheduled slots, and the local times SCHEDULER.md fires them at. A run at any
# other time buckets to whichever it belongs to, so a launchd catch-up overwrites its own
# slot file instead of minting a new filename the relay's seen-set has nothing to match on.
SLOT_MIDDAY = "1305"
SLOT_EVENING = "1705"
FIRE_MIDDAY = time(13, 5)
FIRE_EVENING = time(17, 5)

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
   After the merged work, add ONE compact line for repos that pushed >= 5 commits or opened
   PRs today but merged nothing yet (e.g. "acme/api: 20 commits in flight") — a busy
   in-progress repo is signal, not noise. Repos whose only activity is opened issues may be
   omitted.
2. IN FLIGHT — one or two lines, only if `semantic.hits` shows themes that are NOT already
   covered by the shipped items. If it adds nothing new, omit this section entirely.
3. HEALTH — if `health.problem_count` is greater than zero, ONE line naming the problems.
   If `github.stale_repos` is non-empty, ONE line naming those repos and why — a repo
   listed there may be under-reported today (sync lag or a failed collector), so never
   present its quietness as a quiet day. If both are empty, write nothing about health.

Hard rules:
- Do NOT invent anything. Every claim must trace to the data below.
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

    Applied to every string that can reach the prompt: collector errors (the prompt
    instructs the model to report failed sections, so error text is published verbatim-ish,
    and a sqlite error carries the full database path and with it a username), doctor
    details, commit subjects, PR/issue titles, and semantic hit titles. If you add a field
    to the facts payload that came from outside this process, scrub it here too.
    """
    if not text:
        return text
    return text.replace(str(Path.home()), "~")


def _is_safe_subdir(subdir: str) -> bool:
    """True if *subdir* is a plain relative directory path inside the pulse repo.

    Rejects the empty string, absolute paths, anything containing a '..' segment, and
    Windows-style drive/UNC prefixes. See publish() for why this is not cosmetic.
    """
    if not subdir or subdir.startswith(("/", "\\")) or ":" in subdir:
        return False
    parts = [p for p in subdir.replace("\\", "/").split("/") if p]
    return bool(parts) and all(p not in ("..", ".") for p in parts)


def _fail(where: str, error: object) -> dict[str, Any]:
    """A collector failure, scrubbed. Never returns empty data alongside the error."""
    return {"error": _scrub(f"{where}: {error}")}


def slot_for(now: datetime) -> str:
    """Bucket a wall-clock time to one of the two scheduled slots.

    The filename-keyed dedupe in the Sleuth relay only works if the slot is one of two
    fixed values. A catch-up run at 14:12 must produce the 1305 file, not a 1412 file.

    The boundary is the EVENING FIRE TIME, not an arbitrary mid-afternoon hour. launchd
    runs a slept-through job on the next wake, so a 13:05 job missed by a sleeping Mac can
    fire at 15:30 — and with a 15:00 boundary that midday run wrote the *1705* filename.
    The 17:05 job then overwrote it, the relay had already seen that name, and NEITHER
    digest reached the channel. Bucketing on the fire time makes any catch-up before 17:05
    the midday slot, which is what was actually scheduled.
    """
    return SLOT_MIDDAY if now.time() < FIRE_EVENING else SLOT_EVENING


def _local_midnight(day: date, tz: Any) -> datetime:
    """Local midnight on *day*, carrying THAT instant's UTC offset.

    `datetime.now().astimezone()` returns a FIXED-OFFSET tzinfo captured at the current
    instant, so `.replace(hour=0)` on it stamps midnight with the afternoon's offset — an
    hour wrong on both DST transition days. That is why run() resolves `now` through
    time_ops.local_tz(), which returns a real ZoneInfo: attaching one to a naive midnight
    re-resolves the offset for the local time it is attached to.

    *tz* is honoured whatever it is. A fixed-offset tzinfo has no DST to re-resolve, so
    `replace` is exactly right for it too; an earlier version fell back to `.astimezone()`
    for the non-ZoneInfo case, which DISCARDED the caller's zone and silently bounded the
    day in the machine's zone while `build_facts` labelled it with the caller's.
    """
    naive = datetime.combine(day, time.min)
    if tz is None:
        return naive.astimezone()
    return naive.replace(tzinfo=tz)


def _utc_day_bounds(now: datetime) -> tuple[str, str]:
    """UTC half-open bounds for the LOCAL calendar day containing *now*.

    Returned in SQLite's datetime() output format so they compare directly against
    `datetime(<column>)`, which normalizes both the 'Z' and '+HH:MM' forms in these tables.

    Each boundary is resolved independently — a DST day is 23 or 25 hours long, so
    `start + timedelta(days=1)` is not its end.
    """
    tz = now.tzinfo
    start_local = _local_midnight(now.date(), tz)
    end_local = _local_midnight(now.date() + timedelta(days=1), tz)
    fmt = "%Y-%m-%d %H:%M:%S"
    return (
        start_local.astimezone(timezone.utc).strftime(fmt),
        end_local.astimezone(timezone.utc).strftime(fmt),
    )


# The widest UTC offset any timestamp can carry (UTC+14 .. UTC-12). Used to widen the
# semantic prefilter — see _semantic_prefilter_bound.
_MAX_UTC_OFFSET = timedelta(hours=14)


def _as_utc(stamp: str) -> datetime | None:
    """Parse an ISO-8601 stamp in EITHER stored form to an aware UTC datetime.

    semantic_documents.updated_at is not one format. Measured on the live index, 24,509 of
    60,431 github rows carry a numeric offset ('2026-09-01T16:45:05-07:00') and the rest
    are 'Z'. Returns None for anything unparseable rather than raising, so one malformed
    row cannot take out the collector.
    """
    if not stamp:
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _semantic_prefilter_bound(start_utc: str) -> str:
    """A DELIBERATELY LOOSE lower bound for search_semantic_documents' raw compare.

    db/semantic.py filters `sd.updated_at >= ?` as a raw string, with no datetime()
    normalization, and the column mixes 'Z' and '+HH:MM' forms. For an offset-form row the
    leading characters are LOCAL time, so no single string bound is correct for both forms:
    a row stamped '2026-09-01T06:00:00-07:00' is 13:00 UTC — squarely inside a Sep 1
    Pacific day — yet '06' < '07' against a '2026-09-01T07:00:00Z' bound excludes it.

    So the SQL bound only prefilters: it is pushed back by the widest possible UTC offset,
    which cannot drop an in-window row in either format. collect_semantic then applies the
    real window in Python, on parsed instants. Over-fetching is safe; under-fetching reads
    to the channel as a quiet day, which is the failure this job exists to avoid.
    """
    widened = datetime.strptime(start_utc, "%Y-%m-%d %H:%M:%S") - _MAX_UTC_OFFSET
    return widened.strftime("%Y-%m-%dT%H:%M:%SZ")


# One row per (repo, sha) for the local day, across BOTH commit tables.
#
# The two tables overlap. github_commits holds PR-attached commits; github_direct_commits
# holds branch pushes — and a commit pushed to a branch that later lands in a PR is in
# both. Measured on the live database: 4,156 of 33,073 direct rows share (repo, sha) with
# a github_commits row, and github_commits ALONE has 2,680 repo+sha groups with more than
# one row. A plain UNION ALL therefore overstated commit_total, double-counted the same
# commit in by_repo, and handed the model the same subject twice — in a job whose contract
# is "never present a false number". pulse.py:255-263 reads this same pair of tables and
# has always guarded it with a NOT EXISTS; this is the same guard, expressed as a GROUP BY
# so it also collapses the duplicates WITHIN github_commits.
#
# MIN(source) resolves the label: 'pr' sorts before 'push', so a commit in both tables is
# reported as PR-attached, which is the more specific truth.
#
# The grouping key is the CANONICAL repo expression (see _repo_canonicalizer), not bare
# LOWER(repo_full_name): a renamed org's old spelling still syncs via GitHub redirects,
# so the same repo can hold rows under both spellings (#147) — without the canonical key
# those mirror rows split every count in two.


def _repo_canonicalizer() -> tuple[str, dict[str, str]]:
    """(sql_expr, params) mapping a repo_full_name column through the org-alias collapse.

    The expression lowercases the name and rewrites a renamed org's old owner
    segment to its current spelling — the same collapse
    ``config.canonical_github_repo_name`` applies in Python (#147). Mirrored rows
    (one repo synced under both spellings) then GROUP BY together instead of
    double-counting. Alias values travel as bound parameters so operator config
    never interpolates into the SQL string. With no aliases configured the
    expression is a plain LOWER({col}) and the parameter dict is empty.
    """
    try:
        from rebalance.ingest.config import get_github_org_aliases

        aliases = get_github_org_aliases()
    except Exception:  # noqa: BLE001 — a config read must never break the collector
        aliases = {}
    if not isinstance(aliases, dict) or not aliases:
        return "LOWER({col})", {}
    params: dict[str, str] = {}
    whens: list[str] = []
    for i, (old, new) in enumerate(sorted(aliases.items())):
        # THEN appends the repo segment after the canonical owner — the owner alone
        # is not a repo name, and the first cut of this expression lost it.
        whens.append(f"WHEN :alias_old_{i} THEN :alias_new_{i} || substr({{col}}, instr({{col}}, '/'))")
        params[f"alias_old_{i}"] = str(old).lower()
        params[f"alias_new_{i}"] = str(new).lower()
    case = "LOWER(CASE LOWER(substr({col}, 1, instr({col}, '/') - 1)) " + " ".join(whens) + " ELSE {col} END)"
    return case, params


def _day_commits_cte(canon_expr: str) -> str:
    """DAY_COMMITS_CTE with *canon_expr* (from _repo_canonicalizer) as the repo key."""
    canonical = canon_expr.format(col="repo_full_name")
    return f"""
    WITH day_commits AS (
        SELECT {canonical}      AS repo_full_name,
               sha,
               MIN(message)      AS message,
               MIN(author_login) AS author_login,
               MIN(committed_at) AS committed_at,
               MIN(source)       AS source
        FROM (
            SELECT repo_full_name, sha, message, author_login, committed_at, 'pr' AS source
            FROM github_commits
            WHERE datetime(committed_at) >= :start AND datetime(committed_at) < :end
            UNION ALL
            SELECT repo_full_name, sha, message, author_login, committed_at, 'push' AS source
            FROM github_direct_commits
            WHERE datetime(committed_at) >= :start AND datetime(committed_at) < :end
        )
        GROUP BY {canonical}, sha
    )
"""


# --- Collectors ----------------------------------------------------------------
# Each returns a dict. On failure it returns {"error": "..."} rather than empty data,
# so the synthesizer can say "unavailable" instead of implying a quiet day.


def collect_github(db: Path, bounds: tuple[str, str]) -> dict[str, Any]:
    """Today's GitHub activity. No LLM, no parsing — the typed columns already carry it."""
    start_utc, end_utc = bounds
    window = {"start": start_utc, "end": end_utc}
    canon_expr, alias_params = _repo_canonicalizer()
    canonical = canon_expr.format(col="repo_full_name")
    cte = _day_commits_cte(canon_expr)
    window.update(alias_params)
    try:
        # db_connection_readonly already sets row_factory = sqlite3.Row (connection.py:101).
        with db_connection_readonly(db) as conn:
            # by_repo is derived from the SAME day-bounded event tables as commit_total and
            # merged_total, so the per-repo lines and the footer cannot disagree.
            #
            # It deliberately does NOT read github_activity. That table looks per-day —
            # it has a scan_date column — but _summarize_by_repo() (github_scan.py:259)
            # counts every event in the fetched window (scan_github days=30; watched-repo
            # rollups use since_days=14) and stamps the whole total with scan_date=today.
            # github_watch.derive_watched_repo_activity() says so in its own docstring:
            # "scan_date = today and window-total counts".
            #
            # Measured against live data for 2026-09-01: github_activity said rebalanceOS
            # shipped 13 commits when 2 landed, said XYZ-forge shipped 5 when 42 landed,
            # and listed two repos with zero commits that day as active. For a job whose
            # contract is "never present a false number", that is the largest source of one.
            #
            # Its scan_date is also written from now_utc(), so filtering it by a LOCAL date
            # string dropped an evening's work outright for anyone off UTC — the same class
            # of bug the commit tables were already fixed for.
            #
            # The GROUP BY is the canonical repo expression (#147): lowercased, with a
            # renamed org's old owner spelling rewritten to the current one. Casing
            # variants AND org mirrors of one repo collapse into a single line, so a
            # transfer/rename can no longer inflate the "N active repos" footer with a
            # repo that does not exist.
            repos = [
                dict(r)
                for r in conn.execute(
                    cte
                    + f"""
                    SELECT {canonical}        AS repo_full_name,
                           SUM(commits)        AS commits,
                           SUM(prs_merged)     AS prs_merged,
                           SUM(prs_opened)     AS prs_opened,
                           SUM(issues_opened)  AS issues_opened,
                           COUNT(DISTINCT author_login) AS contributors
                    FROM (
                        -- Deduped commits from BOTH tables. Reading only github_commits
                        -- made push-only repos vanish from the digest; reading both
                        -- without the dedupe counted shared commits twice.
                        SELECT repo_full_name, author_login,
                               1 AS commits, 0 AS prs_merged, 0 AS prs_opened, 0 AS issues_opened
                        FROM day_commits
                        UNION ALL
                        SELECT repo_full_name, author_login, 0, 1, 0, 0
                        FROM github_items
                        WHERE item_type = 'pull_request'
                          AND datetime(merged_at) >= :start AND datetime(merged_at) < :end
                        UNION ALL
                        SELECT repo_full_name, author_login, 0, 0,
                               CASE WHEN item_type = 'pull_request' THEN 1 ELSE 0 END,
                               CASE WHEN item_type = 'issue' THEN 1 ELSE 0 END
                        FROM github_items
                        WHERE datetime(created_at) >= :start AND datetime(created_at) < :end
                    )
                    GROUP BY {canonical}
                    ORDER BY commits DESC, prs_merged DESC
                    """,
                    window,
                )
            ]

            # No ORDER BY inside the COUNT — SQLite would materialise and sort the whole
            # day's rows just to count them.
            commit_total = conn.execute(cte + "SELECT COUNT(*) FROM day_commits", window).fetchone()[0]
            commits = [
                dict(r)
                for r in conn.execute(
                    cte
                    + """
                    SELECT repo_full_name, message, author_login, committed_at, source
                    FROM day_commits
                    ORDER BY datetime(committed_at) DESC
                    LIMIT :limit
                    """,
                    {**window, "limit": COMMIT_DETAIL_LIMIT},
                )
            ]

            # item_type = 'pull_request' on BOTH the total and the detail, and the count
            # is DISTINCT on (canonical repo, number): a repo mirrored under two org
            # spellings holds the SAME PR number twice (#147), and a plain COUNT(*) read
            # "10 merged" on a day that shipped five. The by_repo prs_merged branch and
            # the detail query below share both predicates, so the footer's total, the
            # per-repo lines and the model's item list cannot disagree.
            merged_total = conn.execute(
                f"""
                SELECT COUNT(DISTINCT {canonical} || '#' || number)
                FROM github_items
                WHERE item_type = 'pull_request'
                  AND datetime(merged_at) >= :start AND datetime(merged_at) < :end
                """,
                window,
            ).fetchone()[0]
            merged = [
                dict(r)
                for r in conn.execute(
                    f"""
                    SELECT {canonical} AS repo_full_name,
                           number, MAX(title) AS title, author_login,
                           MAX(merged_at)    AS merged_at
                    FROM github_items
                    WHERE item_type = 'pull_request'
                      AND datetime(merged_at) >= :start AND datetime(merged_at) < :end
                    GROUP BY {canonical}, number
                    ORDER BY datetime(merged_at) DESC
                    LIMIT :limit
                    """,
                    {**window, "limit": ITEM_DETAIL_LIMIT},
                )
            ]

            # closed_not_merged deliberately spans BOTH item types — a closed issue is
            # part of the day's work — and dedupes on (canonical repo, number) for the
            # same mirror reason as merged_total.
            closed_total = conn.execute(
                f"""
                SELECT COUNT(DISTINCT {canonical} || '#' || number)
                FROM github_items
                WHERE datetime(closed_at) >= :start AND datetime(closed_at) < :end AND merged_at IS NULL
                """,
                window,
            ).fetchone()[0]
            closed = [
                dict(r)
                for r in conn.execute(
                    f"""
                    SELECT {canonical} AS repo_full_name,
                           item_type, number, MAX(title) AS title
                    FROM github_items
                    WHERE datetime(closed_at) >= :start AND datetime(closed_at) < :end
                      AND merged_at IS NULL
                    GROUP BY {canonical}, number
                    ORDER BY datetime(closed_at) DESC
                    LIMIT :limit
                    """,
                    {**window, "limit": ITEM_DETAIL_LIMIT},
                )
            ]
    except sqlite3.Error as e:
        return _fail("github collector failed", e)

    # First line of each commit message is the subject; the body is noise for a digest.
    # Scrubbed like every other string bound for the prompt: a commit subject such as
    # "fix: point the loader at /Users/<name>/Library/..." otherwise carries a home path,
    # and with it a username, verbatim into a team channel.
    for c in commits:
        subject = (c.get("message") or "").splitlines()[0][:140] if c.get("message") else ""
        c["message"] = _scrub(subject)
    for item in (*merged, *closed):
        item["title"] = _scrub(item.get("title") or "")

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


# How stale a watched repo's per-repo sync timestamp may be before the digest names it.
# The hourly github-sync walks ~60+ repos sequentially and a full run can take over an
# hour, so the floor must clear one whole cadence plus one whole run; 180 min does.
# A repo failing its sync (rate-limit 403, see #147/#148) crosses this and is reported
# instead of reading as a quiet day. Same "never imply a quiet day when a collector
# failed" contract as the prompt's error rule.
STALE_REPO_LAG_MINUTES = 180
STALE_REPO_DETAIL_LIMIT = 8


def collect_repo_freshness(db: Path, now: datetime) -> list[dict[str, Any]]:
    """Watched repos whose data may under-report today (#147).

    Two signals, both canonicalized through the org-alias collapse:

    - ``github_repo_meta.fetched_at`` — written by every successful per-repo sync, so a
      repo trailing *now* by more than :data:`STALE_REPO_LAG_MINUTES` has missed at least
      one full sync cycle (rate-limit 403, sync overrun, watchlist churn). This catches
      exactly the #147 shape: a repo merged 3 PRs while its rows were last touched hours
      earlier, and the digest said nothing.
    - ``github_repo_coverage`` rows in a non-ok state — the local-git backfill's verdict
      (``uncoverable``/``stale``) with its reason, so a repo whose commit corpus cannot be
      verified is named rather than trusted.

    Only repos in the CURRENT watched set are reported: a repo that aged out of
    monitoring legitimately has a frozen timestamp, and re-reporting it forever would
    train the channel to ignore the line.
    """
    try:
        from rebalance.ingest.config import canonical_github_repo_name
        from rebalance.ingest.index_ops import get_watched_repos

        watched_lower = {canonical_github_repo_name(r).lower() for r in get_watched_repos(Path(db))["watched"]}
    except Exception as e:  # noqa: BLE001 — freshness must never kill the digest
        return [{"error": _scrub(f"watched-set resolve failed: {e}")}]

    entries: dict[str, dict[str, Any]] = {}
    try:
        with db_connection_readonly(db) as conn:
            rows = conn.execute(
                "SELECT repo_full_name, MAX(fetched_at) AS last_fetched FROM github_repo_meta GROUP BY repo_full_name"
            ).fetchall()
            for r in rows:
                repo = canonical_github_repo_name(r["repo_full_name"] or "")
                if repo.lower() not in watched_lower:
                    continue
                fetched = _as_utc(r["last_fetched"] or "")
                if fetched is None:
                    continue
                lag_minutes = (now - fetched).total_seconds() / 60  # raw-ok: staleness, not an event duration
                if lag_minutes >= STALE_REPO_LAG_MINUTES:
                    entries[repo.lower()] = {
                        "repo": repo,
                        "reason": f"not synced since {r['last_fetched']} ({round(lag_minutes / 60)}h ago)",
                    }
            try:
                coverage_rows = conn.execute(
                    "SELECT repo_full_name, state, reason FROM github_repo_coverage WHERE state != 'ok'"
                ).fetchall()
            except sqlite3.Error:
                coverage_rows = []  # table may not exist on a fresh install
            for r in coverage_rows:
                repo = canonical_github_repo_name(r["repo_full_name"] or "")
                if repo.lower() not in watched_lower:
                    continue
                reason = f"commit corpus {r['state']}"
                if r["reason"]:
                    reason += f" ({_scrub(str(r['reason']))})"
                existing = entries.get(repo.lower())
                if existing:
                    existing["reason"] += f"; {reason}"
                else:
                    entries[repo.lower()] = {"repo": repo, "reason": reason}
    except sqlite3.Error as e:
        # Partial data plus the error — the rows already gathered still name real
        # stale repos; dropping them to report only the error would hide signal.
        partial = sorted(entries.values(), key=lambda entry: entry["repo"])
        partial.append({"error": _scrub(f"freshness query failed: {e}")})
        return partial

    stale = sorted(entries.values(), key=lambda e: e["repo"])
    if len(stale) > STALE_REPO_DETAIL_LIMIT:
        trimmed = stale[:STALE_REPO_DETAIL_LIMIT]
        trimmed.append({"repo": f"+{len(stale) - STALE_REPO_DETAIL_LIMIT} more", "reason": "list truncated"})
        return trimmed
    return stale


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

    # Shape-check before iterating. `payload.get("checks", [])` only defaults when the key
    # is ABSENT — a doctor that emits {"checks": null} yields None and the for-loop raises
    # TypeError out of this collector, out of build_facts and out of run(), killing the
    # whole digest. This is the one collector that shells out to another program, so it is
    # the one most able to be handed a shape it did not expect; the documented contract is
    # that a collector records its failure IN the facts instead.
    if not isinstance(payload, dict):
        return _fail("doctor output was not a JSON object", type(payload).__name__)
    checks = payload.get("checks") or []
    if not isinstance(checks, list):
        return _fail("doctor 'checks' was not a list", type(checks).__name__)

    problems = [
        {
            "name": c.get("name"),
            "status": c.get("status"),
            "disposition": c.get("disposition"),
            "detail": _scrub(c.get("detail") or "")[:200],
        }
        for c in checks
        if isinstance(c, dict) and c.get("disposition") == "problem"
    ]
    return {
        "verdict": payload.get("verdict"),
        "problem_count": len(problems),
        "problems": problems,
    }


def collect_semantic(db: Path, bounds: tuple[str, str]) -> dict[str, Any]:
    """Date-bounded semantic search over the BGE index, filtered to GitHub sources.

    source_filter is REQUIRED — see the module docstring. Titles are deduped because the
    index legitimately holds several near-identical chunks of the same document.

    Takes the same UTC *bounds* as collect_github rather than a local date string.
    search_semantic_documents filters with a RAW `sd.updated_at >= ?` (db/semantic.py:507)
    — no datetime() normalization — and the column mixes 'Z' and '+HH:MM' forms, so no
    single string bound is correct for both. The SQL bound is therefore only a widened
    prefilter and the real window is applied here on parsed instants.
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

    start_utc, end_utc = bounds
    window_start = datetime.strptime(start_utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    window_end = datetime.strptime(end_utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    try:
        rows = semantic_index.query(
            db,
            SEMANTIC_QUERY,
            top_k=SEMANTIC_TOP_K,
            updated_after=_semantic_prefilter_bound(start_utc),
            source_filter=SEMANTIC_SOURCES,
        )
    except Exception as e:  # noqa: BLE001 — any failure degrades this slot, never the run
        return _fail("semantic query failed", e)

    seen: set[str] = set()
    hits: list[dict[str, Any]] = []
    for r in rows:
        # The SQL bound only prefilters (see _semantic_prefilter_bound); the real window is
        # applied here, on parsed instants, because updated_at mixes 'Z' and '+HH:MM' forms
        # and a raw string compare is meaningless across the two. This also supplies the
        # upper bound db/semantic.py has no parameter for, so a future-stamped document
        # cannot ride into today's digest.
        updated = _as_utc(r.get("updated_at") or "")
        if updated is None or not (window_start <= updated < window_end):
            continue
        # source_pk, not source_id: query() builds its result dicts by hand
        # (semantic_index.py:824-838) and there is no source_id key, so the old fallback was
        # always None. title is already normalized to '' there, so a titleless github
        # document hit `if not title: continue` and was dropped in silence — the IN FLIGHT
        # section read as "nothing in flight" when the truth was a degraded query.
        title = _scrub((r.get("title") or r.get("source_pk") or "").strip())
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        hits.append({"title": title[:160], "source_type": r.get("source_type")})

    return {"query": SEMANTIC_QUERY, "sources": SEMANTIC_SOURCES, "hits": hits}


def build_facts(db: Path, now: datetime) -> dict[str, Any]:
    today = now.strftime("%Y-%m-%d")
    bounds = _utc_day_bounds(now)
    github = collect_github(db, bounds)
    # Freshness is attached separately so a failure in either half cannot take out
    # the other: the day's counts and the "which repos may be under-reported" verdict
    # are independent facts (#147).
    github.setdefault("stale_repos", collect_repo_freshness(db, now))
    return {
        "date": today,
        "generated_at": now.isoformat(timespec="seconds"),
        "window": "midnight to now, local time",
        "window_utc": {"start": bounds[0], "end": bounds[1]},
        "github": github,
        "health": collect_health(),
        "semantic": collect_semantic(db, bounds),
    }


# --- Synthesis -----------------------------------------------------------------


class SynthesisUnconfigured(Exception):
    """The machine was never set up to synthesize — not a failure of this run.

    A missing Gemini key is operator state, like the kill switch, and the installer says so
    explicitly: the key is hand-added to the RENDERED plist and a reinstall overwrites it
    (install_hiqs_digest_scheduler.sh:19-23). Treating that as a failed job writes
    job_failed to auth_activity.jsonl twice a day, which doctor's _check_auth_failures
    raises as an `auth:launchd` ERROR and health_issue_reporter files as a GitHub issue —
    for a machine that is merely unconfigured, and indistinguishably from a real Gemini
    outage. run() returns 0 for this and non-zero for everything else.
    """


def synthesize(facts: dict[str, Any]) -> str | None:
    """Gemini-only. Returns None if the call failed — the caller writes nothing.

    NO fallback model. A degraded summary posted to a team channel is worse than silence,
    because nobody can tell it apart from a good one.

    Raises SynthesisUnconfigured when the machine has no API key, so run() can exit 0 for
    "never set up" while still exiting non-zero for "tried and failed".
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
        raise SynthesisUnconfigured("no Gemini API key")

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
        # "Active" means shipped something — a commit or a merge. by_repo deliberately
        # also carries repos whose only event was an opened issue, so the model can see
        # them, but len(by_repo) as the footer count announced "3 active repos" on a day
        # when three people merely filed issues in three idle repos, while the model
        # correctly named none of them (prompt rule 2: never list a repo that shipped
        # nothing). The footer and the prose have to mean the same thing by "active".
        shipped = [r for r in gh.get("by_repo", []) if (r.get("commits") or 0) or (r.get("prs_merged") or 0)]
        counts.append(f"{len(shipped)} active repos")
        # Stale repos ride in the footer so the caveat survives even a model that
        # fumbles the HEALTH line: "10 merged · 4 active repos · 2 repos data-stale"
        # cannot be misread the way a silent omission can (#147).
        stale = [r for r in gh.get("stale_repos", []) if isinstance(r, dict) and r.get("repo") and "error" not in r]
        if stale:
            counts.append(f"{len(stale)} repos data-stale")
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
    #
    # Validated for the same reason --slot is choices-constrained. This value is
    # interpolated into a path that _commit_and_push_if_changed mkdir -p's and writes
    # BEFORE git sees it, so '../../../../tmp/x' or an absolute '/tmp/x' (pathlib discards
    # the left operand for an absolute right one) writes the digest to an arbitrary
    # location and then fails at `git add` with an error that never names the real cause.
    subdir = os.environ.get("HIQS_DIGEST_SUBDIR", "digests").strip()
    if not _is_safe_subdir(subdir):
        return {"ok": False, "reason": f"HIQS_DIGEST_SUBDIR is not a relative path inside the repo: {subdir!r}"}
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
        # The spread goes FIRST. _commit_and_push_if_changed returns its own "reason" on
        # the wrote-file-but-nothing-staged path (pulse.py:1045) — e.g. the pulse repo
        # gitignores digests/ — and with the spread last that bare "nothing staged"
        # overwrote the diagnostic below, hiding the only text naming the cause.
        return {
            **result,
            "ok": False,
            "reason": _scrub(f"git publish failed: {result.get('git_error') or result}"),
            "file_rel": file_rel,
        }
    return {**result, "ok": True, "file_rel": file_rel}


# --- Orchestration -------------------------------------------------------------


def run(
    *,
    dry_run: bool = False,
    facts_only: bool = False,
    slot: str | None = None,
    push: bool = True,
    now: datetime | None = None,
) -> int:
    # time_ops.local_tz() returns a real ZoneInfo and honours REBALANCE_TZ — the same
    # resolver pulse.py, doctor.py and next_actions.py use. `datetime.now().astimezone()`
    # returns a FIXED-OFFSET tzinfo instead, which is both DST-blind for the day bounds and
    # deaf to the configured zone, so this job's "today" could disagree with the pulse page
    # sitting next to it in the same repo.
    now = now or datetime.now(local_tz())
    explicit_slot = slot is not None
    slot = slot or slot_for(now)

    # Post-midnight catch-up guard, mirroring daily-synthesis's RUN_HOUR_FLOOR
    # (daily_synthesis.py:63-67; SCHEDULER.md records it as "a post-midnight catch-up
    # skips itself"). launchd derives nothing from the fire time it MISSED: a 17:05 job
    # slept through on Sep 1 and run at 07:00 on Sep 2 would build `today` and `slot` from
    # the wake time and publish hiqs-2026-09-02-1305.md summarizing seven empty hours of a
    # brand-new day — while Sep 1's evening work is never digested at all. That post does
    # not read as late; it reads as an on-time, quiet midday digest, so generated_at (this
    # job's entire observability design) cannot save it.
    #
    # Exit 0: a skipped catch-up is correct behaviour, not a failed job.
    if not (dry_run or facts_only or explicit_slot) and now.time() < FIRE_MIDDAY:
        log(
            f"SKIP: {now:%H:%M} is before the {FIRE_MIDDAY:%H:%M} midday slot — this is a "
            "post-midnight catch-up of a missed run, and today has barely started. "
            "Pass --slot to publish anyway."
        )
        return 0

    # The kill switch is checked BEFORE collection, not after. Collecting costs a
    # `rebalance doctor` subprocess (180s cap) and an MLX embedding load for the semantic
    # query; an operator who set the switch to stop this job's cost should not still pay
    # both twice a day to publish nothing. --facts-only deliberately still collects: it
    # makes no LLM call, so the switch has no bearing on it.
    if not facts_only and os.environ.get(LLM_DISABLE_ENV) == "1":
        log(f"{LLM_DISABLE_ENV}=1 — synthesis disabled by operator; nothing collected or published.")
        return 0

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

    # An unconfigured machine is operator state, not a failed run — same reasoning as the
    # kill switch above. Exit 0 so the dashboard does not show a red job twice a day
    # forever on a device where the API key was simply never added.
    try:
        summary = synthesize(facts)
    except SynthesisUnconfigured as e:
        log(f"{e} — this machine is not set up to synthesize; nothing published.")
        return 0
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
    # choices=, not a free string. The slot IS the filename the relay dedupes on, so
    # `--slot 1412` mints a name it has never seen and posts the day a third time, and
    # `--slot ../../notes` escapes the digests/ directory it watches entirely.
    parser.add_argument(
        "--slot",
        choices=(SLOT_MIDDAY, SLOT_EVENING),
        help=f"slot label (default: bucketed from the clock — {SLOT_MIDDAY} or {SLOT_EVENING})",
    )
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
