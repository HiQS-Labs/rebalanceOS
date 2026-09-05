"""GH-150 / 0.75.0 fe1: Mirror-invariance test for the shared SQL read layer.

Generalizes tests/test_hiqs_digest.py::test_org_mirror_rows_collapse_into_one_repo
across all query families in src/rebalance/ingest/db/queries.py.

Given a database with clean canonical data vs a database seeded with both canonical
and mirror org rows (sharing commit SHAs, PR numbers, activity rows, etc.), every
public function in db/queries.py MUST return identical, deduplicated results.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import rebalance.ingest.db.queries as queries_mod
from rebalance.ingest import config as config_module
from rebalance.ingest.db.schema import ensure_github_schema, ensure_schema

PACIFIC = ZoneInfo("America/Los_Angeles")


@pytest.fixture(autouse=True)
def org_alias(monkeypatch):
    aliases = {"hiqs-suite": "HiQS-Labs"}
    monkeypatch.setattr(queries_mod, "_get_alias_map", lambda: aliases)
    monkeypatch.setattr(config_module, "get_github_org_aliases", lambda: aliases)
    return aliases


def _seed_canonical_data(conn: sqlite3.Connection) -> None:
    now_iso = "2026-09-02T18:00:00Z"
    now_date = "2026-09-02"

    # Meta
    conn.execute(
        """
        INSERT INTO github_repo_meta (repo_full_name, default_branch, pushed_at, updated_at, open_issues_count, has_issues, has_projects, fetched_at)
        VALUES ('HiQS-Labs/xyz-forge', 'main', ?, ?, 2, 1, 1, ?)
        """,
        (now_iso, now_iso, now_iso),
    )

    # Milestones
    conn.execute(
        """
        INSERT INTO github_milestones (repo_full_name, number, title, description, state, open_issues, closed_issues, due_on, created_at, updated_at, closed_at, html_url)
        VALUES ('HiQS-Labs/xyz-forge', 1, 'v1.0', 'Release 1.0', 'open', 1, 1, '2026-09-30', ?, ?, NULL, 'https://github.com/HiQS-Labs/xyz-forge/milestone/1')
        """,
        (now_iso, now_iso),
    )

    # Items (PRs and issues)
    conn.execute(
        """
        INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, author_login, head_ref, base_ref, created_at, updated_at, fetched_at, html_url)
        VALUES ('HiQS-Labs/xyz-forge', 'pull_request', 10, 'feat: core engine', 'open', 0, 'noelsaw1', 'feature/core', 'main', ?, ?, ?, 'https://github.com/HiQS-Labs/xyz-forge/pull/10')
        """,
        (now_iso, now_iso, now_iso),
    )
    conn.execute(
        """
        INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, author_login, milestone_title, created_at, updated_at, fetched_at, html_url)
        VALUES ('HiQS-Labs/xyz-forge', 'issue', 5, 'bug: fix parsing', 'open', 0, 'noelsaw1', 'v1.0', ?, ?, ?, 'https://github.com/HiQS-Labs/xyz-forge/issues/5')
        """,
        (now_iso, now_iso, now_iso),
    )

    # PR commits
    conn.execute(
        """
        INSERT INTO github_commits (repo_full_name, item_type, item_number, sha, author_login, message, committed_at, html_url, fetched_at)
        VALUES ('HiQS-Labs/xyz-forge', 'pull_request', 10, 'abc1234567890', 'noelsaw1', 'feat(core): initial commit', ?, 'https://github.com/HiQS-Labs/xyz-forge/commit/abc1234', ?)
        """,
        (now_iso, now_iso),
    )

    # Direct commits
    conn.execute(
        """
        INSERT INTO github_direct_commits (event_id, repo_full_name, sha, ref, author_login, author_name, message, committed_at, html_url, path_coverage, discovered_at, fetched_at, source)
        VALUES ('evt_1', 'HiQS-Labs/xyz-forge', 'def9876543210', 'refs/heads/main', 'noelsaw1', 'Noel Saw', 'fix(direct): urgent patch', ?, 'https://github.com/HiQS-Labs/xyz-forge/commit/def9876', 'complete', ?, ?, 'events')
        """,
        (now_iso, now_iso, now_iso),
    )

    # Comments
    conn.execute(
        """
        INSERT INTO github_comments (repo_full_name, item_type, item_number, comment_type, github_comment_id, author_login, body, created_at, updated_at, fetched_at)
        VALUES ('HiQS-Labs/xyz-forge', 'pull_request', 10, 'issue_comment', 101, 'noelsaw1', 'LGTM ready to merge', ?, ?, ?)
        """,
        (now_iso, now_iso, now_iso),
    )

    # Links
    conn.execute(
        """
        INSERT INTO github_links (repo_full_name, source_type, source_number, target_type, target_number, link_kind)
        VALUES ('HiQS-Labs/xyz-forge', 'pull_request', 10, 'issue', 5, 'fixes')
        """
    )

    # Activity
    conn.execute(
        """
        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)
        VALUES ('noelsaw1', 'HiQS-Labs/xyz-forge', ?, 5, 2, 1, 1, 1, 3, 1, ?, ?)
        """,
        (now_date, now_iso, now_iso),
    )

    # Documents
    conn.execute(
        """
        INSERT INTO github_documents (repo_full_name, source_type, source_number, doc_type, source_key, title, body, content_hash, updated_at, fetched_at)
        VALUES ('HiQS-Labs/xyz-forge', 'pull_request', 10, 'pr', 'github:HiQS-Labs/xyz-forge:pull_request:10', 'feat: core engine', 'PR body description', 'hash1', ?, ?)
        """,
        (now_iso, now_iso),
    )


def _seed_mirror_rows(conn: sqlite3.Connection) -> None:
    now_iso = "2026-09-02T18:00:00Z"
    now_date = "2026-09-02"

    # Meta under old spelling
    conn.execute(
        """
        INSERT INTO github_repo_meta (repo_full_name, default_branch, pushed_at, updated_at, open_issues_count, has_issues, has_projects, fetched_at)
        VALUES ('HiQS-Suite/xyz-forge', 'main', ?, ?, 2, 1, 1, ?)
        """,
        (now_iso, now_iso, now_iso),
    )

    # Milestone under old spelling
    conn.execute(
        """
        INSERT INTO github_milestones (repo_full_name, number, title, description, state, open_issues, closed_issues, due_on, created_at, updated_at, closed_at, html_url)
        VALUES ('HiQS-Suite/xyz-forge', 1, 'v1.0', 'Release 1.0', 'open', 1, 1, '2026-09-30', ?, ?, NULL, 'https://github.com/HiQS-Suite/xyz-forge/milestone/1')
        """,
        (now_iso, now_iso),
    )

    # Same PR under old spelling
    conn.execute(
        """
        INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, author_login, head_ref, base_ref, created_at, updated_at, fetched_at, html_url)
        VALUES ('HiQS-Suite/xyz-forge', 'pull_request', 10, 'feat: core engine', 'open', 0, 'noelsaw1', 'feature/core', 'main', ?, ?, ?, 'https://github.com/HiQS-Suite/xyz-forge/pull/10')
        """,
        (now_iso, now_iso, now_iso),
    )
    # Same Issue under old spelling
    conn.execute(
        """
        INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, author_login, milestone_title, created_at, updated_at, fetched_at, html_url)
        VALUES ('HiQS-Suite/xyz-forge', 'issue', 5, 'bug: fix parsing', 'open', 0, 'noelsaw1', 'v1.0', ?, ?, ?, 'https://github.com/HiQS-Suite/xyz-forge/issues/5')
        """,
        (now_iso, now_iso, now_iso),
    )

    # Same PR commit under old spelling
    conn.execute(
        """
        INSERT INTO github_commits (repo_full_name, item_type, item_number, sha, author_login, message, committed_at, html_url, fetched_at)
        VALUES ('HiQS-Suite/xyz-forge', 'pull_request', 10, 'abc1234567890', 'noelsaw1', 'feat(core): initial commit', ?, 'https://github.com/HiQS-Suite/xyz-forge/commit/abc1234', ?)
        """,
        (now_iso, now_iso),
    )

    # Same Direct commit under old spelling
    conn.execute(
        """
        INSERT INTO github_direct_commits (event_id, repo_full_name, sha, ref, author_login, author_name, message, committed_at, html_url, path_coverage, discovered_at, fetched_at, source)
        VALUES ('evt_1', 'HiQS-Suite/xyz-forge', 'def9876543210', 'refs/heads/main', 'noelsaw1', 'Noel Saw', 'fix(direct): urgent patch', ?, 'https://github.com/HiQS-Suite/xyz-forge/commit/def9876', 'complete', ?, ?, 'events')
        """,
        (now_iso, now_iso, now_iso),
    )

    # Same comment under old spelling
    conn.execute(
        """
        INSERT INTO github_comments (repo_full_name, item_type, item_number, comment_type, github_comment_id, author_login, body, created_at, updated_at, fetched_at)
        VALUES ('HiQS-Suite/xyz-forge', 'pull_request', 10, 'issue_comment', 101, 'noelsaw1', 'LGTM ready to merge', ?, ?, ?)
        """,
        (now_iso, now_iso, now_iso),
    )

    # Same link under old spelling
    conn.execute(
        """
        INSERT INTO github_links (repo_full_name, source_type, source_number, target_type, target_number, link_kind)
        VALUES ('HiQS-Suite/xyz-forge', 'pull_request', 10, 'issue', 5, 'fixes')
        """
    )

    # Superseded stale snapshot under the old spelling: an earlier scan of the
    # SAME day with smaller totals (the rename happened mid-day; the canonical
    # spelling was scanned later and more completely). Values are deliberately
    # non-zero and deliberately different — a zero-filled duplicate can never
    # witness double-counting, and identical values can never witness the wrong
    # row being picked (SOP §6, clause 5).
    conn.execute(
        """
        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)
        VALUES ('noelsaw1', 'HiQS-Suite/xyz-forge', ?, 3, 1, 1, 0, 1, 1, 0, ?, ?)
        """,
        (now_date, "2026-09-02T16:30:00Z", "2026-09-02T17:00:00Z"),
    )

    # Document under old spelling
    conn.execute(
        """
        INSERT INTO github_documents (repo_full_name, source_type, source_number, doc_type, source_key, title, body, content_hash, updated_at, fetched_at)
        VALUES ('HiQS-Suite/xyz-forge', 'pull_request', 10, 'pr', 'github:HiQS-Suite/xyz-forge:pull_request:10', 'feat: core engine', 'PR body description', 'hash1', ?, ?)
        """,
        (now_iso, now_iso),
    )


@pytest.fixture()
def db_pair(tmp_path: Path):
    db_clean = tmp_path / "clean.db"
    db_mirror = tmp_path / "mirror.db"

    with sqlite3.connect(db_clean) as conn:
        conn.row_factory = sqlite3.Row
        ensure_schema(conn)
        ensure_github_schema(conn)
        _seed_canonical_data(conn)

    with sqlite3.connect(db_mirror) as conn:
        conn.row_factory = sqlite3.Row
        ensure_schema(conn)
        ensure_github_schema(conn)
        _seed_canonical_data(conn)
        _seed_mirror_rows(conn)

    return db_clean, db_mirror


PUBLIC_QUERY_FUNCTIONS = [
    name
    for name in queries_mod.__all__
    if callable(getattr(queries_mod, name))
]


@pytest.mark.parametrize("fn_name", PUBLIC_QUERY_FUNCTIONS)
def test_query_function_mirror_invariance(db_pair, org_alias, fn_name):
    """Every public query function in db/queries.py must return byte-identical results

    with and without mirror org rows in the database.
    """
    db_clean, db_mirror = db_pair
    fn = getattr(queries_mod, fn_name)

    start = datetime(2026, 9, 2, 0, 0, 0, tzinfo=PACIFIC)
    end = datetime(2026, 9, 3, 0, 0, 0, tzinfo=PACIFIC)

    # Build function-specific arguments
    kwargs_by_fn = {
        "fetch_github_balance": {
            "project_repos": {"XYZ Forge": ["HiQS-Labs/xyz-forge"]},
            "since_days": 14,
        },
        "fetch_org_activity": {
            "since_days": 14,
            "ignored_repos": [],
        },
        "fetch_day_commits": {
            "start": start,
            "end": end,
            "github_login": "noelsaw1",
        },
        "fetch_day_items": {
            "start": start,
            "end": end,
            "github_login": "noelsaw1",
        },
        "fetch_day_comments": {
            "start": start,
            "end": end,
            "github_login": "noelsaw1",
        },
        "fetch_watched_activity": {
            "external_repos": ["HiQS-Labs/xyz-forge"],
            "start": start,
            "end": end,
        },
        "fetch_open_items_for_projects": {
            "project_repos": {"XYZ Forge": ["HiQS-Labs/xyz-forge"]},
        },
        "fetch_repo_diagnostics": {
            "repo_name": "HiQS-Labs/xyz-forge",
            "sha": "abc1234",
            "pr": 10,
        },
        "fetch_release_readiness_data": {
            "repo_full_name": "HiQS-Labs/xyz-forge",
            "milestone_title": "v1.0",
        },
        "fetch_recent_github": {
            "limit": 10,
        },
        "fetch_repo_activity_counts": {
            "days": 14,
            "limit": 10,
        },
        "fetch_open_prs": {
            "limit": 10,
        },
    }

    kwargs = kwargs_by_fn[fn_name]

    with sqlite3.connect(db_clean) as conn_clean:
        conn_clean.row_factory = sqlite3.Row
        res_clean = fn(conn_clean, **kwargs)

    with sqlite3.connect(db_mirror) as conn_mirror:
        conn_mirror.row_factory = sqlite3.Row
        res_mirror = fn(conn_mirror, **kwargs)

    # Normalize JSON representation to compare structure & values
    dump_clean = json.dumps(res_clean, sort_keys=True, default=str)
    dump_mirror = json.dumps(res_mirror, sort_keys=True, default=str)

    assert dump_clean == dump_mirror, (
        f"{fn_name} is NOT mirror-invariant!\nClean:\n{dump_clean}\nMirrored:\n{dump_mirror}"
    )


def test_repo_scoped_queries_reach_alias_only_corpus(tmp_path):
    """Calling repo-scoped queries with canonical name must find rows stored under legacy alias."""
    db_path = tmp_path / "alias_only.db"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        # Seed under legacy alias only (HiQS-Suite/xyz-forge)
        _seed_mirror_rows(conn)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        # Query with canonical target (HiQS-Labs/xyz-forge)
        diag = queries_mod.fetch_repo_diagnostics(conn, "HiQS-Labs/xyz-forge", sha="abc1234", pr=10)
        assert diag["counts"]["commits"] == 1
        assert diag["counts"]["items"] == 2
        assert len(diag["commit_matches"]) == 1
        assert diag["pr_data"] is not None

        readiness = queries_mod.fetch_release_readiness_data(conn, "HiQS-Labs/xyz-forge", milestone_title="v1.0")
        assert readiness["milestone"] is not None
        assert len(readiness["issues"]) == 1
        assert len(readiness["prs"]) == 1


def test_naive_datetime_bounds_handling(db_pair):
    """Day-window query functions must accept naive datetimes without raising TypeError."""
    db_clean, _ = db_pair
    # Naive datetimes (no tzinfo)
    naive_start = datetime(2026, 9, 2, 0, 0, 0)
    naive_end = datetime(2026, 9, 3, 0, 0, 0)

    with sqlite3.connect(db_clean) as conn:
        conn.row_factory = sqlite3.Row
        commits = queries_mod.fetch_day_commits(conn, naive_start, naive_end, "noelsaw1")
        assert len(commits) == 2

        items = queries_mod.fetch_day_items(conn, naive_start, naive_end, "noelsaw1")
        assert len(items) == 2

        comments = queries_mod.fetch_day_comments(conn, naive_start, naive_end, "noelsaw1")
        assert len(comments) == 1

        watched = queries_mod.fetch_watched_activity(
            conn, ["HiQS-Labs/xyz-forge"], start=naive_start, end=naive_end
        )
        assert len(watched) == 1


def test_release_readiness_custom_default_branch(tmp_path):
    """Release readiness must detect promotion PR when repo default branch is non-main."""
    db_path = tmp_path / "custom_branch.db"
    now_iso = "2026-09-02T18:00:00Z"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        conn.execute(
            """
            INSERT INTO github_repo_meta (repo_full_name, default_branch, pushed_at, updated_at, open_issues_count, has_issues, has_projects, fetched_at)
            VALUES ('HiQS-Labs/xyz-forge', 'master', ?, ?, 1, 1, 1, ?)
            """,
            (now_iso, now_iso, now_iso),
        )
        conn.execute(
            """
            INSERT INTO github_milestones (repo_full_name, number, title, state, open_issues, closed_issues, due_on, created_at, updated_at, html_url)
            VALUES ('HiQS-Labs/xyz-forge', 1, 'v1.0', 'open', 0, 1, '2026-09-30', ?, ?, 'https://github.com/HiQS-Labs/xyz-forge/milestone/1')
            """,
            (now_iso, now_iso),
        )
        conn.execute(
            """
            INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, author_login, head_ref, base_ref, created_at, updated_at, fetched_at, html_url)
            VALUES ('HiQS-Labs/xyz-forge', 'pull_request', 20, 'feat: release v1.0', 'open', 0, 'noelsaw1', 'release/1.0', 'master', ?, ?, ?, 'https://github.com/HiQS-Labs/xyz-forge/pull/20')
            """,
            (now_iso, now_iso, now_iso),
        )
        conn.commit()

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        readiness = queries_mod.fetch_release_readiness_data(conn, "HiQS-Labs/xyz-forge", milestone_title="v1.0")
        assert readiness["promotion_pr"] is not None
        assert readiness["promotion_pr"]["number"] == 20


# ---------------------------------------------------------------------------
# Snapshot reconciliation: latest scanned_at wins per (login, canonical repo,
# scan_date); never sum across spellings (SOP §6).
# ---------------------------------------------------------------------------


def _insert_activity(
    conn: sqlite3.Connection,
    login: str,
    repo: str,
    scan_date: str,
    scanned_at: str,
    *,
    commits: int = 0,
    pushes: int = 0,
    prs_opened: int = 0,
    prs_merged: int = 0,
    issues_opened: int = 0,
    issue_comments: int = 0,
    reviews: int = 0,
    last_active_at: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,
                                     prs_opened, prs_merged, issues_opened, issue_comments,
                                     reviews, last_active_at, scanned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            login, repo, scan_date, commits, pushes, prs_opened, prs_merged,
            issues_opened, issue_comments, reviews, last_active_at, scanned_at,
        ),
    )


NEWER_TOTALS = dict(
    commits=48, pushes=11, prs_opened=13, prs_merged=4,
    issues_opened=21, issue_comments=5, reviews=6, last_active_at="2026-09-02T23:30:00Z",
)


@pytest.mark.parametrize("newer_spelling", ["canonical", "mirror"])
def test_duplicate_day_snapshot_latest_scan_wins(tmp_path, org_alias, newer_spelling):
    """One day recorded under two spellings must count exactly once.

    The snapshot with the latest scanned_at wins, regardless of which spelling
    carries it and regardless of insertion order (SOP §6).
    """
    canonical = "HiQS-Labs/xyz-forge"
    mirror = "HiQS-Suite/xyz-forge"
    newer_repo = canonical if newer_spelling == "canonical" else mirror
    older_repo = mirror if newer_spelling == "canonical" else canonical

    db_path = tmp_path / "dup_day.db"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        _insert_activity(
            conn, "noelsaw1", older_repo, "2026-09-02", "2026-09-02T17:00:00Z",
            commits=38, pushes=9, prs_opened=13, prs_merged=2,
            issues_opened=21, issue_comments=3, reviews=3,
            last_active_at="2026-09-02T16:45:00Z",
        )
        _insert_activity(
            conn, "noelsaw1", newer_repo, "2026-09-02", "2026-09-02T23:45:00Z",
            **NEWER_TOTALS,
        )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
        assert balance[0]["total_commits"] == 48
        assert balance[0]["prs_opened"] == 13
        assert balance[0]["prs_merged"] == 4
        assert balance[0]["issues_opened"] == 21
        assert balance[0]["last_active_at"] == "2026-09-02T23:30:00Z"

        counts = queries_mod.fetch_repo_activity_counts(conn, days=14, limit=10)
        assert len(counts) == 1
        assert counts[0]["commits"] == 48
        assert counts[0]["prs"] == 17
        assert counts[0]["issues"] == 21
        assert counts[0]["score"] == 48 + 13 + 4 + 21 + 5 + 6

        org = queries_mod.fetch_org_activity(conn, since_days=14)
        assert len(org["HiQS-Labs"]) == 1
        assert org["HiQS-Labs"][0]["commits"] == 48
        assert org["HiQS-Labs"][0]["prs_opened"] == 13


def test_activity_distinct_days_and_logins_still_sum(tmp_path, org_alias):
    """Latest-scan-wins applies within one (login, repo, day); distinct days and
    distinct logins must still add together."""
    db_path = tmp_path / "distinct_days.db"
    canonical = "HiQS-Labs/xyz-forge"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        _insert_activity(conn, "noelsaw1", canonical, "2026-09-01", "2026-09-01T20:00:00Z", commits=5)
        _insert_activity(conn, "noelsaw1", canonical, "2026-09-02", "2026-09-02T20:00:00Z", commits=7)
        _insert_activity(conn, "teammate1", canonical, "2026-09-02", "2026-09-02T21:00:00Z", commits=4)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
        assert balance[0]["total_commits"] == 16

        counts = queries_mod.fetch_repo_activity_counts(conn, days=14, limit=10)
        assert counts[0]["commits"] == 16

        org = queries_mod.fetch_org_activity(conn, since_days=14)
        assert org["HiQS-Labs"][0]["commits"] == 16


# ---------------------------------------------------------------------------
# Comment identity: native GitHub comment id, not (author, timestamp).
# ---------------------------------------------------------------------------


def _insert_comment(
    conn: sqlite3.Connection,
    repo: str,
    github_comment_id: int,
    created_at: str,
    *,
    item_type: str = "pull_request",
    item_number: int = 10,
    comment_type: str = "issue_comment",
    author: str = "noelsaw1",
) -> None:
    conn.execute(
        """
        INSERT INTO github_comments (repo_full_name, item_type, item_number, comment_type,
                                     github_comment_id, author_login, body, created_at,
                                     updated_at, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (repo, item_type, item_number, comment_type, github_comment_id, author,
         "A review remark", created_at, created_at, created_at),
    )


def test_comments_same_timestamp_distinct_ids_both_survive(tmp_path, org_alias):
    """Two distinct comments by one author sharing a timestamp must both count;
    a mirror-spelling copy of one of them must not add a third."""
    db_path = tmp_path / "comment_ids.db"
    canonical = "HiQS-Labs/xyz-forge"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        _insert_comment(conn, canonical, 201, "2026-09-02T18:00:00Z")
        _insert_comment(conn, canonical, 202, "2026-09-02T18:00:00Z")
        _insert_comment(conn, "HiQS-Suite/xyz-forge", 201, "2026-09-02T18:00:00Z")

    start = datetime(2026, 9, 2, 0, 0, 0, tzinfo=PACIFIC)
    end = datetime(2026, 9, 3, 0, 0, 0, tzinfo=PACIFIC)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        comments = queries_mod.fetch_day_comments(conn, start, end, "noelsaw1")
        assert len(comments) == 2

        watched = queries_mod.fetch_watched_activity(conn, [canonical], start=start, end=end)
        assert watched[0]["comments"] == 2


# ---------------------------------------------------------------------------
# Item resolution: newest record per canonical item wins BEFORE any state or
# milestone filter (SOP §6).
# ---------------------------------------------------------------------------


def _insert_item(
    conn: sqlite3.Connection,
    repo: str,
    item_type: str,
    number: int,
    state: str,
    *,
    updated_at: str,
    fetched_at: str,
    head_ref: str | None = None,
    base_ref: str | None = None,
    milestone_title: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO github_items (repo_full_name, item_type, number, title, state,
                                  author_login, head_ref, base_ref, milestone_title,
                                  created_at, updated_at, fetched_at, html_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repo, item_type, number, "item", state, "noelsaw1", head_ref, base_ref,
            milestone_title, "2026-08-01T00:00:00Z", updated_at, fetched_at,
            f"https://github.com/{repo}/{item_type}/{number}",
        ),
    )


def _seed_state_pair(
    conn: sqlite3.Connection,
    *,
    item_type: str,
    number: int,
    old_state: str,
    new_state: str,
    order: str,
    milestone_title: str | None = None,
    head_ref: str | None = None,
    base_ref: str | None = None,
) -> None:
    """Insert one canonical and one mirror copy of an item whose states disagree.

    The canonical copy is always the NEWER record (updated/fetched at 14:00), the
    mirror copy the stale one (12:00). ``order`` only flips insertion order, which
    must not influence which record wins.
    """
    canonical = "HiQS-Labs/xyz-forge"
    mirror = "HiQS-Suite/xyz-forge"
    copies = [
        (mirror, old_state, "2026-09-02T12:00:00Z"),
        (canonical, new_state, "2026-09-02T14:00:00Z"),
    ]
    if order == "new_first":
        copies.reverse()
    for repo, state, ts in copies:
        _insert_item(
            conn, repo, item_type, number, state,
            updated_at=ts, fetched_at=ts,
            head_ref=head_ref, base_ref=base_ref, milestone_title=milestone_title,
        )


@pytest.mark.parametrize("order", ["old_first", "new_first"])
@pytest.mark.parametrize("scenario", ["old_open_new_closed", "old_closed_new_reopened"])
def test_open_items_follow_newest_state(tmp_path, org_alias, order, scenario):
    """A stale open copy must not list a closed item, and a stale closed copy
    must not hide one that has since reopened — in either insertion order."""
    old_state = "open" if scenario == "old_open_new_closed" else "closed"
    new_state = "closed" if scenario == "old_open_new_closed" else "open"
    expect_open = new_state == "open"

    db_path = tmp_path / f"open_items_{scenario}_{order}.db"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        _seed_state_pair(
            conn, item_type="issue", number=5,
            old_state=old_state, new_state=new_state, order=order,
        )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        items = queries_mod.fetch_open_items_for_projects(
            conn, {"XYZ Forge": ["HiQS-Labs/xyz-forge"]}
        )
        assert (len(items["XYZ Forge"]) == 1) is expect_open


@pytest.mark.parametrize("order", ["old_first", "new_first"])
@pytest.mark.parametrize("scenario", ["old_open_new_closed", "old_closed_new_reopened"])
def test_open_prs_follow_newest_state(tmp_path, org_alias, order, scenario):
    """fetch_open_prs resolves mirrored copies to the newest record before
    checking state, in either insertion order."""
    old_state = "open" if scenario == "old_open_new_closed" else "closed"
    new_state = "closed" if scenario == "old_open_new_closed" else "open"
    expect_open = new_state == "open"

    db_path = tmp_path / f"open_prs_{scenario}_{order}.db"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        _seed_state_pair(
            conn, item_type="pull_request", number=10,
            old_state=old_state, new_state=new_state, order=order,
        )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        prs = queries_mod.fetch_open_prs(conn, limit=10)
        assert (len(prs) == 1) is expect_open


@pytest.mark.parametrize("order", ["old_first", "new_first"])
@pytest.mark.parametrize("scenario", ["old_open_new_closed", "old_closed_new_reopened"])
def test_release_readiness_uses_resolved_newest_records(tmp_path, org_alias, order, scenario):
    """Release readiness must read the same resolved set: a stale open mirror
    copy can neither revive a closed PR as the promotion PR, nor keep a closed
    milestone issue open; the reverse must not hide reopened work."""
    old_state = "open" if scenario == "old_open_new_closed" else "closed"
    new_state = "closed" if scenario == "old_open_new_closed" else "open"

    db_path = tmp_path / f"readiness_{scenario}_{order}.db"
    now_iso = "2026-09-02T18:00:00Z"
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        conn.execute(
            """
            INSERT INTO github_repo_meta (repo_full_name, default_branch, pushed_at, updated_at, open_issues_count, has_issues, has_projects, fetched_at)
            VALUES ('HiQS-Labs/xyz-forge', 'main', ?, ?, 1, 1, 1, ?)
            """,
            (now_iso, now_iso, now_iso),
        )
        conn.execute(
            """
            INSERT INTO github_milestones (repo_full_name, number, title, state, open_issues, closed_issues, due_on, created_at, updated_at, html_url)
            VALUES ('HiQS-Labs/xyz-forge', 1, 'v1.0', 'open', 1, 0, '2026-09-30', ?, ?, 'https://github.com/HiQS-Labs/xyz-forge/milestone/1')
            """,
            (now_iso, now_iso),
        )
        _seed_state_pair(
            conn, item_type="issue", number=5,
            old_state=old_state, new_state=new_state, order=order,
            milestone_title="v1.0",
        )
        _seed_state_pair(
            conn, item_type="pull_request", number=10,
            old_state=old_state, new_state=new_state, order=order,
            head_ref="release/1.0", base_ref="main",
        )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        data = queries_mod.fetch_release_readiness_data(
            conn, "HiQS-Labs/xyz-forge", milestone_title="v1.0"
        )
        assert len(data["issues"]) == 1
        assert data["issues"][0]["state"] == new_state
        assert len(data["prs"]) == 1
        assert data["prs"][0]["state"] == new_state
        if new_state == "open":
            assert data["promotion_pr"] is not None
            assert data["promotion_pr"]["number"] == 10
        else:
            assert data["promotion_pr"] is None

