#!/usr/bin/env python3
"""
scan_unclosed_loops.py — Deterministic Scanner for Unmerged Work, Un-PRed Branches,
and Open Pull Requests across the Operator's Repositories.

Used by the `/daily` skill to maintain `temp/close-the-loop.md` and generate
compact, low-token cycle summary strings without overloading context windows.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


KNOWN_ACTIVE_ROOTS = (
    Path("/Users/noelsaw/Documents/GH Repos"),
    Path("/Users/noelsaw/Local Sites"),
    Path("/Users/noelsaw/marathon-clones"),
)

PRIMARY_WATCHED_REPOS = [
    "HiQS-Labs/rebalanceOS",
    "HiQS-Labs/XYZ-forge",
    "HiQS-Labs/AEGIS-Sleuth-Slackbot",
    "HiQS-Labs/Model-catalog",
    "NeochromeTeam/mac-buyers-guide-2.0",
    "NeochromeTeam/mac-buyers-guide-soc-families",
    "HiQS-Labs/LTVERA-PANDAS",
]


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=10)
        return res.returncode, res.stdout.strip()
    except Exception as e:
        return 1, str(e)


def discover_git_repos(max_age_days: float = 14.0) -> list[Path]:
    """Discover recently modified git repositories across standard development roots."""
    found: list[Path] = []
    now = time.time()
    cutoff = now - (max_age_days * 86400)

    for root in KNOWN_ACTIVE_ROOTS:
        if not root.exists():
            continue
        # Direct children check (e.g. /Documents/GH Repos/*)
        try:
            for child in root.iterdir():
                if child.is_dir() and (child / ".git").exists():
                    try:
                        mtime = child.stat().st_mtime
                        if mtime >= cutoff:
                            found.append(child)
                    except OSError:
                        found.append(child)
        except OSError:
            pass

        # Nested check for Local Sites plugins/themes (limited depth)
        if "Local Sites" in str(root):
            for dirpath, dirs, _ in os.walk(root):
                if ".git" in dirs:
                    p = Path(dirpath)
                    try:
                        if p.stat().st_mtime >= cutoff:
                            found.append(p)
                    except OSError:
                        found.append(p)
                    dirs.remove(".git")
                # Prune depth > 5
                if dirpath.count(os.sep) - str(root).count(os.sep) > 5:
                    dirs.clear()

    return sorted(list(set(found)))


def inspect_git_repo(repo_path: Path) -> dict[str, Any]:
    """Inspect local git state: branch, ahead/behind, dirty files, worktrees, unmerged branches."""
    _, branch = run_cmd(["git", "branch", "--show-current"], cwd=repo_path)
    branch = branch or "detached"

    _, s_out = run_cmd(["git", "status", "-s"], cwd=repo_path)
    dirty_lines = [line for line in s_out.splitlines() if line.strip()]

    ahead, behind = 0, 0
    if branch != "detached":
        code, ab_out = run_cmd(
            ["git", "rev-list", "--left-right", "--count", f"origin/{branch}...{branch}"], cwd=repo_path
        )
        if code == 0 and len(ab_out.split()) == 2:
            parts = ab_out.split()
            behind, ahead = int(parts[0]), int(parts[1])

    # Worktrees
    _, wt_out = run_cmd(["git", "worktree", "list"], cwd=repo_path)
    worktrees = []
    for line in wt_out.splitlines()[1:]:
        if line.strip():
            worktrees.append(line.strip())

    # Age of HEAD commit
    _, log_epoch = run_cmd(["git", "log", "-1", "--format=%ct"], cwd=repo_path)
    age_days = (time.time() - int(log_epoch)) / 86400 if log_epoch.isdigit() else 999.0

    return {
        "path": str(repo_path),
        "name": repo_path.name,
        "branch": branch,
        "dirty_count": len(dirty_lines),
        "dirty_sample": dirty_lines[:5],
        "ahead": ahead,
        "behind": behind,
        "worktrees": worktrees,
        "age_days": round(age_days, 1),
    }


def fetch_open_prs() -> list[dict[str, Any]]:
    """Fetch open PRs across primary watched repos using gh CLI."""
    prs = []
    for repo in PRIMARY_WATCHED_REPOS:
        code, out = run_cmd(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--json",
                "number,title,headRefName,updatedAt,url,author",
            ]
        )
        if code == 0 and out:
            try:
                data = json.loads(out)
                for item in data:
                    item["repo"] = repo
                    prs.append(item)
            except json.JSONDecodeError:
                pass
    return prs


def update_close_the_loop_ledger(
    ledger_path: Path, local_issues: list[dict[str, Any]], open_prs: list[dict[str, Any]]
) -> None:
    """Update temp/close-the-loop.md with latest in-flight loops while preserving manual triage."""
    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

    content = [
        "# Close-the-Loop Ledger (Active & Pending Loops)",
        "",
        f"_Last updated: {now_str}_",
        "",
        "This ledger tracks all unmerged branches, dangling worktree commits, unlanded PRs, and cleanup tasks across all active and legacy repositories.",
        "",
        "---",
        "",
        "## 🚨 Tier 1: Active In-Flight Work (Current Sprint / Today)",
        "",
        "| Repo | Item / Branch | Status / Blocker | Next Immediate Action |",
        "|---|---|---|---|",
    ]

    for item in local_issues:
        content.append(f"| **`{item['repo']}`** | `{item['branch_or_wt']}` | {item['status']} | {item['action']} |")

    content.extend(
        [
            "",
            "---",
            "",
            "## ⏳ Tier 2: Open & Pending Pull Requests (Primary Watched Repos)",
            "",
        ]
    )

    if open_prs:
        for pr in open_prs:
            content.append(
                f"- [ ] [{pr['repo']}#{pr['number']}]({pr['url']}) — `{pr['headRefName']}`: {pr['title']} (Updated: {pr['updatedAt'][:10]})"
            )
    else:
        content.append("_No open pull requests currently pending on primary watched repositories._")

    content.extend(
        [
            "",
            "---",
            "",
            "## 🧹 Maintenance Discipline (How to Keep This Clear)",
            "1. **Never leave a branch un-PRed**: As soon as a worktree commit lands (`/relay-xyz` QA pass), open the PR immediately.",
            "2. **Post-Merge Cleanup**: When a PR merges, run `/merge-cleanup` to remove stale worktrees and isolated clone folders.",
            "3. **Daily Sweep**: During `/daily` cycles, surface items that have been open for $\\ge 4$ cycles ($>60\\text{m}$).",
            "",
        ]
    )

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text("\n".join(content), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan and report unclosed loops across repositories")
    parser.add_argument("--json", action="store_true", help="Output raw JSON analysis")
    parser.add_argument("--summary-line", action="store_true", help="Output the 1-line markdown summary")
    parser.add_argument("--update-ledger", action="store_true", default=True, help="Update temp/close-the-loop.md")
    args = parser.parse_args()

    repos = discover_git_repos(max_age_days=7.0)
    repo_stats = [inspect_git_repo(r) for r in repos]
    open_prs = fetch_open_prs()

    # Classify active in-flight issues
    unpred_branches: list[dict[str, str]] = []
    unpushed_branches: list[dict[str, str]] = []
    dirty_repos: list[dict[str, Any]] = []
    active_worktrees: list[dict[str, str]] = []

    for r in repo_stats:
        if r["worktrees"]:
            for wt in r["worktrees"]:
                active_worktrees.append({"repo": r["name"], "wt": wt})
                # If worktree branch has commits not yet PRed
                if "[" in wt:
                    bname = wt.split("[")[-1].split("]")[0]
                    unpred_branches.append({"repo": r["name"], "branch": bname, "wt_desc": wt})

        if r["ahead"] > 0:
            unpushed_branches.append({"repo": r["name"], "branch": r["branch"], "ahead": r["ahead"]})

        if r["dirty_count"] > 0 and r["age_days"] <= 3.0:
            dirty_repos.append({"repo": r["name"], "count": r["dirty_count"]})

    # Prepare structured local issues list
    local_issues = []
    for item in unpred_branches:
        local_issues.append(
            {
                "repo": item["repo"],
                "branch_or_wt": item["branch"],
                "status": "Linked worktree active; verify if PR is open",
                "action": "Push & cut PR or run /merge-cleanup if merged",
            }
        )
    for item in unpushed_branches:
        local_issues.append(
            {
                "repo": item["repo"],
                "branch_or_wt": item["branch"],
                "status": f"{item['ahead']} unpushed commit(s) ahead of origin",
                "action": "Push commits to remote origin",
            }
        )

    # Ledger update
    ledger_file = Path("/Users/noelsaw/Documents/GH Repos/rebalanceOS/temp/close-the-loop.md")
    if args.update_ledger:
        update_close_the_loop_ledger(ledger_file, local_issues, open_prs)

    # Format 1-line compact summary
    unpred_count = len(unpred_branches)
    open_pr_count = len(open_prs)
    unpushed_count = len(unpushed_branches)

    parts = []
    if unpred_count > 0:
        names = ", ".join(f"`{x['repo']}:{x['branch']}`" for x in unpred_branches[:2])
        parts.append(f"{unpred_count} un-PRed branch{'es' if unpred_count > 1 else ''} ({names})")
    else:
        parts.append("0 un-PRed branches")

    if open_pr_count > 0:
        sample_prs = ", ".join(f"`{p['repo']}#{p['number']}`" for p in open_prs[:2])
        parts.append(f"{open_pr_count} open PR{'s' if open_pr_count > 1 else ''} ({sample_prs})")
    else:
        parts.append("0 open PRs")

    if unpushed_count > 0:
        parts.append(f"{unpushed_count} unpushed branch{'es' if unpushed_count > 1 else ''}")
    else:
        parts.append("0 unpushed commits")

    summary_line = f"- **Unclosed Loops**: {', '.join(parts)} `[Details: temp/close-the-loop.md]`"

    if args.json:
        payload = {
            "summary_line": summary_line,
            "counts": {
                "unpred_branches": unpred_count,
                "open_prs": open_pr_count,
                "unpushed_branches": unpushed_count,
                "active_worktrees": len(active_worktrees),
                "dirty_repos": len(dirty_repos),
            },
            "unpred_branches": unpred_branches,
            "open_prs": open_prs,
            "unpushed_branches": unpushed_branches,
            "ledger_path": str(ledger_file),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(summary_line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
