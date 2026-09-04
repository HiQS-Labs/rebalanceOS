"""Tests for utils/hiqs_digest.py (GH-142).

Every test here pins a way this job could publish something WRONG to a team channel, or
report success while publishing nothing — both worse than an obvious crash, because the
symptom is a plausible-looking post or a green dashboard.

Grouped by the failure they prevent:
  * Quiet day vs broken collector must never look alike.
  * The post must not state a false number (capped lists as totals, a rolling window's
    totals as one day's, an evening's commits attributed to tomorrow, PR commits without
    direct pushes, an hour lost or gained on a DST day).
  * A missed run must not publish the wrong day, or eat the next slot's filename.
  * A failed publish must not exit 0, and must keep the diagnosis.
  * The documented kill switch must not read as a crash.
  * The slot label must stay one of two fixed values, or the relay's dedupe breaks.

The fixture builds its tables with the PRODUCTION schema helper, not a hand-rolled subset.
A hand-rolled github_activity previously omitted the `pushes` column, which is exactly the
row shape that exposed a bug in the collector — the fixture could not represent the
failure it was supposed to catch.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

import rebalance.ingest
from rebalance.ingest.db import ensure_github_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    """Load utils/hiqs_digest.py from SOURCE, bypassing __pycache__.

    spec_from_file_location() hands back a SourceFileLoader, which honours the bytecode
    cache — and that cache is keyed on (mtime, size). Edit the module twice inside one
    second in a way that keeps the size equal (reordering two dict keys does exactly that)
    and the next run silently executes the PREVIOUS bytecode. Observed here: a green suite
    validating code that was no longer on disk.

    That is the same failure this whole module is written against — a check that reports
    success while measuring the wrong thing — so the harness compiles the source itself.
    """
    path = REPO_ROOT / "utils" / "hiqs_digest.py"
    module = types.ModuleType("hiqs_digest")
    module.__file__ = str(path)
    sys.modules["hiqs_digest"] = module
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)  # noqa: S102
    return module


hiqs_digest = _load_module()

# A REAL zone, not timezone(timedelta(hours=-7)). A fixed offset cannot express DST, and
# the day-bounds bug this suite pins only exists because production was handed one.
PACIFIC = ZoneInfo("America/Los_Angeles")


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """A schema-shaped but empty database — the 'quiet day' case."""
    path = tmp_path / "rebalance.db"
    conn = sqlite3.connect(path)
    ensure_github_schema(conn)
    conn.close()
    return path


def _all_repos(db: Path) -> set[str]:
    """Every repo present in the fixture's artifact tables, canonical-lowered.

    collect_github now REQUIRES a watched set (#159). These tests predate the filter and
    are about other properties, so they hand it everything they inserted — the filter is
    a no-op for them by construction. The tests that prove the filter actually CONSTRAINS
    are the contamination ones below; do not read this helper as coverage of it.
    """
    from rebalance.ingest.config import canonical_github_repo_name

    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT repo_full_name FROM github_commits "
            "UNION SELECT repo_full_name FROM github_direct_commits "
            "UNION SELECT repo_full_name FROM github_items"
        ).fetchall()
    return {canonical_github_repo_name(r[0]).lower() for r in rows} or {"none/inserted"}


def _bounds(now: datetime) -> tuple[str, str]:
    return hiqs_digest._utc_day_bounds(now)


def _commit(conn, repo: str, msg: str, at: str, *, login: str = "me", sha: str | None = None) -> None:
    conn.execute(
        "INSERT INTO github_commits (repo_full_name, item_type, item_number, sha, author_login, "
        "message, committed_at, fetched_at) VALUES (?,'pull_request',1,?,?,?,?,'x')",
        (repo, sha or f"sha-{msg}-{at}", login, msg, at),
    )


def _direct_commit(conn, repo: str, msg: str, at: str, *, login: str = "me", sha: str | None = None) -> None:
    conn.execute(
        "INSERT INTO github_direct_commits (repo_full_name, sha, event_id, author_login, message, "
        "committed_at, discovered_at, fetched_at) VALUES (?,?,?,?,?,?,'x','x')",
        (repo, sha or f"dsha-{msg}-{at}", f"ev-{msg}", login, msg, at),
    )


def _activity(conn, login: str, repo: str, scan_date: str, commits: int, pushes: int = 0) -> None:
    """A github_activity row — a 14-to-30-day WINDOW total stamped with today's date."""
    conn.execute(
        "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, "
        "prs_opened, prs_merged, issues_opened, issue_comments, reviews, scanned_at) "
        "VALUES (?,?,?,?,?,0,0,0,0,0,'x')",
        (login, repo, scan_date, commits, pushes),
    )


# --- Quiet day vs broken collector ---------------------------------------------


def test_quiet_day_is_not_an_error(db: Path):
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    assert "error" not in facts
    assert facts["by_repo"] == []
    assert facts["commit_total"] == 0


def test_a_commit_in_both_tables_is_counted_once(db: Path):
    """The two commit tables OVERLAP — a branch push that later lands in a PR is in both.

    Measured on the live database: 4,156 of 33,073 github_direct_commits rows share
    (repo, sha) with a github_commits row. A plain UNION ALL therefore overstated
    commit_total, double-counted the commit in by_repo, and handed the model the same
    subject twice — in a job whose contract is "never present a false number".
    pulse.py:255-263 reads the same pair of tables and has always guarded this.
    """
    conn = sqlite3.connect(db)
    _commit(conn, "org/a", "one thing", "2026-09-01T18:00:00Z", sha="deadbeef")
    _direct_commit(conn, "org/a", "one thing", "2026-09-01T18:00:00Z", sha="deadbeef")
    conn.commit()
    conn.close()

    facts = hiqs_digest.collect_github(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)), _all_repos(db))

    assert facts["commit_total"] == 1, "one commit in both tables is still one commit"
    assert [r["commits"] for r in facts["by_repo"]] == [1]
    assert len(facts["commits"]) == 1, "the model must not be shown the same subject twice"
    assert facts["commits"][0]["source"] == "pr", "'pr' is the more specific truth"


def test_duplicate_rows_within_github_commits_are_collapsed(db: Path):
    """github_commits alone has 2,680 repo+sha groups with more than one row on live data."""
    conn = sqlite3.connect(db)
    _commit(conn, "org/a", "one thing", "2026-09-01T18:00:00Z", sha="cafe")
    _commit(conn, "org/a", "one thing", "2026-09-01T18:00:00Z", sha="cafe")
    conn.commit()
    conn.close()

    facts = hiqs_digest.collect_github(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)), _all_repos(db))

    assert facts["commit_total"] == 1


def test_distinct_commits_are_not_collapsed(db: Path):
    """The dedupe must key on (repo, sha) — not flatten a busy day into one row."""
    conn = sqlite3.connect(db)
    _commit(conn, "org/a", "first", "2026-09-01T18:00:00Z", sha="aaa")
    _direct_commit(conn, "org/a", "second", "2026-09-01T19:00:00Z", sha="bbb")
    _direct_commit(conn, "org/b", "third", "2026-09-01T20:00:00Z", sha="aaa")  # same sha, other repo
    conn.commit()
    conn.close()

    facts = hiqs_digest.collect_github(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)), _all_repos(db))

    assert facts["commit_total"] == 3
    assert sorted(r["commits"] for r in facts["by_repo"]) == [1, 2]


def test_broken_db_reports_an_error_rather_than_a_quiet_day(tmp_path: Path):
    """THE important one: a missing table must not read as 'nothing happened today'."""
    broken = tmp_path / "broken.db"
    sqlite3.connect(broken).close()  # valid sqlite file, no tables
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)

    facts = hiqs_digest.collect_github(broken, _bounds(now), {"any/repo"})

    assert "error" in facts, "a failed collector must surface an error, not empty data"
    assert "by_repo" not in facts, "error case must not also present empty results"


def test_collector_errors_are_scrubbed_of_the_home_path(monkeypatch, tmp_path: Path):
    """Error strings reach the prompt, and the prompt tells the model to report them."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    broken = tmp_path / "broken.db"
    sqlite3.connect(broken).close()
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)

    error = hiqs_digest.collect_github(broken, _bounds(now), {"any/repo"})["error"]

    assert str(tmp_path) not in error, "home path must never ride into the prompt"


# --- The post must not state a false number ------------------------------------


def test_by_repo_never_reads_the_rolling_window_rollup_table(db: Path):
    """THE false-number test. github_activity looks per-day and is not.

    Every row holds a 14-to-30-day event-window total stamped with today's scan_date —
    github_watch.derive_watched_repo_activity() says so in its own docstring, and
    github_scan._summarize_by_repo() counts the whole fetched window with no day filter.
    Measured on live data, sourcing by_repo there reported 13 commits for a repo that
    landed 2, and 5 for one that landed 42. by_repo must come from the day-bounded event
    tables instead.
    """
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        # A fortnight of work for org/busy, and a repo idle today but active last week.
        _activity(conn, "me", "org/busy", "2026-09-01", commits=40, pushes=7)
        _activity(conn, "__watch__", "org/idle-today", "2026-09-01", commits=62)
        _commit(conn, "org/busy", "the only commit today", "2026-09-01T18:00:00Z")

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    by_repo = {r["repo_full_name"]: r for r in facts["by_repo"]}
    assert list(by_repo) == ["org/busy"], "a repo idle today must not be listed as active"
    assert by_repo["org/busy"]["commits"] == 1, "one commit landed today, not the window's 40"
    assert facts["commit_total"] == 1


def test_by_repo_and_the_footer_total_cannot_disagree(db: Path):
    """Both derive from the same day-bounded rows, so the post cannot contradict itself."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/a", "one", "2026-09-01T18:00:00Z")
        _commit(conn, "org/a", "two", "2026-09-01T19:00:00Z")
        _direct_commit(conn, "org/b", "three", "2026-09-01T20:00:00Z")

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    assert sum(r["commits"] for r in facts["by_repo"]) == facts["commit_total"] == 3


def test_push_only_repo_is_not_dropped_from_by_repo(db: Path):
    """A repo whose whole day was direct pushes must still count as active."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _direct_commit(conn, "org/pushonly", "straight to main", "2026-09-01T18:00:00Z")

    by_repo = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))["by_repo"]

    assert [r["repo_full_name"] for r in by_repo] == ["org/pushonly"]
    assert by_repo[0]["commits"] == 1


def test_by_repo_counts_contributors_across_logins_without_double_listing(db: Path):
    """Operator choice (GH-142): all contributors, one row per repo — this is a team channel."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/shared", "a", "2026-09-01T18:00:00Z", login="alice")
        _commit(conn, "org/shared", "b", "2026-09-01T19:00:00Z", login="bob")
        _direct_commit(conn, "org/shared", "c", "2026-09-01T20:00:00Z", login="alice")

    by_repo = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))["by_repo"]

    assert len(by_repo) == 1, "one row per repo, not per login"
    assert by_repo[0]["commits"] == 3
    assert by_repo[0]["contributors"] == 2


def test_case_variants_of_one_repo_are_not_counted_as_two(db: Path):
    """The tables carry rows written under different casings of the same owner/name.

    config.normalize_github_repo_name calls the lowercased form canonical, so grouping on
    the raw string listed one repo twice and inflated the "N active repos" footer with a
    repository that does not exist.
    """
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "Acme-Org/Widget-Service", "a", "2026-09-01T18:00:00Z")
        _commit(conn, "acme-org/widget-service", "b", "2026-09-01T19:00:00Z")

    by_repo = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))["by_repo"]

    assert len(by_repo) == 1, "one repo, however its name was cased when stored"
    assert by_repo[0]["repo_full_name"] == "acme-org/widget-service"
    assert by_repo[0]["commits"] == 2


def test_totals_are_counted_separately_from_the_capped_detail(db: Path):
    """Reporting a LIMIT-capped list length as the day's total pins it on busy days."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    over = hiqs_digest.COMMIT_DETAIL_LIMIT + 12
    with sqlite3.connect(db) as conn:
        for i in range(over):
            _commit(conn, "org/r", f"fix {i}", "2026-09-01T18:00:00Z", sha=f"s{i}")

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    assert facts["commit_total"] == over, "the total is the real count"
    assert len(facts["commits"]) == hiqs_digest.COMMIT_DETAIL_LIMIT, "detail stays capped"


def test_evening_local_commits_are_not_pushed_to_tomorrow(db: Path):
    """date(committed_at) is UTC; a naive compare loses an evening's work off UTC.

    18:00 Pacific on Sep 1 stores as 2026-09-02T01:00:00Z. It belongs to Sep 1's digest.
    """
    now = datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/r", "evening work", "2026-09-02T01:00:00Z")  # 18:00 Sep 1 PDT
        _commit(conn, "org/r", "yesterday", "2026-09-01T06:00:00Z")  # 23:00 Aug 31 PDT

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    messages = [c["message"] for c in facts["commits"]]
    assert "evening work" in messages, "18:00 local Sep 1 belongs to Sep 1"
    assert "yesterday" not in messages, "23:00 local Aug 31 does not"
    assert facts["commit_total"] == 1


def test_direct_pushes_are_counted_alongside_pr_commits(db: Path):
    """github_commits is PR-attached only; reading it alone contradicts by_repo counts."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/r", "via pr", "2026-09-01T18:00:00Z")
        # Offset-bearing form, as this table actually stores it.
        _direct_commit(conn, "org/r", "pushed straight", "2026-09-01T11:00:00-07:00")

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    assert facts["commit_total"] == 2
    assert sorted(c["source"] for c in facts["commits"]) == ["pr", "push"]


def test_commit_message_is_trimmed_to_its_subject(db: Path):
    """Commit bodies are noise. Parameterized so the newline is real, not a literal \\n."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/r", "fix: the thing\n\nlong body", "2026-09-01T18:00:00Z")

    commits = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))["commits"]

    assert commits[0]["message"] == "fix: the thing"


def test_health_filters_on_disposition_not_raw_status(monkeypatch):
    """A WARN the reconciler suppressed must not be republished as a live problem."""

    class FakeRun:
        returncode = 0
        stdout = (
            '{"verdict": "ok", "checks": ['
            '{"name":"live","status":"warning","disposition":"problem","detail":"real"},'
            '{"name":"recovered","status":"warning","disposition":"suppressed","detail":"hidden"},'
            '{"name":"fine","status":"ok","disposition":"ok","detail":""}]}'
        )

    monkeypatch.setattr(hiqs_digest.subprocess, "run", lambda *a, **k: FakeRun())

    health = hiqs_digest.collect_health()

    assert health["problem_count"] == 1
    assert [p["name"] for p in health["problems"]] == ["live"]


# --- Day bounds, including DST --------------------------------------------------


def test_day_bounds_cover_a_normal_24_hour_day():
    start, end = _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC))

    assert (start, end) == ("2026-09-01 07:00:00", "2026-09-02 07:00:00")


def test_day_bounds_are_correct_on_the_dst_end_day():
    """Nov 1 2026 is 25 hours long in Pacific: midnight is PDT, the next midnight is PST.

    Computing both from *now*'s fixed offset started the window an hour late and dropped
    every commit made between 00:00 and 01:00 local.
    """
    start, end = _bounds(datetime(2026, 11, 1, 13, 5, tzinfo=PACIFIC))

    assert start == "2026-11-01 07:00:00", "local midnight Nov 1 was still PDT (UTC-7)"
    assert end == "2026-11-02 08:00:00", "the next local midnight is PST (UTC-8)"


def test_day_bounds_are_correct_on_the_dst_start_day():
    """Mar 8 2026 is 23 hours long: midnight is PST, the next midnight is PDT."""
    start, end = _bounds(datetime(2026, 3, 8, 13, 5, tzinfo=PACIFIC))

    assert start == "2026-03-08 08:00:00"
    assert end == "2026-03-09 07:00:00"


def test_a_dst_day_is_not_assumed_to_be_24_hours():
    """The generic form of the two above — start + timedelta(days=1) is not the day's end."""
    for day, hours in ((datetime(2026, 11, 1), 25), (datetime(2026, 3, 8), 23)):
        start, end = _bounds(day.replace(hour=13, minute=5, tzinfo=PACIFIC))
        span = datetime.strptime(end, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        assert span == timedelta(hours=hours), f"{day:%Y-%m-%d} is {hours} local hours long"


@pytest.fixture
def pacific_process_tz():
    """Force the PROCESS timezone so the fixed-offset path is deterministic on any machine."""
    old = os.environ.get("TZ")
    os.environ["TZ"] = "America/Los_Angeles"
    time.tzset()
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old
        time.tzset()


def test_run_resolves_now_through_a_real_zone_not_a_fixed_offset(pacific_process_tz, monkeypatch):
    """This is the test that keeps the DST bug fixed.

    The three DST cases above cannot: `.replace(tzinfo=zone)` on a real ZoneInfo
    re-resolves the offset by itself, so they pass against a broken _local_midnight too.
    What actually protects the window is that run() builds `now` with time_ops.local_tz(),
    a real ZoneInfo. `datetime.now().astimezone()` returns a FIXED-OFFSET tzinfo that
    freezes whatever was in force at the moment of the call, so midnight gets stamped with
    the afternoon's offset and the window slips an hour on a transition day — and a fixed
    offset is also deaf to REBALANCE_TZ and the configured pulse timezone.
    """
    seen: dict[str, Any] = {}

    def _capture(db, now):
        seen["now"] = now
        raise SystemExit(0)  # stop run() before it does any real work

    monkeypatch.setattr(hiqs_digest, "build_facts", _capture)
    monkeypatch.setattr(hiqs_digest, "resolve_database_path", lambda: Path(__file__))

    with pytest.raises(SystemExit):
        hiqs_digest.run(slot="1305")

    assert isinstance(seen["now"].tzinfo, ZoneInfo), (
        "run() must resolve now through time_ops.local_tz(); a fixed-offset tzinfo is "
        "DST-blind and ignores REBALANCE_TZ"
    )


def test_local_midnight_honours_an_explicitly_passed_zone(pacific_process_tz):
    """A caller-supplied zone is used, not silently replaced by the machine's.

    An earlier version fell back to `naive.astimezone()` for any tz that was not a
    ZoneInfo, which DISCARDED the argument. run(now=<UTC+9 datetime>) under a Pacific
    process then bounded the day in Pacific while build_facts labelled the payload with the
    UTC+9 date — a digest with a plausible date, a window hours away from it, and zero rows
    in every collector.
    """
    tokyo = timezone(timedelta(hours=9))
    now = datetime(2026, 9, 2, 6, 0, tzinfo=tokyo)

    start, end = hiqs_digest._utc_day_bounds(now)

    # Local midnight in UTC+9 on Sep 2 is 2026-09-01 15:00 UTC, whatever the machine is set to.
    assert (start, end) == ("2026-09-01 15:00:00", "2026-09-02 15:00:00")


# --- Rendering ------------------------------------------------------------------


def test_render_surfaces_generated_at_and_real_totals():
    """A late launchd catch-up must announce its own lateness; totals must be totals."""
    now = datetime(2026, 9, 1, 23, 40, tzinfo=PACIFIC)
    facts = {
        "date": "2026-09-01",
        "github": {
            "commit_total": 177,
            "merged_total": 22,
            "commits": [1, 2],
            "by_repo": [
                {"repo_full_name": "org/a", "commits": 170, "prs_merged": 20},
                {"repo_full_name": "org/b", "commits": 7, "prs_merged": 2},
            ],
        },
        "health": {"problem_count": 2},
    }

    out = hiqs_digest.render("a summary", facts, now)

    assert "23:40" in out, "generated_at must be rendered, not just stored"
    assert "177 commits" in out, "the footer reports the total, not the capped detail length"
    assert "22 merged" in out
    assert "2 active repos" in out
    assert "2 health warnings" in out


def test_render_counts_only_repos_that_shipped_as_active():
    """by_repo carries issue-only repos so the model can see them; the footer must not.

    On a day when three people merely filed issues in three otherwise-idle repos, a
    len(by_repo) footer announced "3 active repos" while the model — correctly following
    the prompt's issue-only-omission rule — named none of them. The reader saw three
    active repos and no explanation of what they did.
    """
    facts = {
        "date": "2026-09-01",
        "github": {
            "commit_total": 4,
            "merged_total": 0,
            "by_repo": [
                {"repo_full_name": "org/shipped", "commits": 4, "prs_merged": 0, "issues_opened": 0},
                {"repo_full_name": "org/issue-only", "commits": 0, "prs_merged": 0, "issues_opened": 1},
                {"repo_full_name": "org/merged-only", "commits": 0, "prs_merged": 1, "issues_opened": 0},
            ],
        },
        "health": {"problem_count": 0},
    }

    out = hiqs_digest.render("a summary", facts, datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC))

    assert "2 active repos" in out, "commits or merges count as active; an opened issue does not"


def test_render_survives_a_failed_collector():
    facts = {"date": "2026-09-01", "github": {"error": "boom"}, "health": {"error": "boom"}}

    out = hiqs_digest.render("degraded", facts, datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC))

    assert "no deterministic counts available" in out


# --- Slot labelling -------------------------------------------------------------


@pytest.mark.parametrize(
    ("hour", "minute", "expected"),
    [
        (13, 5, "1305"),
        (14, 12, "1305"),
        (9, 0, "1305"),
        (15, 30, "1305"),  # the catch-up case pinned below
        (17, 4, "1305"),
        (17, 5, "1705"),
        (23, 0, "1705"),
    ],
)
def test_slot_buckets_to_one_of_two_fixed_labels(hour: int, minute: int, expected: str):
    """A catch-up at 14:12 must overwrite the 1305 file, not mint a third filename."""
    assert hiqs_digest.slot_for(datetime(2026, 9, 1, hour, minute, tzinfo=PACIFIC)) == expected


def test_a_late_midday_catchup_does_not_consume_the_evening_slot():
    """The boundary is the evening FIRE time, not an arbitrary mid-afternoon hour.

    Mac asleep from 12:00, woken 15:30: launchd fires the missed 13:05 job then. Under the
    old hour-15 boundary that midday run wrote the 1705 filename; the real 17:05 run
    overwrote it; the relay had already seen that name; NEITHER digest reached Slack.
    """
    catchup = datetime(2026, 9, 1, 15, 30, tzinfo=PACIFIC)
    real_evening = datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC)

    assert hiqs_digest.slot_for(catchup) == hiqs_digest.SLOT_MIDDAY
    assert hiqs_digest.slot_for(real_evening) == hiqs_digest.SLOT_EVENING
    assert hiqs_digest.slot_for(catchup) != hiqs_digest.slot_for(real_evening)


def test_slot_argument_rejects_a_free_form_label(monkeypatch, capsys):
    """--slot IS the filename. 1412 posts the day a third time; ../../notes escapes digests/."""
    for bad in ("1412", "../../notes"):
        monkeypatch.setattr(sys, "argv", ["hiqs_digest.py", "--slot", bad])
        with pytest.raises(SystemExit) as exc:
            hiqs_digest.main()
        assert exc.value.code != 0, f"--slot {bad} must be refused"
        capsys.readouterr()


# --- Missed runs must not publish the wrong day ---------------------------------


def _stub_run_deps(monkeypatch, tmp_path: Path) -> list[object]:
    db_path = tmp_path / "rebalance.db"
    db_path.touch()
    monkeypatch.setattr(hiqs_digest, "resolve_database_path", lambda: db_path)
    monkeypatch.setattr(
        hiqs_digest,
        "build_facts",
        lambda *a: {"date": "2026-09-01", "github": {}, "health": {}, "semantic": {}},
    )
    monkeypatch.setattr(hiqs_digest, "synthesize", lambda facts: "summary")
    published: list[object] = []
    monkeypatch.setattr(hiqs_digest, "publish", lambda *a, **k: (published.append(a), {"ok": True})[1])
    return published


def test_post_midnight_catchup_skips_instead_of_publishing_the_wrong_day(monkeypatch, tmp_path: Path):
    """A 17:05 job missed on Sep 1 and run at 07:00 Sep 2 must not publish.

    It would derive both the date and the slot from the WAKE time, producing
    hiqs-2026-09-02-1305.md summarizing seven empty hours of a brand-new day — while Sep
    1's evening work is never digested at all. The post does not read as late; it reads as
    an on-time, quiet midday digest, so generated_at cannot surface it.
    """
    published = _stub_run_deps(monkeypatch, tmp_path)

    rc = hiqs_digest.run(now=datetime(2026, 9, 2, 7, 0, tzinfo=PACIFIC))

    assert rc == 0, "a skipped catch-up is correct behaviour, not a failed job"
    assert published == [], "must not publish a digest of a day that has barely started"


def test_a_normal_midday_run_is_not_treated_as_a_catchup(monkeypatch, tmp_path: Path):
    """The negative control — the guard must not swallow the scheduled 13:05 run."""
    published = _stub_run_deps(monkeypatch, tmp_path)

    rc = hiqs_digest.run(now=datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC))

    assert rc == 0
    assert len(published) == 1, "the real midday job must still publish"


def test_an_explicit_slot_overrides_the_catchup_guard(monkeypatch, tmp_path: Path):
    """An operator passing --slot has said which slot they mean; don't second-guess them."""
    published = _stub_run_deps(monkeypatch, tmp_path)

    rc = hiqs_digest.run(now=datetime(2026, 9, 2, 7, 0, tzinfo=PACIFIC), slot=hiqs_digest.SLOT_EVENING)

    assert rc == 0
    assert len(published) == 1


# --- Semantic slot --------------------------------------------------------------


class _RecordingIndex:
    """Records the kwargs query() was called with, and returns canned rows."""

    def __init__(self, rows=()):
        self.rows = list(rows)
        self.kwargs: dict = {}

    def query(self, db, q, **kwargs):
        self.kwargs = kwargs
        return self.rows


def test_semantic_always_filters_to_github_sources(monkeypatch, db: Path):
    """source_filter is required, not tuning — unfiltered the slot returns vault noise.

    Asserting SEMANTIC_SOURCES == ["github"] restated a literal and would still have passed
    with the source_filter argument deleted. This pins the argument reaching query().
    """
    index = _RecordingIndex()
    monkeypatch.setattr(rebalance.ingest, "semantic_index", index, raising=False)

    hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)))

    assert index.kwargs["source_filter"] == ["github"]


def test_semantic_sql_bound_is_widened_because_the_column_mixes_formats(monkeypatch, db: Path):
    """The SQL bound only PREFILTERS; it is deliberately looser than the real window.

    search_semantic_documents compares updated_at RAW — no datetime() normalization — and
    the column is not one format: 24,509 of 60,431 github rows on the live index carry a
    numeric offset ('2026-09-01T16:45:05-07:00') rather than 'Z'. For an offset-form row
    the leading characters are LOCAL time, so a bound correct for one form is wrong for the
    other: a row stamped '2026-09-01T06:00:00-07:00' is 13:00 UTC, squarely inside the Sep 1
    Pacific day, yet '06' < '07' excludes it from a '2026-09-01T07:00:00Z' bound.

    So the bound is pushed back by the widest possible UTC offset (14h) and the real window
    is applied in Python. Over-fetching is safe; under-fetching reads to the channel as a
    quiet day.
    """
    index = _RecordingIndex()
    monkeypatch.setattr(rebalance.ingest, "semantic_index", index, raising=False)

    hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC)))

    # Local midnight Sep 1 Pacific is 2026-09-01 07:00 UTC; minus the 14h widening.
    assert index.kwargs["updated_after"] == "2026-08-31T17:00:00Z"


def test_semantic_keeps_offset_form_rows_inside_the_window(monkeypatch, db: Path):
    """The real window is applied on PARSED instants, so both stored forms are honoured.

    This is the row the raw string compare dropped: 06:00 local at UTC-7 is 13:00 UTC, well
    inside the Sep 1 Pacific day, but it sorts below an ISO-Z bound of 07:00. Measured on
    live data, the raw filter admitted 479 documents for that day where 501 were genuinely
    in-window.
    """
    index = _RecordingIndex(
        [
            {"title": "offset-form, inside", "source_type": "github", "updated_at": "2026-09-01T06:00:00-07:00"},
            {"title": "offset-form, yesterday", "source_type": "github", "updated_at": "2026-08-31T20:00:00-07:00"},
            {"title": "z-form, inside", "source_type": "github", "updated_at": "2026-09-01T18:00:00Z"},
        ]
    )
    monkeypatch.setattr(rebalance.ingest, "semantic_index", index, raising=False)

    hits = hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC)))["hits"]

    assert [h["title"] for h in hits] == ["offset-form, inside", "z-form, inside"]


def test_semantic_falls_back_to_source_pk_not_a_key_that_never_exists(monkeypatch, db: Path):
    """query() returns no source_id, so the old fallback silently dropped titleless docs."""
    index = _RecordingIndex(
        [
            {"title": "", "source_pk": "org/repo#42", "source_type": "github", "updated_at": "2026-09-01T18:00:00Z"},
            {"title": "A real title", "source_type": "github", "updated_at": "2026-09-01T19:00:00Z"},
        ]
    )
    monkeypatch.setattr(rebalance.ingest, "semantic_index", index, raising=False)

    hits = hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)))["hits"]

    assert [h["title"] for h in hits] == ["org/repo#42", "A real title"]


def test_semantic_drops_documents_stamped_beyond_the_day(monkeypatch, db: Path):
    """query() has no upper bound, so a future timestamp would ride into today's digest."""
    index = _RecordingIndex(
        [
            {"title": "today", "source_type": "github", "updated_at": "2026-09-01T18:00:00Z"},
            {"title": "tomorrow", "source_type": "github", "updated_at": "2026-09-03T18:00:00Z"},
        ]
    )
    monkeypatch.setattr(rebalance.ingest, "semantic_index", index, raising=False)

    hits = hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)))["hits"]

    assert [h["title"] for h in hits] == ["today"]


def test_semantic_failure_is_recorded_not_swallowed(monkeypatch, db: Path):
    """A degraded slot must never read as a quiet one."""

    class Boom:
        def query(self, *a, **k):
            raise RuntimeError("[metal::load_device] No Metal device available")

    monkeypatch.setattr(rebalance.ingest, "semantic_index", Boom(), raising=False)

    out = hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)))

    assert "error" in out and "hits" not in out


# --- Publish + exit codes -------------------------------------------------------


def _stub_pulse(monkeypatch, tmp_path: Path, result: dict) -> Path:
    repo = tmp_path / "pulse"
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.pulse",
        type("M", (), {"_commit_and_push_if_changed": staticmethod(lambda **kw: result)}),
    )
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.config",
        type("C", (), {"get_pulse_config": staticmethod(lambda: {"pulse_target_path": str(repo)})}),
    )
    return repo


def test_publish_reports_failure_when_the_push_fails(monkeypatch, tmp_path: Path):
    """_commit_and_push_if_changed has no 'ok' key — assuming success hides a dead job."""
    _stub_pulse(
        monkeypatch,
        tmp_path,
        {"wrote_file": True, "committed": True, "pushed": False, "git_error": "non-fast-forward"},
    )

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC), "1305", dry_run=False, push=True)

    assert result["ok"] is False, "a failed push must not report success"
    assert "non-fast-forward" in result["reason"]


def test_publish_failure_keeps_its_diagnosis_when_the_result_carries_a_reason(monkeypatch, tmp_path: Path):
    """pulse.py returns reason='nothing staged' when e.g. digests/ is gitignored.

    Spreading the result LAST overwrote the constructed diagnostic with that bare string,
    so the operator was told the digest did not publish but not that the destination is
    excluded from git — which is the whole diagnosis.
    """
    _stub_pulse(
        monkeypatch,
        tmp_path,
        {"wrote_file": True, "committed": False, "pushed": False, "reason": "nothing staged"},
    )

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC), "1305", dry_run=False, push=True)

    assert result["ok"] is False
    assert "git publish failed" in result["reason"], "the constructed diagnostic must survive"
    assert "nothing staged" in result["reason"], "and must still name the underlying cause"


def test_publish_writes_the_slot_into_the_filename(monkeypatch, tmp_path: Path):
    """The filename IS the contract — nothing else pinned it.

    The Sleuth relay's seen-set is keyed on the filename, so `hiqs-<date>-<slot>.md` is the
    single load-bearing invariant of this design. Every run() test stubs publish out and
    the other publish tests only read result["ok"], so swapping the now/slot arguments,
    dropping the slot from the f-string, or building the date from a different clock all
    passed the suite green while breaking the dedupe.
    """
    seen: dict[str, Any] = {}

    def _record(**kw):
        seen.update(kw)
        return {"wrote_file": True, "committed": True, "pushed": True}

    repo = tmp_path / "pulse"
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.pulse",
        type("M", (), {"_commit_and_push_if_changed": staticmethod(_record)}),
    )
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.config",
        type("C", (), {"get_pulse_config": staticmethod(lambda: {"pulse_target_path": str(repo)})}),
    )

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC), "1705", dry_run=False, push=True)

    assert seen["file_rel"] == "digests/hiqs-2026-09-01-1705.md"
    assert result["file_rel"] == "digests/hiqs-2026-09-01-1705.md"


@pytest.mark.parametrize("subdir", ["../../../../tmp/escape", "/tmp/abs", "digests/../..", ""])
def test_publish_rejects_a_subdir_that_escapes_the_repo(monkeypatch, tmp_path: Path, subdir: str):
    """HIQS_DIGEST_SUBDIR is interpolated into the path, exactly like --slot was.

    _commit_and_push_if_changed mkdir -p's and writes the file BEFORE git sees it, and
    `target_repo / file_rel` discards target_repo entirely for an absolute file_rel — so an
    unvalidated value writes the digest somewhere arbitrary and then fails at `git add`
    with an error that never names the real cause.
    """
    called: list[dict] = []
    repo = tmp_path / "pulse"
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.pulse",
        type("M", (), {"_commit_and_push_if_changed": staticmethod(lambda **kw: called.append(kw) or {})}),
    )
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.config",
        type("C", (), {"get_pulse_config": staticmethod(lambda: {"pulse_target_path": str(repo)})}),
    )
    monkeypatch.setenv("HIQS_DIGEST_SUBDIR", subdir)

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC), "1305", dry_run=False, push=True)

    assert result["ok"] is False
    assert not called, "nothing may be written for a rejected subdir"


def test_publish_treats_an_unchanged_file_as_success(monkeypatch, tmp_path: Path):
    """A same-slot re-run with identical content has nothing to do — that is not failure."""
    _stub_pulse(
        monkeypatch,
        tmp_path,
        {"wrote_file": False, "committed": False, "pushed": False, "reason": "no content change"},
    )

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC), "1305", dry_run=False, push=True)

    assert result["ok"] is True


def test_an_unconfigured_machine_exits_zero_rather_than_reporting_a_failed_job(monkeypatch):
    """No API key is operator state, like the kill switch — not a failure of this run.

    The installer says the key is hand-added to the RENDERED plist and that a reinstall
    overwrites it, so "never configured" is a normal state for a device. Exiting 1 wrote
    job_failed to auth_activity.jsonl twice a day, which doctor's _check_auth_failures
    raises as an auth:launchd ERROR and health_issue_reporter files as a GitHub issue —
    indistinguishable from a real Gemini outage.
    """
    monkeypatch.delenv(hiqs_digest.LLM_DISABLE_ENV, raising=False)
    monkeypatch.setattr(hiqs_digest, "resolve_database_path", lambda: Path(__file__))
    monkeypatch.setattr(hiqs_digest, "build_facts", lambda db, now: {n: {} for n in ("github", "health", "semantic")})
    monkeypatch.setattr(
        hiqs_digest,
        "synthesize",
        lambda facts: (_ for _ in ()).throw(hiqs_digest.SynthesisUnconfigured("no Gemini API key")),
    )

    assert hiqs_digest.run(slot="1305") == 0


def test_a_failed_synthesis_still_exits_non_zero(monkeypatch):
    """ "Tried and failed" is a real failure and must stay distinguishable from "never set up"."""
    monkeypatch.delenv(hiqs_digest.LLM_DISABLE_ENV, raising=False)
    monkeypatch.setattr(hiqs_digest, "resolve_database_path", lambda: Path(__file__))
    monkeypatch.setattr(hiqs_digest, "build_facts", lambda db, now: {n: {} for n in ("github", "health", "semantic")})
    monkeypatch.setattr(hiqs_digest, "synthesize", lambda facts: None)

    assert hiqs_digest.run(slot="1305") == 1


def test_kill_switch_skips_collection_entirely(monkeypatch):
    """The switch exists to stop this job's COST, which is mostly collection.

    Checked after build_facts, it still paid a `rebalance doctor` subprocess (180s cap) and
    an MLX embedding load twice a day in order to publish nothing.
    """
    monkeypatch.setenv(hiqs_digest.LLM_DISABLE_ENV, "1")

    def _never(*a, **k):
        raise AssertionError("collection must not run when the kill switch is set")

    monkeypatch.setattr(hiqs_digest, "build_facts", _never)

    assert hiqs_digest.run(slot="1305") == 0


def test_llm_kill_switch_never_calls_the_model(monkeypatch):
    monkeypatch.setenv(hiqs_digest.LLM_DISABLE_ENV, "1")

    assert hiqs_digest.synthesize({"anything": True}) is None


def test_doctor_payload_with_a_null_checks_key_is_recorded_not_raised(monkeypatch):
    """`payload.get("checks", [])` only defaults when the key is ABSENT.

    A doctor emitting {"checks": null} yielded None, and the comprehension raised
    TypeError out of the collector, out of build_facts and out of run() — killing the whole
    digest. This is the one collector that shells out to another program, so it is the one
    most able to be handed an unexpected shape; the contract is that it records the failure
    in the facts.
    """

    class FakeRun:
        stdout = '{"verdict": "ok", "checks": null}'
        returncode = 0

    monkeypatch.setattr(hiqs_digest.subprocess, "run", lambda *a, **k: FakeRun())

    out = hiqs_digest.collect_health()

    assert out["problem_count"] == 0, "a null checks list is an empty one, not a crash"


def test_doctor_payload_that_is_not_an_object_is_recorded_not_raised(monkeypatch):
    class FakeRun:
        stdout = "[1, 2, 3]"
        returncode = 0

    monkeypatch.setattr(hiqs_digest.subprocess, "run", lambda *a, **k: FakeRun())

    out = hiqs_digest.collect_health()

    assert "error" in out and "problems" not in out


def test_llm_kill_switch_exits_zero_not_failed(monkeypatch, tmp_path: Path):
    """The documented off switch is an operator no-op, not a crash.

    Returning non-zero makes the wrapper emit job_failed twice a day forever, rendered as
    a red job indistinguishable from a Gemini outage.
    """
    published = _stub_run_deps(monkeypatch, tmp_path)
    monkeypatch.setenv(hiqs_digest.LLM_DISABLE_ENV, "1")

    assert hiqs_digest.run(dry_run=True, now=datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)) == 0
    assert published == [], "the switch stops publication as well as synthesis"


def test_run_exits_nonzero_when_every_collector_fails(monkeypatch, tmp_path: Path):
    published = _stub_run_deps(monkeypatch, tmp_path)
    monkeypatch.setattr(
        hiqs_digest,
        "build_facts",
        lambda *a: {"github": {"error": "x"}, "health": {"error": "x"}, "semantic": {"error": "x"}},
    )

    assert hiqs_digest.run(dry_run=True, now=datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)) == 1
    assert published == [], "must not publish when there is nothing to summarize"


# --- Org-alias mirror collapse (#147) -------------------------------------------


@pytest.fixture
def org_alias(monkeypatch):
    """hiqs-suite → HiQS-Labs, as configured on the live machine.

    Patched on the config module (not the digest) because the alias map is read
    at call time by both the digest's SQL builder and the watched-set resolver —
    patching the one source keeps every consumer consistent.
    """
    from rebalance.ingest import config as config_module

    aliases = {"hiqs-suite": "HiQS-Labs"}
    monkeypatch.setattr(config_module, "get_github_org_aliases", lambda: aliases)
    return aliases


def _merged_pr(conn, repo: str, number: int, merged_at: str, title: str = "fix") -> None:
    conn.execute(
        "INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, "
        "merged_at, created_at, fetched_at) VALUES (?, 'pull_request', ?, ?, 'closed', 1, ?, ?, 'x')",
        (repo, number, title, merged_at, merged_at),
    )


def test_org_mirror_rows_collapse_into_one_repo(db: Path, org_alias):
    """The #147 footer said "10 merged · 6 active repos" for ~5 merged across 3 repos.

    A renamed org keeps its old URLs alive via redirects, so the same repo held
    rows under both spellings — same PR numbers, same commit SHAs — and every
    count read double.
    """
    now = datetime(2026, 9, 2, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "HiQS-Suite/xyz-forge", "old spelling", "2026-09-02T18:00:00Z", sha="abc123")
        _commit(conn, "HiQS-Labs/XYZ-forge", "new spelling", "2026-09-02T18:30:00Z", sha="abc123")
        _merged_pr(conn, "HiQS-Suite/xyz-forge", 10, "2026-09-02T19:00:00Z")
        _merged_pr(conn, "HiQS-Labs/XYZ-forge", 10, "2026-09-02T19:10:00Z")

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    assert [r["repo_full_name"] for r in facts["by_repo"]] == ["hiqs-labs/xyz-forge"]
    assert facts["by_repo"][0]["commits"] == 1, "same sha under both spellings is one commit"
    assert facts["commit_total"] == 1
    assert facts["merged_total"] == 1, "same PR number under both spellings is one merge"
    assert len(facts["merged"]) == 1


def test_a_same_named_fork_is_not_collapsed_into_the_org(db: Path, org_alias):
    """Forks share the repo segment but not the owner; only exact owner matches alias."""
    now = datetime(2026, 9, 2, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "arnoldadero/xyz-forge", "fork work", "2026-09-02T18:00:00Z", sha="f1")
        _commit(conn, "HiQS-Labs/xyz-forge", "upstream work", "2026-09-02T18:30:00Z", sha="f2")

    by_repo = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))["by_repo"]

    assert sorted(r["repo_full_name"] for r in by_repo) == ["arnoldadero/xyz-forge", "hiqs-labs/xyz-forge"]


def test_closed_items_dedupe_on_canonical_identity_too(db: Path, org_alias):
    now = datetime(2026, 9, 2, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        for repo in ("HiQS-Suite/xyz-forge", "HiQS-Labs/XYZ-forge"):
            conn.execute(
                "INSERT INTO github_items (repo_full_name, item_type, number, title, state, "
                "closed_at, created_at, fetched_at) VALUES (?, 'issue', 7, 'wontfix', 'closed', ?, ?, 'x')",
                (repo, "2026-09-02T18:00:00Z", "2026-09-02T17:00:00Z"),
            )

    facts = hiqs_digest.collect_github(db, _bounds(now), _all_repos(db))

    assert facts["closed_not_merged_total"] == 1
    assert len(facts["closed_not_merged"]) == 1


# --- Repo freshness (#147): a repo the sync missed is named, never implied quiet --


def _watched_via_push(conn, repo: str, at: str = "2026-09-02T00:00:00Z") -> None:
    """Make *repo* currently-watched via the pushed-repos window (14d)."""
    conn.execute(
        "INSERT INTO github_pushed_repos (repo_full_name, pushed_at, first_seen_at, last_seen_at) VALUES (?,?,?,?)",
        (repo, at, at, at),
    )


def _repo_meta(conn, repo: str, fetched_at: str) -> None:
    conn.execute(
        "INSERT INTO github_repo_meta (repo_full_name, fetched_at) VALUES (?,?)",
        (repo, fetched_at),
    )


def test_a_repo_the_sync_missed_is_named_stale(db: Path, org_alias):
    """The exact #147 shape: rate-limit 403s left one repo hours behind the fleet."""
    now = datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc)
    with sqlite3.connect(db) as conn:
        _watched_via_push(conn, "HiQS-Labs/fresh")
        _watched_via_push(conn, "HiQS-Suite/stale")  # watched under the old spelling
        _repo_meta(conn, "HiQS-Labs/fresh", "2026-09-02T13:30:00Z")
        _repo_meta(conn, "hiqs-suite/stale", "2026-09-02T09:00:00Z")  # 5h behind

    stale = hiqs_digest.collect_repo_freshness(db, now, hiqs_digest.resolve_watched_repos(db))

    named = [e for e in stale if "error" not in e]
    assert [e["repo"] for e in named] == ["HiQS-Labs/stale"], "canonical name, fresh repo absent"
    assert "not synced since" in named[0]["reason"]


def test_an_uncoverable_commit_corpus_is_named_with_its_reason(db: Path, org_alias):
    now = datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc)
    with sqlite3.connect(db) as conn:
        _watched_via_push(conn, "HiQS-Labs/noclone")
        _repo_meta(conn, "HiQS-Labs/noclone", "2026-09-02T13:30:00Z")  # item sync is fresh
        conn.execute(
            "INSERT INTO github_repo_coverage (repo_full_name, state, reason, checked_at) "
            "VALUES ('HiQS-Labs/noclone', 'uncoverable', "
            "'no local clone found under configured local_repo_roots', '2026-09-02T13:00:00Z')",
        )

    stale = hiqs_digest.collect_repo_freshness(db, now, hiqs_digest.resolve_watched_repos(db))

    assert [e["repo"] for e in stale] == ["HiQS-Labs/noclone"]
    assert "uncoverable" in stale[0]["reason"]
    assert "no local clone" in stale[0]["reason"]


def test_a_repo_that_left_the_watched_set_is_not_reported_forever(db: Path):
    """A repo that aged out of monitoring has a legitimately frozen timestamp."""
    now = datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc)
    with sqlite3.connect(db) as conn:
        _repo_meta(conn, "old/gone", "2026-08-01T00:00:00Z")  # stale, but not watched

    assert hiqs_digest.collect_repo_freshness(db, now, {"still/watched"}) == []


def test_the_stale_list_is_capped_with_an_overflow_marker(db: Path):
    now = datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc)
    with sqlite3.connect(db) as conn:
        for i in range(hiqs_digest.STALE_REPO_DETAIL_LIMIT + 3):
            repo = f"org/stale-{i}"
            _watched_via_push(conn, repo)
            _repo_meta(conn, repo, "2026-09-01T00:00:00Z")

    stale = hiqs_digest.collect_repo_freshness(db, now, hiqs_digest.resolve_watched_repos(db))

    assert len(stale) == hiqs_digest.STALE_REPO_DETAIL_LIMIT + 1
    assert stale[-1]["repo"] == "+3 more"


def test_build_facts_attaches_freshness_to_the_github_half(monkeypatch, db: Path):
    monkeypatch.setattr(hiqs_digest, "collect_health", lambda: {"problem_count": 0})
    monkeypatch.setattr(hiqs_digest, "collect_semantic", lambda *a: {"hits": []})
    entry = {"repo": "x/y", "reason": "not synced since earlier"}
    monkeypatch.setattr(hiqs_digest, "collect_repo_freshness", lambda *a: [entry])
    with sqlite3.connect(db) as conn:  # a watched set must resolve, or the half fails closed
        _watched_via_push(conn, "x/y")

    facts = hiqs_digest.build_facts(db, datetime(2026, 9, 2, 13, 5, tzinfo=PACIFIC))

    assert facts["github"]["stale_repos"] == [entry]


# --- Contamination (#159): an unwatched repo must not reach the channel ---------
# These are the tests that prove the watched-set filter CONSTRAINS. The other
# collect_github tests hand it everything they inserted, so the filter is inert there.


def _contaminated(conn) -> None:
    """One watched repo and one third-party repo, same day, identical row shapes."""
    _commit(conn, "HiQS-Labs/mine", "my work", "2026-09-01T18:00:00Z", login="me")
    _commit(conn, "DeusData/theirs", "their work", "2026-09-01T18:00:00Z", login="stranger")
    _direct_commit(conn, "DeusData/theirs", "their push", "2026-09-01T18:30:00Z", login="stranger")
    for repo, login, number in (("HiQS-Labs/mine", "me", 1), ("DeusData/theirs", "stranger", 2)):
        conn.execute(
            "INSERT INTO github_items (repo_full_name, item_type, number, title, author_login, "
            "created_at, merged_at, closed_at, fetched_at) VALUES (?,'pull_request',?,?,?,?,?,?,'x')",
            (repo, number, f"pr from {login}", login,
             "2026-09-01T17:00:00Z", "2026-09-01T18:00:00Z", "2026-09-01T18:00:00Z"),
        )


def test_an_unwatched_repos_merged_prs_never_reach_the_digest(db: Path):
    """The live 2026-09-03 defect: six strangers' merged PRs led the SHIPPED section."""
    now = datetime(2026, 9, 1, 20, 0, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _contaminated(conn)

    facts = hiqs_digest.collect_github(db, _bounds(now), {"hiqs-labs/mine"})

    assert [r["repo_full_name"] for r in facts["by_repo"]] == ["hiqs-labs/mine"]
    assert facts["merged_total"] == 1, "the ignored repo's merged PR must not be counted"
    assert [m["repo_full_name"] for m in facts["merged"]] == ["hiqs-labs/mine"]
    assert facts["commit_total"] == 1, "commits and direct pushes both filtered"
    assert all(c["repo_full_name"] == "hiqs-labs/mine" for c in facts["commits"])


def test_the_same_corpus_reports_the_third_party_repo_when_it_is_watched(db: Path):
    """The negative control: the filter is what removed it, not a broken fixture."""
    now = datetime(2026, 9, 1, 20, 0, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _contaminated(conn)

    facts = hiqs_digest.collect_github(db, _bounds(now), {"hiqs-labs/mine", "deusdata/theirs"})

    assert sorted(r["repo_full_name"] for r in facts["by_repo"]) == ["deusdata/theirs", "hiqs-labs/mine"]
    assert facts["merged_total"] == 2
    assert facts["commit_total"] == 3


def test_a_watched_repos_rows_survive_under_a_mirror_spelling(db: Path, org_alias):
    """Watched under the NEW org spelling, stored under the OLD one (#147)."""
    now = datetime(2026, 9, 1, 20, 0, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "HiQS-Suite/mine", "old spelling on disk", "2026-09-01T18:00:00Z")

    facts = hiqs_digest.collect_github(db, _bounds(now), {"hiqs-labs/mine"})

    assert facts["commit_total"] == 1, "an org mirror must not be filtered out as unwatched"


def test_an_unresolvable_watched_set_fails_the_github_half_closed(monkeypatch, db: Path):
    """No trustworthy watchlist means 'unavailable', never the whole artifact corpus."""
    monkeypatch.setattr(hiqs_digest, "collect_health", lambda: {"problem_count": 0})
    monkeypatch.setattr(hiqs_digest, "collect_semantic", lambda *a: {"hits": []})
    monkeypatch.setattr(hiqs_digest, "collect_github", lambda *a: pytest.fail("must not run unfiltered"))
    with sqlite3.connect(db) as conn:
        _contaminated(conn)  # a corpus that WOULD have been published

    facts = hiqs_digest.build_facts(db, datetime(2026, 9, 1, 20, 0, tzinfo=PACIFIC))

    assert "error" in facts["github"], "an unresolvable watched set must surface an error"
    assert "by_repo" not in facts["github"], "error case must not also present results"


def test_render_footer_names_stale_repos():
    facts = {
        "date": "2026-09-02",
        "github": {
            "commit_total": 3,
            "merged_total": 1,
            "by_repo": [{"repo_full_name": "org/a", "commits": 3, "prs_merged": 1}],
            "stale_repos": [
                {"repo": "org/late", "reason": "not synced since 09:00 (5h ago)"},
                {"repo": "org/late2", "reason": "not synced since 09:00 (5h ago)"},
            ],
        },
        "health": {"problem_count": 0},
    }

    out = hiqs_digest.render("summary", facts, datetime(2026, 9, 2, 13, 5, tzinfo=PACIFIC))

    assert "2 repos data-stale" in out


def test_render_does_not_count_a_freshness_error_as_a_stale_repo():
    facts = {
        "date": "2026-09-02",
        "github": {
            "commit_total": 0,
            "merged_total": 0,
            "by_repo": [],
            "stale_repos": [{"error": "freshness query failed: boom"}],
        },
        "health": {"problem_count": 0},
    }

    out = hiqs_digest.render("summary", facts, datetime(2026, 9, 2, 13, 5, tzinfo=PACIFIC))

    assert "data-stale" not in out


def test_the_prompt_names_stale_repos_and_no_longer_buries_commit_only_repos():
    """#147 cause 2: the old 'NEVER list a repository that shipped nothing' rule turned
    any ingest lag into a silent omission — with stale data, a repo carrying 21% of the
    day's commits was dropped outright."""
    prompt = hiqs_digest.PROMPT_TEMPLATE

    assert "github.stale_repos" in prompt, "HEALTH must be able to name stale repos"
    assert "NEVER list a repository that shipped nothing" not in prompt
    assert ">= 5 commits or opened" in prompt, "commit-only repos get a compact line"
