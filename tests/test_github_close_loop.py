"""Tests for GH-307 deterministic close-the-loop flags."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

from rebalance.cli import app
from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_release_readiness_data
from rebalance.ingest.github_readiness import infer_close_loop_flags

REPO = "AcmeOrg/widget"
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
OLD = "2026-09-10T00:00:00Z"  # 22 days before NOW
FRESH = "2026-10-01T00:00:00Z"  # 1.5 days before NOW


def _item(conn, item_type, number, *, state="open", state_reason=None, is_draft=0, is_merged=0,
          review_decision="", check_status="", head_ref="", milestone=None,
          created=OLD, updated=OLD, closed=None):
    conn.execute(
        """
        INSERT INTO github_items
            (repo_full_name, item_type, number, title, state, state_reason, milestone_title,
             is_draft, is_merged, head_ref, review_decision, check_status, html_url,
             created_at, updated_at, closed_at, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (REPO, item_type, number, f"{item_type} {number}", state, state_reason, milestone,
         is_draft, is_merged, head_ref, review_decision, check_status,
         f"https://github.com/{REPO}/{number}", created, updated, closed, FRESH),
    )


def _link(conn, pr, issue, kind="closes"):
    conn.execute(
        "INSERT INTO github_links (repo_full_name, source_type, source_number, target_type, target_number, link_kind)"
        " VALUES (?, 'pull_request', ?, 'issue', ?, ?)",
        (REPO, pr, issue, kind),
    )


def _branch(conn, name):
    conn.execute(
        "INSERT INTO github_branches (repo_full_name, name, head_sha, is_protected, is_default, fetched_at)"
        " VALUES (?, ?, ?, 0, 0, ?)",
        (REPO, name, f"sha-{name}", FRESH),
    )


def _commit(conn, sha, message, *, ref="refs/heads/development", committed=FRESH):
    conn.execute(
        "INSERT INTO github_direct_commits (repo_full_name, sha, event_id, ref, message, committed_at,"
        " discovered_at, fetched_at) VALUES (?, ?, 'e', ?, ?, ?, ?, ?)",
        (REPO, sha, ref, message, committed, FRESH, FRESH),
    )


def _seed(db_path: Path) -> None:
    with db_connection(db_path, ensure_github_schema) as conn:
        conn.execute(
            "INSERT INTO github_repo_meta (repo_full_name, default_branch, fetched_at) VALUES (?, 'development', ?)",
            (REPO, FRESH),
        )
        conn.execute(
            "INSERT INTO github_milestones (repo_full_name, number, title, state, open_issues, closed_issues)"
            " VALUES (?, 1, 'M1', 'open', 1, 0)",
            (REPO,),
        )
        # PRs: stale vs fresh, forgotten draft vs fresh draft, refinement vs clean.
        _item(conn, "pull_request", 101)                                   # stale_pr
        _item(conn, "pull_request", 102, updated=FRESH)                    # fresh -> none
        _item(conn, "pull_request", 103, is_draft=1)                       # forgotten_draft
        _item(conn, "pull_request", 104, is_draft=1, updated=FRESH)        # fresh draft -> none
        _item(conn, "pull_request", 105, updated=FRESH, review_decision="CHANGES_REQUESTED")
        _item(conn, "pull_request", 106, updated=FRESH, check_status="failing")
        _item(conn, "pull_request", 107, updated=FRESH, review_decision="APPROVED", check_status="success")
        _item(conn, "pull_request", 108, state="closed", is_merged=1, closed=FRESH, updated=FRESH)
        _item(conn, "pull_request", 109, state="closed", is_merged=0, closed=FRESH, updated=FRESH)
        _item(conn, "pull_request", 110, updated=FRESH, head_ref="feat/gh214-tidy")
        # closed_without_delivery: positive and negative twins.
        _item(conn, "issue", 201, state="closed", state_reason="completed", closed=FRESH)   # flag
        _item(conn, "issue", 202, state="closed", state_reason="completed", closed=FRESH)   # merged PR link
        _link(conn, 108, 202, "mentions")
        _item(conn, "issue", 203, state="closed", state_reason="not_planned", closed=FRESH)  # excluded
        _item(conn, "issue", 204, state="closed", state_reason="completed", closed=FRESH)    # direct commit
        _commit(conn, "c1", "fix(GH-204): ship it")
        _item(conn, "issue", 205, state="closed", state_reason="completed", closed=FRESH)    # only unmerged PR -> flag
        _link(conn, 109, 205)
        _item(conn, "issue", 206, state="closed", state_reason="completed", closed=OLD)      # outside 15-day window
        _item(conn, "issue", 207, state="closed", state_reason="completed", closed=FRESH)    # commit on other ref -> flag
        _commit(conn, "c2", "wip #207", ref="refs/heads/feat/x")
        _item(conn, "issue", 208, state="closed", state_reason=None, closed=FRESH)           # #2080 is not #208 -> flag
        _commit(conn, "c3", "closes #2080")
        # started_not_shipped
        _item(conn, "issue", 211, milestone="M1")   # branch, no PR, stale -> flag
        _branch(conn, "feat/gh211-thing")
        _item(conn, "issue", 212)                   # branch but linked PR
        _branch(conn, "fix/GH-212")
        _link(conn, 102, 212)
        _item(conn, "issue", 213, updated=FRESH)    # branch but fresh
        _branch(conn, "feat/gh213-new")
        _item(conn, "issue", 214)                   # branch used by an unlinked PR head
        _branch(conn, "feat/gh214-tidy")
        _item(conn, "issue", 215)                   # gh2150 / gh215suffix must not match
        _branch(conn, "feat/gh2150-other")
        _branch(conn, "gh215suffix")
        conn.commit()


class CloseLoopFlagTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "rebalance.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _flagged(self, report, flag):
        return sorted(item["number"] for item in report["flags"] if item["flag"] == flag)

    def test_no_local_data(self) -> None:
        report = infer_close_loop_flags(self.db_path, REPO, now=NOW)
        self.assertEqual(report["status"], "no_local_data")
        self.assertEqual(report["flags"], [])

    def test_flags_positive_and_negative_twins(self) -> None:
        _seed(self.db_path)
        report = infer_close_loop_flags(self.db_path, REPO, stale_days=7, since_days=15, now=NOW)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(self._flagged(report, "stale_pr"), [101])
        self.assertEqual(self._flagged(report, "forgotten_draft"), [103])
        self.assertEqual(self._flagged(report, "pr_needs_refinement"), [105, 106])
        self.assertEqual(self._flagged(report, "closed_without_delivery"), [201, 205, 207, 208])
        self.assertEqual(self._flagged(report, "started_not_shipped"), [211])
        self.assertEqual(report["counts"]["closed_without_delivery"], 4)
        self.assertTrue(all(item["evidence"] for item in report["flags"]))
        json.dumps(report)  # JSON-safe

    def test_commit_before_issue_creation_is_not_delivery(self) -> None:
        _seed(self.db_path)
        with db_connection(self.db_path, ensure_github_schema) as conn:
            _item(conn, "issue", 220, state="closed", state_reason="completed", created=FRESH, closed=FRESH)
            _commit(conn, "c4", "GH-220 early", committed="2026-09-30T00:00:00Z")
            conn.commit()
        report = infer_close_loop_flags(self.db_path, REPO, since_days=15, now=NOW)
        self.assertIn(220, self._flagged(report, "closed_without_delivery"))

    def test_readiness_reader_default_still_filters_to_milestone(self) -> None:
        _seed(self.db_path)
        with db_connection(self.db_path, ensure_github_schema) as conn:
            default = fetch_release_readiness_data(conn, REPO)
            everything = fetch_release_readiness_data(conn, REPO, all_issues=True)
        self.assertEqual([int(i["number"]) for i in default["issues"]], [211])
        self.assertGreater(len(everything["issues"]), 1)

    def test_cli_json(self) -> None:
        _seed(self.db_path)
        result = CliRunner().invoke(
            app, ["github-close-loop", "--repo", REPO, "--database", str(self.db_path), "--output", "json"]
        )
        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(set(payload["counts"]), {
            "stale_pr", "forgotten_draft", "pr_needs_refinement", "closed_without_delivery", "started_not_shipped",
        })


if __name__ == "__main__":
    unittest.main()
