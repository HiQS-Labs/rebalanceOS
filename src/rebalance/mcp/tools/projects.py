from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from rebalance.ingest.github_scan import get_hiqs_work_activity
from rebalance.ingest.registry import get_projects


def _project_repos_map(database_path: Path) -> dict[str, list[str]]:
    """Return {project_name: [repo, ...]} for all active projects."""
    projects = get_projects(database_path, status="active")
    return {p["name"]: p.get("repos") or [] for p in projects}


def register(mcp: FastMCP, database_path: Path) -> None:
    @mcp.tool()
    def list_projects(status: str = "active") -> list[dict[str, Any]]:
        """List projects from the local project_registry table."""
        normalized = status.strip().lower() if status else ""
        return get_projects(database_path, status=normalized or None)

    @mcp.tool()
    def hiqs_work_activity(since_days: int = 30) -> list[dict[str, Any]]:
        """
        Show HiQS work activity balance across active projects (canonical name).

        HiQS = High Quality Signals. Returns one row per project with
        commit/PR/issue counts over the last `since_days` days.  Projects with
        no HiQS work activity are flagged as idle (is_idle=true).  Requires a
        prior `rebalance github-scan` run.
        """
        project_repos = _project_repos_map(database_path)
        return get_hiqs_work_activity(
            database_path=database_path,
            project_repos=project_repos,
            since_days=since_days,
        )

    @mcp.tool()
    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
        """
        Deprecated alias of `hiqs_work_activity` (GH-316).

        Same implementation and identical response shape; use the canonical
        `hiqs_work_activity` tool going forward.
        """
        return hiqs_work_activity(since_days=since_days)
