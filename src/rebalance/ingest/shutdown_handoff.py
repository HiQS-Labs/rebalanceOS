"""Shutdown handoff generation, persistence, and optional read-only DB enrichment.

Provides atomic persistence of end-of-day triage handoffs and optional, bounded,
read-only context extraction from the local Rebalance SQLite database.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from datetime import datetime  # CANONICAL-PATH-OK: type annotation for UTC datetime boundaries
from pathlib import Path
from typing import Any

from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.ingest.db.queries import fetch_day_commits, fetch_day_items
from rebalance.ingest.registry import get_projects
from rebalance.lib.time_ops import now_utc, parse_iso

logger = logging.getLogger(__name__)


def enrich_shutdown_with_db(
    database_path: Path | str | None,
    start_utc: datetime,
    end_utc: datetime,
    github_login: str = "noelsaw1",
    max_records: int = 1000,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Extract author-scoped commits, items, and registered projects in read-only mode.

    Gracefully degrades if the database is absent, locked, stale, or malformed.
    Never mutates the database or triggers schema initialization.
    """
    if not database_path:
        return {
            "status": "degraded",
            "reason": "no database path configured",
            "commits": [],
            "items": [],
            "projects": [],
        }

    p = Path(database_path).expanduser().resolve()
    if not p.exists():
        return {
            "status": "degraded",
            "reason": f"database file {p} does not exist",
            "commits": [],
            "items": [],
            "projects": [],
        }

    try:
        with db_connection_readonly(p) as conn:
            # Set busy timeout on connection to prevent hanging
            conn.execute(f"PRAGMA busy_timeout = {int(timeout_seconds * 1000)}")

            start_monotonic = time.monotonic()

            def _progress_handler() -> int:
                if time.monotonic() - start_monotonic > timeout_seconds:
                    return 1  # Abort query execution
                return 0

            conn.set_progress_handler(_progress_handler, 1000)
            try:
                commits = fetch_day_commits(conn, start=start_utc, end=end_utc, github_login=github_login)
                items = fetch_day_items(conn, start=start_utc, end=end_utc, github_login=github_login)
                projects = get_projects(conn=conn, status="active", limit=max_records)
            finally:
                conn.set_progress_handler(None, 0)

            # Check freshness of newest commit or item
            latest_epoch: float = 0.0
            for c in commits:
                c_at = c.get("committed_at")
                if isinstance(c_at, str):
                    parsed_dt = parse_iso(c_at)
                    if parsed_dt:
                        latest_epoch = max(latest_epoch, parsed_dt.timestamp())

            now_epoch = now_utc().timestamp()
            is_stale = (now_epoch - latest_epoch > 86400) if latest_epoch > 0 else False

            is_truncated = len(commits) > max_records or len(items) > max_records or len(projects) >= max_records

            # Bounded output
            return {
                "status": "ok",
                "database_path": str(p),
                "is_stale": is_stale,
                "is_truncated": is_truncated,
                "commits": commits[:max_records],
                "items": items[:max_records],
                "projects": projects[:max_records],
            }
    except Exception as exc:
        logger.warning("Optional DB enrichment degraded: %s", exc)
        return {
            "status": "degraded",
            "reason": str(exc),
            "commits": [],
            "items": [],
            "projects": [],
        }


def write_shutdown_handoff(
    output_home: Path | str,
    run_id: str,
    markdown_content: str,
    json_evidence: dict[str, Any],
    date_str: str | None = None,
) -> tuple[Path, Path, Path]:
    """Atomically persist shutdown markdown brief, JSON sidecar, and latest pointer.

    Artifacts are written to:
      <output_home>/<date_str>/<run_id>.md
      <output_home>/<date_str>/<run_id>.json
    and a relative symlink is updated at:
      <output_home>/latest.md -> <date_str>/<run_id>.md
    """
    # 1. Serialize JSON first so any serialization errors abort before file creation
    json_str = json.dumps(json_evidence, indent=2)

    home_dir = Path(output_home).expanduser().resolve()
    if not date_str:
        date_str = now_utc().strftime("%Y-%m-%d")

    target_dir = home_dir / date_str
    target_dir.mkdir(parents=True, exist_ok=True)

    md_target = target_dir / f"{run_id}.md"
    json_target = target_dir / f"{run_id}.json"

    temp_md_path: Path | None = None
    temp_json_path: Path | None = None
    temp_link_path: Path | None = None

    try:
        # 2. Write markdown temp file
        with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, suffix=".mdtmp", encoding="utf-8") as tf_md:
            tf_md.write(markdown_content)
            tf_md.flush()
            os.fsync(tf_md.fileno())
            temp_md_path = Path(tf_md.name)

        # 3. Write JSON temp file
        with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, suffix=".jsontmp", encoding="utf-8") as tf_json:
            tf_json.write(json_str)
            tf_json.flush()
            os.fsync(tf_json.fileno())
            temp_json_path = Path(tf_json.name)

        # 4. Atomically move both files into place
        os.replace(temp_md_path, md_target)
        temp_md_path = None
        os.replace(temp_json_path, json_target)
        temp_json_path = None

        # 5. Atomically update latest.md symlink
        latest_link = home_dir / "latest.md"
        rel_target = Path(date_str) / f"{run_id}.md"

        with tempfile.NamedTemporaryFile("w", dir=home_dir, delete=False, suffix=".linktmp") as tf_link:
            temp_link_path = Path(tf_link.name)

        temp_link_path.unlink(missing_ok=True)
        os.symlink(rel_target, temp_link_path)
        os.replace(temp_link_path, latest_link)
        temp_link_path = None

        return md_target, json_target, latest_link
    finally:
        if temp_md_path and temp_md_path.exists():
            temp_md_path.unlink(missing_ok=True)
        if temp_json_path and temp_json_path.exists():
            temp_json_path.unlink(missing_ok=True)
        if temp_link_path and temp_link_path.exists():
            temp_link_path.unlink(missing_ok=True)


def format_shutdown_brief(
    scanner_data: dict[str, Any],
    db_enrichment: dict[str, Any] | None = None,
    deferrals: list[dict[str, str]] | None = None,
    run_timestamp: str | None = None,
) -> str:
    """Format the end-of-day shutdown brief according to the canonical template."""
    now_str = run_timestamp or now_utc().astimezone().strftime("%Y-%m-%d %H:%M %Z")  # READ-LAYER-OK: display timestamp

    lines = [
        f"# 🌙 End-of-Day Shutdown Brief — {now_str}",
        "",
        "## 🚀 What Advanced Today",
    ]

    projects = scanner_data.get("projects", [])
    advanced_found = False
    for proj in projects:
        recent_commits = proj.get("recent_commits", [])
        open_prs = proj.get("open_prs", [])
        if recent_commits or open_prs:
            advanced_found = True
            c_count = len(recent_commits)
            pr_count = len(open_prs)
            details = []
            if c_count > 0:
                details.append(f"{c_count} commit(s)")
            if pr_count > 0:
                details.append(f"{pr_count} open PR(s)")
            lines.append(f"- **`{proj['canonical_remote']}`**: {', '.join(details)} active in window.")

    if not advanced_found:
        lines.append("- _No commits or pull requests observed in the 3-day activity window._")

    lines.extend(
        [
            "",
            "## 🧭 Project Arcs & Remaining Phases",
        ]
    )

    registered_projects = (db_enrichment or {}).get("projects", [])
    if registered_projects:
        for rp in registered_projects:
            p_name = rp.get("name", "Unknown")
            p_summary = rp.get("summary", "No summary")
            p_tier = rp.get("priority_tier", "-")
            lines.append(f"- **{p_name}** (Tier {p_tier}): {p_summary}")
    else:
        for proj in projects:
            lines.append(f"- **`{proj['canonical_remote']}`**: Arc status tracked via GitHub branches & PRs.")

    lines.extend(
        [
            "",
            "## ⏳ Pending Pull Requests & Proposed Merge Order",
        ]
    )

    all_open_prs = []
    for proj in projects:
        # Exclude active projects from action candidate PRs
        if proj.get("is_active"):
            continue
        for pr in proj.get("open_prs", []):
            if pr.get("state", "OPEN").upper() == "OPEN":
                all_open_prs.append(pr)

    pr_query_errors = scanner_data.get("pr_query_errors", [])
    if all_open_prs:
        for idx, pr in enumerate(all_open_prs, 1):
            pr_repo = pr.get("repo", "")
            pr_num = pr.get("number", "")
            pr_title = pr.get("title", "")
            pr_url = pr.get("url", "")
            lines.append(f"{idx}. [{pr_repo}#{pr_num}]({pr_url}) — {pr_title} (Open)")
    elif pr_query_errors:
        lines.append("_Pull request status unknown for some repositories due to query errors._")
    else:
        lines.append("_No pending pull requests across scanned repositories._")

    lines.extend(
        [
            "",
            "## ⏸️ Deliberate Deferrals & Held PRs",
        ]
    )

    if deferrals:
        for d in deferrals:
            lines.append(f"- `{d.get('target', 'item')}`: {d.get('reason', 'Deferred by operator')}")
    else:
        lines.append("- _None recorded._")

    lines.extend(
        [
            "",
            "## 🛑 Ongoing Activity Exclusions (Excluded from actions)",
        ]
    )

    excluded_repos = scanner_data.get("excluded_repos", [])
    if excluded_repos:
        for ex in excluded_repos:
            r_name = ex.get("name", "unknown")
            reasons = ", ".join(ex.get("activity_reasons", ["ongoing activity detected"]))
            lines.append(f"- **`{r_name}`**: Excluded (`[Reason: {reasons}]`)")
    else:
        lines.append("- _No repositories excluded; all scanned repositories observed stable._")

    lines.extend(
        [
            "",
            "## 🌅 Tomorrow Morning Nudges (Top 1–3 Focus Items)",
        ]
    )

    nudges_emitted = 0
    # Top nudge 1: Un-PRed branches (only from stable, non-excluded projects)
    unpred_list = []
    for proj in projects:
        if proj.get("is_active"):
            continue
        for b in proj.get("branches", []):
            if b.get("pr_status") == "unpred":
                unpred_list.append((proj["canonical_remote"], b["branch"]))

    if unpred_list and nudges_emitted < 3:
        nudges_emitted += 1
        r_name, b_name = unpred_list[0]
        lines.append(
            f"{nudges_emitted}. **Review Un-PRed Branch**: Inspect `{r_name}:{b_name}` and cut PR or merge via `/merge-cleanup`."
        )

    # Top nudge 2: Open PRs (only from stable, non-excluded projects)
    if all_open_prs and nudges_emitted < 3:
        nudges_emitted += 1
        first_pr = all_open_prs[0]
        lines.append(
            f"{nudges_emitted}. **Review Top PR**: Verify checks and review [{first_pr.get('repo')}#{first_pr.get('number')}]({first_pr.get('url')})."
        )

    # Top nudge 3: In-flight project arc
    if nudges_emitted < 3 and registered_projects:
        nudges_emitted += 1
        lines.append(
            f"{nudges_emitted}. **Advance Active Arc**: Resume priority project `{registered_projects[0].get('name')}`."
        )

    if nudges_emitted == 0:
        lines.append("1. **Clean Slate**: All loops closed. Run `/daily` tomorrow to plan new work.")

    lines.append("")
    return "\n".join(lines)
