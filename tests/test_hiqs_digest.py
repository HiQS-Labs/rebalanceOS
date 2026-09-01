"""Tests for utils/hiqs_digest.py (GH-142).

Covers the four behaviours that would silently produce a WRONG Slack post rather than
an obviously broken one:

  1. A failed collector reports its error instead of returning empty data. This repo has
     three documented cases of scheduled jobs reporting success while doing nothing
     (AEGIS-Sleuth-Slackbot#157); "0 commits" and "the query failed" must never look alike.
  2. Semantic hits are deduped by title. The index holds several near-identical chunks of
     the same document, and undeduped they crowd out everything else.
  3. generated_at is RENDERED, not merely stored — it is the entire observability design
     for a launchd job that can run late after a sleep.
  4. Every collector failing exits non-zero and publishes nothing.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from datetime import datetime
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


@pytest.fixture
def empty_db(tmp_path: Path) -> Path:
    """A schema-shaped but empty database — the 'quiet day' case."""
    db = tmp_path / "rebalance.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE github_activity (
                repo_full_name TEXT, scan_date TEXT, commits INT, prs_opened INT,
                prs_merged INT, issues_opened INT, issue_comments INT, reviews INT);
            CREATE TABLE github_commits (
                repo_full_name TEXT, message TEXT, author_login TEXT, committed_at TEXT);
            CREATE TABLE github_items (
                repo_full_name TEXT, item_type TEXT, number INT, title TEXT,
                merged_at TEXT, closed_at TEXT);
            """
        )
    return db


def test_quiet_day_is_not_an_error(empty_db: Path):
    """An empty-but-healthy database yields empty lists and NO error key."""
    facts = hiqs_digest.collect_github(empty_db, "2026-09-01")
    assert "error" not in facts
    assert facts["by_repo"] == []
    assert facts["commits"] == []


def test_broken_db_reports_an_error_rather_than_a_quiet_day(tmp_path: Path):
    """THE important one: a missing table must not read as 'nothing happened today'."""
    db = tmp_path / "broken.db"
    sqlite3.connect(db).close()  # valid sqlite file, no tables

    facts = hiqs_digest.collect_github(db, "2026-09-01")

    assert "error" in facts, "a failed collector must surface an error, not empty data"
    assert "by_repo" not in facts, "error case must not also present empty results"


def test_github_activity_excludes_zero_rows(empty_db: Path):
    """Repos with a row but no activity are noise in a digest and must be filtered out."""
    with sqlite3.connect(empty_db) as conn:
        conn.execute("INSERT INTO github_activity VALUES ('org/busy','2026-09-01',5,1,1,0,0,0)")
        conn.execute("INSERT INTO github_activity VALUES ('org/idle','2026-09-01',0,0,0,0,0,0)")

    repos = hiqs_digest.collect_github(empty_db, "2026-09-01")["by_repo"]

    assert [r["repo_full_name"] for r in repos] == ["org/busy"]


def test_commit_message_is_trimmed_to_its_subject(empty_db: Path):
    """Commit bodies are noise; only the subject line belongs in a digest."""
    # Parameterized on purpose: an inline literal would store a backslash-n rather
    # than a real newline, and the test would pass against broken trimming.
    with sqlite3.connect(empty_db) as conn:
        conn.execute(
            "INSERT INTO github_commits VALUES (?,?,?,?)",
            ("org/r", "fix: the thing\n\nlong body here", "me", "2026-09-01T10:00:00"),
        )

    commits = hiqs_digest.collect_github(empty_db, "2026-09-01")["commits"]

    assert commits[0]["message"] == "fix: the thing"


def test_semantic_hits_are_deduped_by_title(monkeypatch, tmp_path: Path):
    """The index legitimately holds several chunks of one document — collapse them."""
    fake_rows = [
        {"title": "Claude Code Prompt Log", "source_type": "github"},
        {"title": "claude code prompt log", "source_type": "github"},  # case variant
        {"title": "Claude Code Prompt Log", "source_type": "github"},
        {"title": "Actually shipped something", "source_type": "github"},
    ]

    class FakeIndex:
        @staticmethod
        def query(*_args, **_kwargs):
            return fake_rows

    import rebalance.ingest as ingest_pkg

    monkeypatch.setitem(sys.modules, "rebalance.ingest.semantic_index", FakeIndex)
    monkeypatch.setattr(ingest_pkg, "semantic_index", FakeIndex, raising=False)

    result = hiqs_digest.collect_semantic(tmp_path / "db.sqlite", "2026-09-01")

    titles = [h["title"] for h in result["hits"]]
    assert titles == ["Claude Code Prompt Log", "Actually shipped something"]


def test_semantic_always_filters_to_github_sources():
    """source_filter is required, not tuning — unfiltered the slot returns vault noise."""
    assert hiqs_digest.SEMANTIC_SOURCES == ["github"]


def test_render_surfaces_generated_at(tmp_path: Path):
    """A late launchd catch-up must announce its own lateness in the post itself."""
    now = datetime(2026, 9, 1, 23, 40)
    facts = {
        "date": "2026-09-01",
        "github": {"commits": [1, 2], "merged": [1], "by_repo": [1]},
        "health": {"problem_count": 2},
    }

    out = hiqs_digest.render("a summary", facts, now)

    assert "23:40" in out, "generated_at must be rendered, not just stored"
    assert "2026-09-01" in out
    assert "a summary" in out
    assert "2 commits" in out and "2 health warnings" in out


def test_render_survives_a_failed_collector():
    """The footer must not crash or invent counts when a collector errored."""
    facts = {
        "date": "2026-09-01",
        "github": {"error": "boom"},
        "health": {"error": "boom"},
    }

    out = hiqs_digest.render("degraded summary", facts, datetime(2026, 9, 1, 13, 5))

    assert "no deterministic counts available" in out


def test_llm_kill_switch_refuses_to_synthesize(monkeypatch):
    """CB-1: the env kill switch stops the Gemini call without a code change."""
    monkeypatch.setenv(hiqs_digest.LLM_DISABLE_ENV, "1")

    assert hiqs_digest.synthesize({"anything": True}) is None


def test_run_exits_nonzero_when_every_collector_fails(monkeypatch, tmp_path: Path):
    """Nothing to summarize must fail loudly, not publish an empty digest."""
    db = tmp_path / "rebalance.db"
    db.touch()
    monkeypatch.setenv("REBALANCE_DB", str(db))

    monkeypatch.setattr(hiqs_digest, "collect_github", lambda *_: {"error": "x"})
    monkeypatch.setattr(hiqs_digest, "collect_health", lambda: {"error": "x"})
    monkeypatch.setattr(hiqs_digest, "collect_semantic", lambda *_: {"error": "x"})

    published: list[object] = []
    monkeypatch.setattr(hiqs_digest, "publish", lambda *a, **k: published.append(a))

    assert hiqs_digest.run(dry_run=True) == 1
    assert published == [], "must not publish when there is nothing to summarize"
