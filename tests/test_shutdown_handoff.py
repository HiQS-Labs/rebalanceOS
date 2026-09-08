"""Unit and integration tests for shutdown handoff, persistence, and DB enrichment (A7-A12)."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from rebalance.ingest.shutdown_handoff import (
    enrich_shutdown_with_db,
    format_shutdown_brief,
    write_shutdown_handoff,
)


def create_fixture_db(db_path: Path) -> Path:
    """Create a fixture SQLite database mimicking Rebalance DB schema."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE project_registry (
            name TEXT PRIMARY KEY,
            status TEXT,
            summary TEXT,
            value_level TEXT,
            priority_tier INTEGER,
            risk_level TEXT,
            repos_json TEXT,
            tags_json TEXT,
            custom_fields_json TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE github_commits (
            repo_full_name TEXT,
            sha TEXT,
            message TEXT,
            committed_at TEXT,
            html_url TEXT,
            author_login TEXT,
            item_type TEXT,
            item_number INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE github_items (
            repo_full_name TEXT,
            item_type TEXT,
            number INTEGER,
            title TEXT,
            state TEXT,
            html_url TEXT,
            created_at TEXT,
            updated_at TEXT,
            author_login TEXT,
            head_ref TEXT,
            body TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE github_direct_commits (
            repo_full_name TEXT,
            sha TEXT,
            message TEXT,
            committed_at TEXT,
            html_url TEXT,
            author_login TEXT,
            ref TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE github_direct_commit_files (
            repo_full_name TEXT,
            sha TEXT,
            path TEXT
        )
        """
    )

    # Insert sample project
    conn.execute(
        """
        INSERT INTO project_registry VALUES (
            'Rebalance OS',
            'active',
            'Workday operating system',
            'strategic',
            1,
            'medium',
            '["HiQS-Labs/rebalanceOS"]',
            '["core"]',
            '{"provenance": "curated"}'
        )
        """
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO github_commits VALUES (
            'HiQS-Labs/rebalanceOS',
            'abc1234',
            'feat: shutdown handoff',
            ?,
            'https://github.com/HiQS-Labs/rebalanceOS/commit/abc1234',
            'noelsaw1',
            'pull_request',
            196
        )
        """,
        (now_iso,),
    )
    conn.commit()
    conn.close()
    return db_path


def test_a7_continuity_brief_formatting():
    """A7: Rendered handoff includes project phases, open PRs, unpred branches, deferrals, and next nudges."""
    scanner_data = {
        "projects": [
            {
                "canonical_remote": "HiQS-Labs/rebalanceOS",
                "recent_commits": [{"sha": "123", "message": "commit 1"}],
                "open_prs": [
                    {
                        "repo": "HiQS-Labs/rebalanceOS",
                        "number": 196,
                        "title": "Shutdown MVP",
                        "url": "https://github.com/HiQS-Labs/rebalanceOS/pull/196",
                    }
                ],
                "branches": [
                    {
                        "branch": "feat/shutdown-plan",
                        "pr_status": "open",
                        "pr_number": 196,
                        "pr_url": "https://github.com/HiQS-Labs/rebalanceOS/pull/196",
                    },
                    {
                        "branch": "fix/some-bug",
                        "pr_status": "unpred",
                    },
                ],
            }
        ],
        "excluded_repos": [
            {
                "name": "active-repo",
                "activity_reasons": ["Active edits detected in Snapshot B"],
            }
        ],
    }
    deferrals = [{"target": "HiQS-Labs/rebalanceOS#195", "reason": "Held for morning dogfood"}]

    brief = format_shutdown_brief(scanner_data=scanner_data, deferrals=deferrals)

    assert "🌙 End-of-Day Shutdown Brief" in brief
    assert "HiQS-Labs/rebalanceOS" in brief
    assert "Shutdown MVP" in brief
    assert "Deliberate Deferrals" in brief
    assert "Held for morning dogfood" in brief
    assert "Ongoing Activity Exclusions" in brief
    assert "active-repo" in brief
    assert "Tomorrow Morning Nudges" in brief
    assert "Review Un-PRed Branch" in brief


def test_a8_standalone_and_db_enrichment(tmp_path: Path):
    """A8: Works without runtime/DB; gracefully degrades on missing/locked DB; enriches when present."""
    start_utc = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end_utc = datetime(2026, 9, 10, tzinfo=timezone.utc)

    # Case 1: Missing DB -> gracefully degrades to "degraded"
    res_missing = enrich_shutdown_with_db(tmp_path / "nonexistent.db", start_utc, end_utc)
    assert res_missing["status"] == "degraded"
    assert res_missing["commits"] == []
    assert res_missing["projects"] == []

    # Case 2: Valid fixture DB -> extracts commits & projects
    fixture_db = create_fixture_db(tmp_path / "rebalance.db")
    res_ok = enrich_shutdown_with_db(fixture_db, start_utc, end_utc)
    assert res_ok["status"] == "ok"
    assert len(res_ok["commits"]) == 1
    assert len(res_ok["projects"]) == 1
    assert res_ok["projects"][0]["name"] == "Rebalance OS"


def test_a9_durable_atomic_handoff(tmp_path: Path):
    """A9: Two run IDs write atomically and do not overwrite each other; latest.md updates."""
    output_home = tmp_path / "shutdown_out"
    date_str = "2026-09-08"

    # Write run 1
    md1, json1, link1 = write_shutdown_handoff(
        output_home=output_home,
        run_id="run_01",
        markdown_content="# Run 1 Brief\n",
        json_evidence={"run": 1},
        date_str=date_str,
    )
    assert md1.exists()
    assert json1.exists()
    assert link1.is_symlink()
    assert link1.resolve() == md1.resolve()

    # Write run 2
    md2, json2, link2 = write_shutdown_handoff(
        output_home=output_home,
        run_id="run_02",
        markdown_content="# Run 2 Brief\n",
        json_evidence={"run": 2},
        date_str=date_str,
    )
    assert md2.exists()
    assert json2.exists()

    # Verify run 1 is preserved and not overwritten
    assert md1.read_text(encoding="utf-8") == "# Run 1 Brief\n"
    assert json.loads(json1.read_text(encoding="utf-8")) == {"run": 1}

    # Verify latest points to run 2
    assert link2.resolve() == md2.resolve()


def test_a10_exclusion_boundary():
    """A10: Active repositories are excluded from action candidates."""
    scanner_data = {
        "projects": [
            {
                "canonical_remote": "HiQS-Labs/active-repo",
                "is_active": True,
                "activity_reasons": ["concurrent commit"],
            }
        ],
        "excluded_repos": [{"name": "active-repo", "activity_reasons": ["concurrent commit"]}],
        "stable_repos": [],
    }
    brief = format_shutdown_brief(scanner_data=scanner_data)
    assert "Ongoing Activity Exclusions" in brief
    assert "active-repo" in brief


def test_a11_claude_forwarding_compatibility(tmp_path: Path):
    """A11: .claude forwarding shim delegates to canonical scanner and returns 0."""
    claude_script = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "daily" / "scripts" / "scan_unclosed_loops.py"
    assert claude_script.exists()

    res = subprocess.run([sys.executable, str(claude_script), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Scan and report unclosed loops across repositories" in res.stdout


def test_a12_useful_restart(tmp_path: Path):
    """A12: Operator / cold agent can identify next unfinished phase or PR review from first screen."""
    output_home = tmp_path / "shutdown_out"
    scanner_data = {
        "projects": [
            {
                "canonical_remote": "HiQS-Labs/rebalanceOS",
                "open_prs": [
                    {
                        "repo": "HiQS-Labs/rebalanceOS",
                        "number": 196,
                        "title": "shutdown MVP",
                        "url": "https://github.com/HiQS-Labs/rebalanceOS/pull/196",
                    }
                ],
                "branches": [
                    {
                        "branch": "feat/shutdown-plan",
                        "pr_status": "open",
                        "pr_number": 196,
                        "pr_url": "https://github.com/HiQS-Labs/rebalanceOS/pull/196",
                    }
                ],
                "recent_commits": [],
            }
        ],
        "excluded_repos": [],
    }
    brief = format_shutdown_brief(scanner_data)
    md_path, json_path, latest_link = write_shutdown_handoff(
        output_home=output_home,
        run_id="run_12",
        markdown_content=brief,
        json_evidence=scanner_data,
        date_str="2026-09-08",
    )

    # Cold agent reads only latest.md
    restart_content = latest_link.read_text(encoding="utf-8")
    assert "🌙 End-of-Day Shutdown Brief" in restart_content
    assert "Tomorrow Morning Nudges" in restart_content
    assert "HiQS-Labs/rebalanceOS#196" in restart_content

