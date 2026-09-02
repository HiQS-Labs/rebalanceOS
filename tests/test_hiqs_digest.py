"""Tests for utils/hiqs_digest.py (GH-142).

Every test here pins a way this job could publish something WRONG to a team channel, or
report success while publishing nothing — both worse than an obvious crash, because the
symptom is a plausible-looking post or a green dashboard.

Grouped by the failure they prevent:
  * Quiet day vs broken collector must never look alike.
  * The post must not state a false number (capped lists as totals, split per-login rows,
    an evening's commits attributed to tomorrow, PR commits without direct pushes).
  * A failed publish must not exit 0.
  * The documented kill switch must not read as a crash.
  * The slot label must stay one of two fixed values, or the relay's dedupe breaks.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    spec = importlib.util.spec_from_file_location("hiqs_digest", REPO_ROOT / "utils" / "hiqs_digest.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["hiqs_digest"] = module
    spec.loader.exec_module(module)
    return module


hiqs_digest = _load_module()

# US Pacific in September (UTC-7). The timezone bug this suite pins only appears off UTC.
PACIFIC = timezone(timedelta(hours=-7))


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """A schema-shaped but empty database — the 'quiet day' case."""
    path = tmp_path / "rebalance.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE github_activity (
                login TEXT, repo_full_name TEXT, scan_date TEXT, commits INT,
                prs_opened INT, prs_merged INT, issues_opened INT,
                issue_comments INT, reviews INT);
            CREATE TABLE github_commits (
                repo_full_name TEXT, message TEXT, author_login TEXT, committed_at TEXT);
            CREATE TABLE github_direct_commits (
                repo_full_name TEXT, message TEXT, author_login TEXT, committed_at TEXT);
            CREATE TABLE github_items (
                repo_full_name TEXT, item_type TEXT, number INT, title TEXT,
                author_login TEXT, merged_at TEXT, closed_at TEXT);
            """
        )
    return path


def _bounds(now: datetime) -> tuple[str, str]:
    return hiqs_digest._utc_day_bounds(now)


# --- Quiet day vs broken collector ---------------------------------------------


def test_quiet_day_is_not_an_error(db: Path):
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    facts = hiqs_digest.collect_github(db, "2026-09-01", _bounds(now))

    assert "error" not in facts
    assert facts["by_repo"] == []
    assert facts["commit_total"] == 0


def test_broken_db_reports_an_error_rather_than_a_quiet_day(tmp_path: Path):
    """THE important one: a missing table must not read as 'nothing happened today'."""
    broken = tmp_path / "broken.db"
    sqlite3.connect(broken).close()  # valid sqlite file, no tables
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)

    facts = hiqs_digest.collect_github(broken, "2026-09-01", _bounds(now))

    assert "error" in facts, "a failed collector must surface an error, not empty data"
    assert "by_repo" not in facts, "error case must not also present empty results"


def test_collector_errors_are_scrubbed_of_the_home_path(monkeypatch, tmp_path: Path):
    """Error strings reach the prompt, and the prompt tells the model to report them."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    broken = tmp_path / "broken.db"
    sqlite3.connect(broken).close()
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)

    error = hiqs_digest.collect_github(broken, "2026-09-01", _bounds(now))["error"]

    assert str(tmp_path) not in error, "home path must never ride into the prompt"


# --- The post must not state a false number ------------------------------------


def test_activity_is_summed_per_repo_not_listed_per_login(db: Path):
    """github_activity is keyed (login, repo, day) — raw rows double-count a shared repo."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO github_activity VALUES (?,?,?,?,?,?,?,?,?)",
            [
                ("alice", "org/shared", "2026-09-01", 3, 1, 1, 0, 0, 0),
                ("bob", "org/shared", "2026-09-01", 4, 0, 1, 2, 0, 0),
                ("alice", "org/idle", "2026-09-01", 0, 0, 0, 0, 0, 0),
            ],
        )

    repos = hiqs_digest.collect_github(db, "2026-09-01", _bounds(now))["by_repo"]

    assert len(repos) == 1, "one row per repo, not per login"
    assert repos[0]["repo_full_name"] == "org/shared"
    assert repos[0]["commits"] == 7, "counts are summed across contributors"
    assert repos[0]["prs_merged"] == 2
    assert repos[0]["contributors"] == 2


def test_totals_are_counted_separately_from_the_capped_detail(db: Path):
    """Reporting a LIMIT-capped list length as the day's total pins it on busy days."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    over = hiqs_digest.COMMIT_DETAIL_LIMIT + 12
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO github_commits VALUES (?,?,?,?)",
            [("org/r", f"fix {i}", "me", "2026-09-01T18:00:00Z") for i in range(over)],
        )

    facts = hiqs_digest.collect_github(db, "2026-09-01", _bounds(now))

    assert facts["commit_total"] == over, "the total is the real count"
    assert len(facts["commits"]) == hiqs_digest.COMMIT_DETAIL_LIMIT, "detail stays capped"


def test_evening_local_commits_are_not_pushed_to_tomorrow(db: Path):
    """date(committed_at) is UTC; a naive compare loses an evening's work off UTC.

    18:00 Pacific on Sep 1 stores as 2026-09-02T01:00:00Z. It belongs to Sep 1's digest.
    """
    now = datetime(2026, 9, 1, 17, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO github_commits VALUES (?,?,?,?)",
            [
                ("org/r", "evening work", "me", "2026-09-02T01:00:00Z"),  # 18:00 Sep 1 PDT
                ("org/r", "yesterday", "me", "2026-09-01T06:00:00Z"),  # 23:00 Aug 31 PDT
            ],
        )

    facts = hiqs_digest.collect_github(db, "2026-09-01", _bounds(now))

    messages = [c["message"] for c in facts["commits"]]
    assert "evening work" in messages, "18:00 local Sep 1 belongs to Sep 1"
    assert "yesterday" not in messages, "23:00 local Aug 31 does not"
    assert facts["commit_total"] == 1


def test_direct_pushes_are_counted_alongside_pr_commits(db: Path):
    """github_commits is PR-attached only; reading it alone contradicts by_repo counts."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO github_commits VALUES ('org/r','via pr','me','2026-09-01T18:00:00Z')")
        # Offset-bearing form, as this table actually stores it.
        conn.execute(
            "INSERT INTO github_direct_commits VALUES ('org/r','pushed straight','me','2026-09-01T11:00:00-07:00')"
        )

    facts = hiqs_digest.collect_github(db, "2026-09-01", _bounds(now))

    assert facts["commit_total"] == 2
    assert sorted(c["source"] for c in facts["commits"]) == ["pr", "push"]


def test_commit_message_is_trimmed_to_its_subject(db: Path):
    """Commit bodies are noise. Parameterized so the newline is real, not a literal \\n."""
    now = datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO github_commits VALUES (?,?,?,?)",
            ("org/r", "fix: the thing\n\nlong body", "me", "2026-09-01T18:00:00Z"),
        )

    commits = hiqs_digest.collect_github(db, "2026-09-01", _bounds(now))["commits"]

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
    ("hour", "expected"),
    [(13, "1305"), (14, "1305"), (9, "1305"), (15, "1705"), (17, "1705"), (23, "1705")],
)
def test_slot_buckets_to_one_of_two_fixed_labels(hour: int, expected: str):
    """A catch-up at 14:12 must overwrite the 1305 file, not mint a third filename.

    The relay dedupes on filename, so a free-form HHMM label means a late run and a manual
    re-run each post the same day again.
    """
    assert hiqs_digest.slot_for(datetime(2026, 9, 1, hour, 12, tzinfo=PACIFIC)) == expected


# --- Publish + exit codes -------------------------------------------------------


def test_publish_reports_failure_when_the_push_fails(monkeypatch, tmp_path: Path):
    """_commit_and_push_if_changed has no 'ok' key — assuming success hides a dead job."""
    repo = tmp_path / "pulse"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.pulse",
        type(
            "M",
            (),
            {
                "_commit_and_push_if_changed": staticmethod(
                    lambda **kw: {
                        "wrote_file": True,
                        "committed": True,
                        "pushed": False,
                        "git_error": "non-fast-forward",
                    }
                )
            },
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.config",
        type("C", (), {"get_pulse_config": staticmethod(lambda: {"pulse_target_path": str(repo)})}),
    )

    result = hiqs_digest.publish("body", datetime(2026, 9, 1, 13, 5, tzinfo=PACIFIC), "1305", dry_run=False, push=True)

    assert result["ok"] is False, "a failed push must not report success"
    assert "non-fast-forward" in result["reason"]


def test_publish_treats_an_unchanged_file_as_success(monkeypatch, tmp_path: Path):
    """A same-slot re-run with identical content has nothing to do — that is not failure."""
    repo = tmp_path / "pulse"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.pulse",
        type(
            "M",
            (),
            {
                "_commit_and_push_if_changed": staticmethod(
                    lambda **kw: {
                        "wrote_file": False,
                        "committed": False,
                        "pushed": False,
                        "reason": "no content change",
                    }
                )
            },
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "rebalance.ingest.config",
        type("C", (), {"get_pulse_config": staticmethod(lambda: {"pulse_target_path": str(repo)})}),
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
    db_path = tmp_path / "rebalance.db"
    db_path.touch()
    monkeypatch.setattr(hiqs_digest, "resolve_database_path", lambda: db_path)
    monkeypatch.setattr(hiqs_digest, "build_facts", lambda *a: {"github": {}, "health": {}, "semantic": {}})
    monkeypatch.setenv(hiqs_digest.LLM_DISABLE_ENV, "1")

    published: list[object] = []
    monkeypatch.setattr(hiqs_digest, "publish", lambda *a, **k: published.append(a))

    assert hiqs_digest.run(dry_run=True) == 0
    assert published == [], "the switch stops publication as well as synthesis"


def test_run_exits_nonzero_when_every_collector_fails(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "rebalance.db"
    db_path.touch()
    monkeypatch.setattr(hiqs_digest, "resolve_database_path", lambda: db_path)
    monkeypatch.setattr(
        hiqs_digest,
        "build_facts",
        lambda *a: {"github": {"error": "x"}, "health": {"error": "x"}, "semantic": {"error": "x"}},
    )

    published: list[object] = []
    monkeypatch.setattr(hiqs_digest, "publish", lambda *a, **k: published.append(a))

    assert hiqs_digest.run(dry_run=True) == 1
    assert published == [], "must not publish when there is nothing to summarize"


def test_semantic_always_filters_to_github_sources():
    """source_filter is required, not tuning — unfiltered the slot returns vault noise."""
    assert hiqs_digest.SEMANTIC_SOURCES == ["github"]
