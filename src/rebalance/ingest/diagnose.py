"""
Repo diagnostics — one tool to answer "is this repo watched?", "why isn't
it showing up?", and "why didn't this commit/PR show up?"

Composes the existing watched-repos / sync-status / ignore-list machinery
and adds an optional live GitHub probe so the user can tell apart "we
never synced" from "PAT can't see it".
"""

from __future__ import annotations

import urllib.error
from pathlib import Path
from typing import Any

from rebalance.ingest._http import GitHubClient, GitHubHTTPError
from rebalance.ingest.config import (
    get_github_ignored_repos,
    get_github_token,
    normalize_github_repo_name,
)
from rebalance.ingest.db import db_connection
from rebalance.ingest.index_ops import _activity_repos, _project_repos
from rebalance.ingest.registry import get_projects
from rebalance.lib.time_ops import now_utc, parse_utc_iso


# Mirrors github_knowledge.sync_github_repo's default lookback for issues/PRs.
DEFAULT_SYNC_WINDOW_DAYS = 90


def _days_since(iso: str | None) -> float | None:
    parsed = parse_utc_iso(iso)
    if parsed is None:
        return None
    delta = now_utc() - parsed
    return round(delta.total_seconds() / 86400.0, 2)


def _probe_get_json(client: GitHubClient, path: str) -> Any:
    """One shared-client GET for a live probe.

    The shared client retries 429/5xx with backoff and detects rate limits
    from response headers — a bare copy of the auth headers here previously
    turned one transient failure into a false "PAT cannot see this repo"
    verdict (the reason these probes no longer build their own requests).
    """
    return client.get_json(path)


def _probe_failure(key: str, exc: Exception) -> dict[str, Any]:
    """Map a probe exception to the backwards-stable error envelope."""
    if isinstance(exc, GitHubHTTPError):
        return {key: False, "status": exc.status, "error": str(exc)}
    reason = getattr(exc, "reason", None)
    return {key: False, "status": None, "error": str(reason if reason is not None else exc)}


def _live_probe_repo(repo: str, token: str) -> dict[str, Any]:
    """GET /repos/{owner}/{repo}; return {can_see, status, error}."""
    try:
        data = _probe_get_json(GitHubClient(token, job_label="diagnose"), f"/repos/{repo}")
    except (GitHubHTTPError, urllib.error.URLError, OSError) as exc:
        return _probe_failure("can_see", exc)
    return {
        "can_see": True,
        "status": 200,
        "default_branch": data.get("default_branch"),
        "private": bool(data.get("private")),
    }


def _live_probe_commit(repo: str, sha: str, token: str) -> dict[str, Any]:
    try:
        data = _probe_get_json(GitHubClient(token, job_label="diagnose"), f"/repos/{repo}/commits/{sha}")
    except (GitHubHTTPError, urllib.error.URLError, OSError) as exc:
        return _probe_failure("exists", exc)
    commit = data.get("commit") or {}
    committer = commit.get("committer") or {}
    # (... or [""]): an empty commit message is legal in git, and
    # "".splitlines() is [] — indexing it would crash the probe (agy review,
    # pre-existing in the hand-rolled version too).
    return {
        "exists": True,
        "sha": data.get("sha"),
        "committed_at": committer.get("date"),
        "message_first_line": ((commit.get("message") or "").splitlines() or [""])[0][:200],
    }


def _live_probe_pr(repo: str, pr: int, token: str) -> dict[str, Any]:
    try:
        data = _probe_get_json(GitHubClient(token, job_label="diagnose"), f"/repos/{repo}/pulls/{pr}")
    except (GitHubHTTPError, urllib.error.URLError, OSError) as exc:
        return _probe_failure("exists", exc)
    return {
        "exists": True,
        "state": data.get("state"),
        "merged": bool(data.get("merged")),
        "updated_at": data.get("updated_at"),
        "title": data.get("title"),
    }


def diagnose_repo(
    database_path: Path,
    *,
    repo: str,
    sha: str = "",
    pr: int | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """Walk the watched-repos + sync funnel for a single repo and report.

    See spike doc for the funnel; output shape stays backwards-stable as
    new checks get added (everything lives under named keys).
    """
    # Stage 1 — identity & config -----------------------------------------
    try:
        repo_norm = normalize_github_repo_name(repo)
    except ValueError as exc:
        return {
            "repo": repo,
            "verdict": "invalid_input",
            "summary": str(exc),
            "next_actions": [],
        }

    ignored = set(get_github_ignored_repos())
    is_ignored = repo_norm in ignored

    # Find the project that claims this repo (case-insensitive on owner/name).
    claimed_by_project: str | None = None
    project_status: str | None = None
    try:
        for project in get_projects(database_path):
            for r in project.get("repos") or []:
                if r and r.strip().lower() == repo_norm:
                    claimed_by_project = project.get("name")
                    project_status = project.get("status")
                    break
            if claimed_by_project:
                break
    except Exception:
        pass

    # Stage 2 — discovery membership --------------------------------------
    project_repos_lower = {r.lower() for r in _project_repos(database_path)}
    activity_repos_lower = {r.lower() for r in _activity_repos(database_path, since_days=14)}
    in_registry = repo_norm in project_repos_lower
    in_recent_activity = repo_norm in activity_repos_lower
    watched = (in_registry or in_recent_activity) and not is_ignored

    monitoring_reason: str | None = None
    if not watched:
        if is_ignored:
            monitoring_reason = f"{repo_norm} is on github_ignored_repos"
        elif claimed_by_project and project_status and project_status != "active":
            monitoring_reason = (
                f"claimed by project '{claimed_by_project}' but status={project_status!r} (only active projects sync)"
            )
        elif not in_registry and not in_recent_activity:
            monitoring_reason = "not in any active project's repos and no events in github_activity in the last 14 days"
        else:
            monitoring_reason = "not in watched set"

    # Stage 3 — sync freshness, Stage 4 — sha lookup, Stage 5 — pr lookup
    counts: dict[str, Any] = {"items": 0, "commits": 0, "comments": 0, "documents": 0}
    last_synced: str | None = None
    default_branch: str | None = None
    commit_block: dict[str, Any] | None = None
    pr_block: dict[str, Any] | None = None

    pr_num: int | None = None
    if pr is not None:
        try:
            pr_num = int(pr)
        except (TypeError, ValueError):
            pr_block = {"error": f"pr must be an integer, got {pr!r}"}

    try:
        from rebalance.ingest.db import fetch_repo_diagnostics

        with db_connection(database_path) as conn:
            diag = fetch_repo_diagnostics(conn, repo_norm, sha=sha, pr=pr_num)
            counts = diag["counts"]
            last_synced = diag["last_synced"]
            default_branch = diag["default_branch"]

            if sha:
                sha_clean = sha.strip().lower()
                matches = diag.get("commit_matches") or []
                commit_block = {
                    "sha_query": sha_clean,
                    "found_in_db": len(matches) > 0,
                }
                if matches:
                    commit_block["matches"] = matches
                    if len(matches) > 1:
                        commit_block["ambiguous"] = True

            if pr_num is not None and pr_block is None:
                pr_data = diag.get("pr_data")
                pr_block = {"number": pr_num, "found_in_db": pr_data is not None}
                if pr_data:
                    pr_block["state"] = pr_data["state"]
                    pr_block["merged"] = bool(pr_data["is_merged"])
                    pr_block["title"] = pr_data["title"]
                    pr_block["author"] = pr_data["author_login"]
                    pr_block["created_at"] = pr_data["created_at"]
                    pr_block["updated_at"] = pr_data["updated_at"]
                    pr_block["merged_at"] = pr_data["merged_at"]
                    pr_block["comments_count"] = pr_data["comments_count"]
                    pr_block["commits_count"] = pr_data["commits_count"]
                    pr_block["fetched_at"] = pr_data["fetched_at"]
                    pr_block["html_url"] = pr_data["html_url"]
    except Exception as exc:
        last_synced = None
        counts["__db_error__"] = str(exc)
        if sha and commit_block is not None:
            commit_block["db_error"] = str(exc)
        if pr_num is not None and pr_block is not None:
            pr_block["db_error"] = str(exc)

    staleness_days = _days_since(last_synced)
    if last_synced is None:
        freshness = "never_synced"
    elif staleness_days is not None and staleness_days > DEFAULT_SYNC_WINDOW_DAYS:
        freshness = "stale"
    else:
        freshness = "fresh"

    if commit_block and not commit_block.get("found_in_db"):
        if not watched:
            commit_block["likely_cause"] = "repo is not watched, so its commits are never ingested"
        elif freshness == "never_synced":
            commit_block["likely_cause"] = (
                "repo is watched but has never been synced — run refresh_index(scope=['github'])"
            )
        else:
            commit_block["likely_cause"] = (
                "current pipeline only ingests commits referenced by PRs in the "
                f"{DEFAULT_SYNC_WINDOW_DAYS}-day lookback. A bare commit on a "
                "branch with no PR (or one outside the window) will not appear."
            )

    if pr_block and not pr_block.get("found_in_db") and "error" not in pr_block:
        if not watched:
            pr_block["likely_cause"] = "repo is not watched, so its PRs are never ingested"
        elif freshness == "never_synced":
            pr_block["likely_cause"] = (
                "repo is watched but has never been synced — run refresh_index(scope=['github'])"
            )
        else:
            pr_block["likely_cause"] = (
                f"PR #{pr_block.get('number')} was not found in local DB (either outside "
                f"the {DEFAULT_SYNC_WINDOW_DAYS}-day lookback or never fetched)"
            )

    # Stage 6 — live PAT visibility --------------------------------------
    pat_block: dict[str, Any] = {"checked": False}
    if live:
        token = get_github_token()
        if not token:
            pat_block = {"checked": True, "can_see": False, "error": "no GitHub token configured"}
        else:
            probe = _live_probe_repo(repo_norm, token)
            pat_block = {"checked": True, **probe}
            if sha and isinstance(commit_block, dict):
                commit_block["live"] = _live_probe_commit(repo_norm, sha.strip(), token)
            if pr is not None and isinstance(pr_block, dict) and "error" not in pr_block:
                try:
                    pr_block["live"] = _live_probe_pr(repo_norm, int(pr), token)
                except (TypeError, ValueError):
                    pass

    # Verdict + summary ---------------------------------------------------
    next_actions: list[str] = []
    if is_ignored:
        verdict = "not_watched_ignored"
        summary = f"{repo_norm} is on the ignored list — remove it to start syncing."
        next_actions.append("remove_github_ignored_repo(repo)")
    elif claimed_by_project and project_status and project_status != "active":
        verdict = "not_watched_inactive_project"
        summary = (
            f"{repo_norm} is claimed by project {claimed_by_project!r} but its "
            f"status is {project_status!r}; only active projects are synced."
        )
        next_actions.append(f"set project {claimed_by_project!r} status to 'active'")
    elif not watched:
        verdict = "not_watched_no_signal"
        summary = (
            f"{repo_norm} is not watched: not in any active project's repos and no events seen in the last 14 days."
        )
        next_actions.append("add the repo to an active project's repos[] in the registry")
    elif freshness == "never_synced":
        verdict = "watched_never_synced"
        summary = f"{repo_norm} is watched but has never been synced."
        next_actions.append("refresh_index(scope=['github'])")
    elif freshness == "stale":
        verdict = "watched_but_stale"
        summary = (
            f"{repo_norm} is watched; last synced {staleness_days} days ago (> {DEFAULT_SYNC_WINDOW_DAYS}d window)."
        )
        next_actions.append(f"refresh_index(scope=['github'], repos=['{repo_norm}'])")
    else:
        verdict = "watched_and_fresh"
        summary = (
            f"{repo_norm} is watched; last synced {staleness_days} days ago. "
            f"items={counts['items']} commits={counts['commits']} "
            f"comments={counts['comments']} documents={counts['documents']}."
        )

    if live and pat_block.get("checked") and pat_block.get("can_see") is False:
        next_actions.insert(
            0,
            "GitHub PAT cannot see this repo — check token scopes or org SSO authorization",
        )

    return {
        "repo": repo_norm,
        "verdict": verdict,
        "summary": summary,
        "monitoring": {
            "watched": watched,
            "in_registry": in_registry,
            "in_recent_activity": in_recent_activity,
            "ignored": is_ignored,
            "claimed_by_project": claimed_by_project,
            "project_status": project_status,
            "reason": monitoring_reason,
        },
        "sync": {
            "last_synced": last_synced,
            "staleness_days": staleness_days,
            "freshness": freshness,
            "counts": counts,
            "default_branch": default_branch,
            "sync_window_days": DEFAULT_SYNC_WINDOW_DAYS,
        },
        "commit": commit_block,
        "pr": pr_block,
        "pat": pat_block,
        "next_actions": next_actions,
    }
