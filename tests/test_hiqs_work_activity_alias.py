"""GH-316: `hiqs_work_activity` is canonical; `github_balance` stays as a deprecated alias.

Both MCP tool names must resolve through the real FastMCP server and return
identical, fully-populated rows — and the frozen output contract (all nine
keys) must not drift while the naming changes.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from rebalance.ingest.db import (
    db_connection,
    ensure_github_schema,
    ensure_project_schema,
    ensure_schema,
)
from rebalance.ingest.github_scan import get_github_balance, get_hiqs_work_activity
from rebalance.mcp.server import create_server

FROZEN_OUTPUT_KEYS = {
    "project_name",
    "repos_linked",
    "repos_touched",
    "total_commits",
    "prs_opened",
    "prs_merged",
    "issues_opened",
    "last_active_at",
    "is_idle",
}


def _call(server, name: str, args: dict):
    """Invoke an MCP tool; FastMCP emits one JSON text block per list item."""
    content, _ = asyncio.run(server.call_tool(name, args))
    return [json.loads(block.text) for block in content]


class HiqsWorkActivityAliasTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "rebalance.db"
        with db_connection(self.db, ensure_schema) as conn:
            ensure_project_schema(conn)
            ensure_github_schema(conn)
            conn.execute(
                "INSERT INTO project_registry (name, status, repos_json, tags_json, custom_fields_json)"
                " VALUES ('Alpha', 'active', '[\"a/one\"]', '[]', '{}')"
            )
            conn.execute(
                "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,"
                " prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)"
                " VALUES ('me', 'a/one', '2026-10-01', 7, 2, 3, 1, 0, 0, 0,"
                " '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z')"
            )
            conn.commit()

    def test_python_alias_is_the_canonical_function(self) -> None:
        self.assertIs(get_github_balance, get_hiqs_work_activity)

    def test_both_mcp_tool_names_return_identical_populated_rows(self) -> None:
        server = create_server(self.db)
        canonical = _call(server, "hiqs_work_activity", {"since_days": 30})
        alias = _call(server, "github_balance", {"since_days": 30})
        self.assertEqual(canonical, alias)
        self.assertEqual(len(canonical), 1)
        row = canonical[0]
        self.assertEqual(set(row), FROZEN_OUTPUT_KEYS)
        self.assertEqual(row["project_name"], "Alpha")
        self.assertEqual(row["total_commits"], 7)
        self.assertEqual(row["prs_merged"], 1)
        self.assertFalse(row["is_idle"])
        self.assertEqual(row["repos_touched"], ["a/one"])


if __name__ == "__main__":
    unittest.main()
