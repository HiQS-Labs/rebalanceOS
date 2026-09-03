"""GH-150 / 0.75.0 fe1: Mirror-invariance test for the shared SQL read layer.

Generalizes tests/test_hiqs_digest.py::test_org_mirror_rows_collapse_into_one_repo
across all query families in src/rebalance/ingest/db/queries.py.

Given a database with clean canonical data vs a database seeded with both canonical
and mirror org rows (sharing commit SHAs, PR numbers, activity rows, etc.), every
public function in db/queries.py MUST return identical, deduplicated results.
"""

from __future__ import annotations

import inspect
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

import rebalance.ingest.db.queries as queries_mod
from rebalance.ingest import config as config_module
from rebalance.ingest.db.schema import ensure_github_schema, ensure_schema

PACIFIC = ZoneInfo("America/Los_Angeles")


@pytest.fixture()
def org_alias(monkeypatch):
    aliases = {"hiqs-suite": "HiQS-Labs"}
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

    # Duplicate activity under old spelling
    conn.execute(
        """
        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)
        VALUES ('noelsaw1', 'HiQS-Suite/xyz-forge', ?, 0, 0, 0, 0, 0, 0, 0, ?, ?)
        """,
        (now_date, now_iso, now_iso),
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
