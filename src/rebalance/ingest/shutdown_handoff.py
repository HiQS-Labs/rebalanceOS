"""Shutdown handoff generation, persistence, and optional read-only DB enrichment.

Provides atomic persistence of end-of-day triage handoffs and optional, bounded,
read-only context extraction from the local Rebalance SQLite database.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone  # CANONICAL-PATH-OK: type hints and timezone handling
from pathlib import Path
from typing import Any

from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.ingest.db.queries import fetch_day_commits, fetch_day_items
from rebalance.ingest.registry import get_projects
from rebalance.lib.time_ops import format_local, now_utc, parse_iso

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

            commits = fetch_day_commits(conn, start=start_utc, end=end_utc, github_login=github_login)
            items = fetch_day_items(conn, start=start_utc, end=end_utc, github_login=github_login)
            projects = get_projects(conn=conn, status="active")

            # Check freshness of newest commit or item
            latest_epoch: float = 0.0
            for c in commits:
                c_at = c.get("committed_at")
                if isinstance(c_at, str):
                    try:
                        latest_epoch = max(latest_epoch, datetime.fromisoformat(c_at.replace("Z", "+00:00")).timestamp())
                    except Exception:
                        pass

            now_epoch = datetime.now(timezone.utc).timestamp()
            is_stale = (now_epoch - latest_epoch > 86400) if latest_epoch > 0 else False

            # Bounded output
            return {
                "status": "ok",
                "database_path": str(p),
                "is_stale": is_stale,
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
    home_dir = Path(output_home).expanduser().resolve()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    target_dir = home_dir / date_str
    target_dir.mkdir(parents=True, exist_ok=True)

    md_target = target_dir / f"{run_id}.md"
    json_target = target_dir / f"{run_id}.json"

    # Atomic write for markdown file
    with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, suffix=".tmp") as tf_md:
        tf_md.write(markdown_content)
        tf_md.flush()
        os.fsync(tf_md.fileno())
        temp_md_path = Path(tf_md.name)

    os.replace(temp_md_path, md_target)

    # Atomic write for JSON sidecar
    with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, suffix=".tmp") as tf_json:
        tf_json.write(json.dumps(json_evidence, indent=2))
        tf_json.flush()
        os.fsync(tf_json.fileno())
        temp_json_path = Path(tf_json.name)

    os.replace(temp_json_path, json_target)

    # Atomic symlink update for latest.md
    latest_link = home_dir / "latest.md"
    rel_target = Path(date_str) / f"{run_id}.md"

    with tempfile.NamedTemporaryFile("w", dir=home_dir, delete=False, suffix=".linktmp") as tf_link:
        temp_link_path = Path(tf_link.name)

    temp_link_path.unlink(missing_ok=True)
    os.symlink(rel_target, temp_link_path)
    os.replace(temp_link_path, latest_link)

    return md_target, json_target, latest_link


def format_shutdown_brief(
    scanner_data: dict[str, Any],
    db_enrichment: dict[str, Any] | None = None,
    deferrals: list[dict[str, str]] | None = None,
    run_timestamp: str | None = None,
) -> str:
    """Format the end-of-day shutdown brief according to the canonical template."""
    now_str = run_timestamp or datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

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
        for pr in proj.get("open_prs", []):
            all_open_prs.append(pr)

    if all_open_prs:
        for idx, pr in enumerate(all_open_prs, 1):
            pr_repo = pr.get("repo", "")
            pr_num = pr.get("number", "")
            pr_title = pr.get("title", "")
            pr_url = pr.get("url", "")
            lines.append(f"{idx}. [{pr_repo}#{pr_num}]({pr_url}) — {pr_title} (Open)")
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
    # Top nudge 1: Un-PRed branches
    unpred_list = []
    for proj in projects:
        for b in proj.get("branches", []):
            if b.get("pr_status") == "unpred":
                unpred_list.append((proj["canonical_remote"], b["branch"]))

    if unpred_list and nudges_emitted < 3:
        nudges_emitted += 1
        r_name, b_name = unpred_list[0]
        lines.append(
            f"{nudges_emitted}. **Review Un-PRed Branch**: Inspect `{r_name}:{b_name}` and cut PR or merge via `/merge-cleanup`."
        )

    # Top nudge 2: Open PRs
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
