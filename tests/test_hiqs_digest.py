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
from datetime import datetime, timedelta
from pathlib import Path
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


def _bounds(now: datetime) -> tuple[str, str]:
    return hiqs_digest._utc_day_bounds(now)


def _commit(conn, repo: str, msg: str, at: str, *, login: str = "me", sha: str | None = None) -> None:
    conn.execute(
        "INSERT INTO github_commits (repo_full_name, item_type, item_number, sha, author_login, "
        "message, committed_at, fetched_at) VALUES (?,'pull_request',1,?,?,?,?,'x')",
        (repo, sha or f"sha-{msg}-{at}", login, msg, at),
    )


def _direct_commit(conn, repo: str, msg: str, at: str, *, login: str = "me") -> None:
    conn.execute(
        "INSERT INTO github_direct_commits (repo_full_name, sha, event_id, author_login, message, "
        "committed_at, discovered_at, fetched_at) VALUES (?,?,?,?,?,?,'x','x')",
        (repo, f"dsha-{msg}-{at}", f"ev-{msg}", login, msg, at),
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
    facts = hiqs_digest.collect_github(db, _bounds(now))

    assert "error" not in facts
    assert facts["by_repo"] == []
    assert facts["commit_total"] == 0


def test_broken_db_reports_an_error_rather_than_a_quiet_day(tmp_path: Path):
    """THE important one: a missing table must not read as 'nothing happened today'."""
    broken = tmp_path / "broken.db"
    sqlite3.connect(broken).close()  # valid sqlite file, no tables
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)

    facts = hiqs_digest.collect_github(broken, _bounds(now))

    assert "error" in facts, "a failed collector must surface an error, not empty data"
    assert "by_repo" not in facts, "error case must not also present empty results"


def test_collector_errors_are_scrubbed_of_the_home_path(monkeypatch, tmp_path: Path):
    """Error strings reach the prompt, and the prompt tells the model to report them."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    broken = tmp_path / "broken.db"
    sqlite3.connect(broken).close()
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)

    error = hiqs_digest.collect_github(broken, _bounds(now))["error"]

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

    facts = hiqs_digest.collect_github(db, _bounds(now))

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

    facts = hiqs_digest.collect_github(db, _bounds(now))

    assert sum(r["commits"] for r in facts["by_repo"]) == facts["commit_total"] == 3


def test_push_only_repo_is_not_dropped_from_by_repo(db: Path):
    """A repo whose whole day was direct pushes must still count as active."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _direct_commit(conn, "org/pushonly", "straight to main", "2026-09-01T18:00:00Z")

    by_repo = hiqs_digest.collect_github(db, _bounds(now))["by_repo"]

    assert [r["repo_full_name"] for r in by_repo] == ["org/pushonly"]
    assert by_repo[0]["commits"] == 1


def test_by_repo_counts_contributors_across_logins_without_double_listing(db: Path):
    """Operator choice (GH-142): all contributors, one row per repo — this is a team channel."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/shared", "a", "2026-09-01T18:00:00Z", login="alice")
        _commit(conn, "org/shared", "b", "2026-09-01T19:00:00Z", login="bob")
        _direct_commit(conn, "org/shared", "c", "2026-09-01T20:00:00Z", login="alice")

    by_repo = hiqs_digest.collect_github(db, _bounds(now))["by_repo"]

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

    by_repo = hiqs_digest.collect_github(db, _bounds(now))["by_repo"]

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

    facts = hiqs_digest.collect_github(db, _bounds(now))

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

    facts = hiqs_digest.collect_github(db, _bounds(now))

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

    facts = hiqs_digest.collect_github(db, _bounds(now))

    assert facts["commit_total"] == 2
    assert sorted(c["source"] for c in facts["commits"]) == ["pr", "push"]


def test_commit_message_is_trimmed_to_its_subject(db: Path):
    """Commit bodies are noise. Parameterized so the newline is real, not a literal \\n."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        _commit(conn, "org/r", "fix: the thing\n\nlong body", "2026-09-01T18:00:00Z")

    commits = hiqs_digest.collect_github(db, _bounds(now))["commits"]

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


@pytest.mark.parametrize(
    ("moment", "start", "end"),
    [
        (datetime(2026, 11, 1, 13, 5), "2026-11-01 07:00:00", "2026-11-02 08:00:00"),
        (datetime(2026, 3, 8, 13, 5), "2026-03-08 08:00:00", "2026-03-09 07:00:00"),
        (datetime(2026, 9, 1, 13, 5), "2026-09-01 07:00:00", "2026-09-02 07:00:00"),
    ],
)
def test_day_bounds_are_dst_correct_for_the_fixed_offset_now_that_run_builds(
    pacific_process_tz, moment: datetime, start: str, end: str
):
    """run() calls datetime.now().astimezone(), which returns a FIXED-OFFSET tzinfo.

    THIS is the test that pins the production bug. The ZoneInfo cases above cannot:
    .replace(hour=0) on a real zone re-resolves the offset by itself, so they pass against
    the broken code too — verified by reverting the fix and watching them stay green. A
    fixed offset freezes whatever was in force at the moment of the call, so midnight gets
    stamped with the afternoon's offset and the window slips an hour on a transition day.
    """
    now = moment.astimezone()  # exactly the shape run() hands to _utc_day_bounds

    assert hiqs_digest._utc_day_bounds(now) == (start, end)


# --- Rendering ------------------------------------------------------------------


def test_render_surfaces_generated_at_and_real_totals():
    """A late launchd catch-up must announce its own lateness; totals must be totals."""
    now = datetime(2026, 9, 1, 23, 40, tzinfo=PACIFIC)
    facts = {
        "date": "2026-09-01",
        "github": {"commit_total": 177, "merged_total": 22, "commits": [1, 2], "by_repo": [1, 2]},
        "health": {"problem_count": 2},
    }

    out = hiqs_digest.render("a summary", facts, now)

    assert "23:40" in out, "generated_at must be rendered, not just stored"
    assert "177 commits" in out, "the footer reports the total, not the capped detail length"
    assert "22 merged" in out
    assert "2 health warnings" in out


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


def test_semantic_is_bounded_by_utc_in_the_columns_own_format(monkeypatch, db: Path):
    """search_semantic_documents compares updated_at RAW — no datetime() normalization.

    A local date string admitted the previous evening's work as today's in-flight themes,
    and a space-separated bound compares wrong against an ISO-Z column ('T' sorts above ' ').
    """
    index = _RecordingIndex()
    monkeypatch.setattr(rebalance.ingest, "semantic_index", index, raising=False)

    hiqs_digest.collect_semantic(db, _bounds(datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC)))

    assert index.kwargs["updated_after"] == "2026-09-01T07:00:00Z", "UTC start of the LOCAL day, ISO-Z"


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


def test_publish_treats_an_unchanged_file_as_success(monkeypatch, tmp_path: Path):
    """A same-slot re-run with identical content has nothing to do — that is not failure."""
    _stub_pulse(
        monkeypatch,
        tmp_path,
        {"wrote_file": False, "committed": False, "pushed": False, "reason": "no content change"},
    )

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC), "1305", dry_run=False, push=True)

    assert result["ok"] is True


def test_llm_kill_switch_never_calls_the_model(monkeypatch):
    monkeypatch.setenv(hiqs_digest.LLM_DISABLE_ENV, "1")

    assert hiqs_digest.synthesize({"anything": True}) is None


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
