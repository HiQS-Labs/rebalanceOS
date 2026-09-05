"""Shared SQL read layer for activity signals, rollups, and presentations.

Part of 0.75.0 Fleet Engine (fe1) and GitHub issue #150.

All presentation and report query families live here rather than embedding raw
SQL in CLI scripts or ingest modules:
- GitHub balance per project (project-matching, idle detection)
- Organization activity rollups (dashboard org table)
- Day activity queries (PR commits, direct commits, items, comments)
- Watched repos activity queries
- Open items per project
- Repo diagnostics
- Release readiness facts
- Recent presentation queries (dashboard TUI / web: recent GitHub, vault, calendar, email, Figma)

Every query routes repo identity through an in-memory alias map so mirror-org rows
(the same repository recorded under a renamed or aliased org) and casing variants
collapse into a single canonical identity.

Reconciliation semantics (SOP §6 — one entity counted twice is a defect):
- ``github_activity`` is a snapshot table (``UNIQUE(login, repo_full_name, scan_date)
  ON CONFLICT REPLACE``): an org rename re-keys the row mid-day, leaving one day
  recorded twice. The copy with the latest ``scanned_at`` wins per
  (login, canonical repo, scan_date); callers never sum across spellings.
- ``github_items`` copies resolve to the newest record per canonical item
  *before* any state or milestone filter, so a stale "open" copy can never
  outvote a newer "closed" one.
- Comments are identified by their native GitHub comment id, so distinct
  comments sharing a timestamp both survive while mirror copies count once.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from rebalance.ingest.agent_tags import classify as classify_source
from rebalance.ingest.config import get_github_org_aliases
from rebalance.lib.time_ops import now_utc, parse_utc_iso


# Default cloud agent bots recognized as automated commit authors
CLOUD_AGENT_AUTHORS: tuple[str, ...] = (
    "lovable-dev[bot]",
    "lovable[bot]",
    "chatgpt-codex-connector[bot]",
    "codex-bot[bot]",
    "claude[bot]",
    "claude-bot[bot]",
)


def _get_alias_map() -> dict[str, str]:
    """Retrieve the org alias mapping."""
    return get_github_org_aliases()


def _canonical_lower(repo: str, alias_map: dict[str, str] | None = None) -> str:
    """Return lowercase canonical repo name with fast in-memory alias lookup."""
    name = (repo or "").strip()
    if not name:
        return ""
    if "/" not in name:
        return name.lower()
    owner, _, rest = name.partition("/")
    aliases = alias_map if alias_map is not None else _get_alias_map()
    target = aliases.get(owner.lower())
    if target:
        return f"{target.lower()}/{rest.lower()}"
    return name.lower()


def _canonical_name(repo: str, alias_map: dict[str, str] | None = None) -> str:
    """Return canonical repo name preserving target casing."""
    name = (repo or "").strip()
    if not name or "/" not in name:
        return name
    owner, _, rest = name.partition("/")
    aliases = alias_map if alias_map is not None else _get_alias_map()
    target = aliases.get(owner.lower())
    if target:
        return f"{target}/{rest}"
    return name


def _all_repo_spellings(repo: str, alias_map: dict[str, str] | None = None) -> list[str]:
    """Return all lowercase equivalent spellings of a repo (canonical, aliases, raw)."""
    aliases = alias_map if alias_map is not None else _get_alias_map()
    name = (repo or "").strip()
    if not name:
        return []
    canon = _canonical_name(name, aliases)
    canon_owner, _, rest = canon.partition("/")
    canon_lower = canon.lower()
    spellings = {name.lower(), canon_lower}
    if rest:
        rest_lower = rest.lower()
        for alias_k, alias_v in aliases.items():
            if alias_v.lower() == canon_owner.lower():
                spellings.add(f"{alias_k.lower()}/{rest_lower}")
    return sorted(spellings)


def _author_filter_sql(column: str, cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS) -> str:
    """SQL snippet matching an author column against operator login or bot logins."""
    bot_placeholders = ", ".join("?" for _ in cloud_authors)
    return (
        f"({column} = ? OR LOWER({column}) IN ({bot_placeholders}) "
        f"OR {column} LIKE '%[bot]' OR {column} LIKE 'claude%' "
        f"OR {column} LIKE 'codex%' OR {column} LIKE 'lovable%')"
    )


def _ensure_utc(dt: datetime) -> datetime:
    """Normalize datetime to timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utc_iso_floor(dt: datetime) -> str:
    """Return *dt* minus 2 hours as a UTC ISO 8601 string for >= SQL queries."""
    floor_dt = _ensure_utc(dt) - timedelta(hours=2)
    return floor_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _in_window(iso_str: str | None, start: datetime, end: datetime) -> bool:
    """Check if an ISO timestamp falls in [start, end)."""
    if not iso_str:
        return False
    parsed = parse_utc_iso(iso_str)
    if parsed is None:
        return False
    start_utc = _ensure_utc(start)
    end_utc = _ensure_utc(end)
    return start_utc <= parsed < end_utc


def _ts_or_epoch(value: str | None) -> datetime:
    """Parse an ISO timestamp for recency ranking; unparseable values sort oldest."""
    parsed = parse_utc_iso(value) if value else None
    return parsed if parsed is not None else datetime.min.replace(tzinfo=timezone.utc)


def _latest_activity_snapshots(
    conn: sqlite3.Connection,
    since_date: str,
    alias_map: dict[str, str],
) -> list[sqlite3.Row]:
    """Return in-window github_activity rows with superseded snapshots collapsed.

    github_activity is a snapshot table — UNIQUE(login, repo_full_name, scan_date)
    ON CONFLICT REPLACE — so each row overwrites the prior observation of that
    login/repo/day, and an org rename re-keys the row mid-day, leaving the same
    day recorded under two spellings. Per SOP §6 the snapshot with the latest
    scanned_at wins per (login, canonical repo, scan_date); ties prefer the
    canonical spelling, then the later insert. Callers aggregate the survivors
    and never sum across spellings of the same day.
    """
    rows = conn.execute(
        """
        SELECT id, login, repo_full_name, scan_date, commits, pushes, prs_opened,
               prs_merged, issues_opened, issue_comments, reviews, last_active_at,
               scanned_at
        FROM github_activity
        WHERE scan_date >= ?
        ORDER BY id
        """,
        (since_date,),
    ).fetchall()

    latest: dict[tuple[str, str, str], tuple[tuple, sqlite3.Row]] = {}
    for row in rows:
        canon_lower = _canonical_lower(row["repo_full_name"], alias_map)
        key = ((row["login"] or "").lower(), canon_lower, row["scan_date"] or "")
        rank = (
            _ts_or_epoch(row["scanned_at"]),
            1 if (row["repo_full_name"] or "").lower() == canon_lower else 0,
            row["id"],
        )
        incumbent = latest.get(key)
        if incumbent is None or rank > incumbent[0]:
            latest[key] = (rank, row)
    return [row for _rank, row in latest.values()]


def _resolve_newest_items(
    rows: list[sqlite3.Row],
    alias_map: dict[str, str],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Collapse mirrored github_items copies to the newest record per canonical item.

    github_items is keyed UNIQUE(repo_full_name, item_type, number) ON CONFLICT
    REPLACE, so an org rename re-keys the row and leaves two records of one item
    that can disagree on state or milestone. The newest record wins: latest
    updated_at (falling back to created_at), then latest fetched_at, then the
    canonical spelling, then the later insert. Callers must filter by state or
    milestone only after this resolution, never before.
    """
    resolved: dict[tuple[str, str, int], tuple[tuple, dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        canon_lower = _canonical_lower(row["repo_full_name"], alias_map)
        key = (canon_lower, row["item_type"] or "", int(row["number"] or 0))
        rank = (
            _ts_or_epoch(row["updated_at"] or row["created_at"]),
            _ts_or_epoch(row["fetched_at"]),
            1 if (row["repo_full_name"] or "").lower() == canon_lower else 0,
            index,
        )
        incumbent = resolved.get(key)
        if incumbent is None or rank > incumbent[0]:
            resolved[key] = (rank, dict(row))
    return {key: record for key, (_rank, record) in resolved.items()}


def _recency_desc(
    items: list[tuple[Any, dict[str, Any]]],
) -> list[tuple[Any, dict[str, Any]]]:
    """Order resolved (key, record) pairs newest-first for presentation output."""
    return sorted(
        items,
        key=lambda kv: (
            _ts_or_epoch(kv[1].get("updated_at") or kv[1].get("created_at")),
            kv[0][2],
        ),
        reverse=True,
    )


# ---------------------------------------------------------------------------
# 1. GitHub Balance per Project (F1)
# ---------------------------------------------------------------------------


def fetch_github_balance(
    conn: sqlite3.Connection,
    project_repos: dict[str, list[str]],
    since_days: int = 14,
) -> list[dict[str, Any]]:
    """Return GitHub activity balance per project using canonical repo identity.

    Collapses mirror-org spellings into one canonical entity and reconciles
    snapshot rows latest-scan-wins (SOP §6), so projects listing either or both
    spellings of a repo get complete, undoubled stats.
    """
    since_date = (now_utc() - timedelta(days=since_days)).strftime("%Y-%m-%d")  # READ-LAYER-OK: P1 read layer destination for since_cutoff (GH-150)
    alias_map = _get_alias_map()

    canonical_stats: dict[str, dict[str, Any]] = {}
    for row in _latest_activity_snapshots(conn, since_date, alias_map):
        canon_key = _canonical_lower(row["repo_full_name"], alias_map)
        if canon_key not in canonical_stats:
            canonical_stats[canon_key] = {
                "commits": 0,
                "pushes": 0,
                "prs_opened": 0,
                "prs_merged": 0,
                "issues_opened": 0,
                "issue_comments": 0,
                "reviews": 0,
                "last_active_at": None,
            }
        cs = canonical_stats[canon_key]
        cs["commits"] += row["commits"] or 0
        cs["pushes"] += row["pushes"] or 0
        cs["prs_opened"] += row["prs_opened"] or 0
        cs["prs_merged"] += row["prs_merged"] or 0
        cs["issues_opened"] += row["issues_opened"] or 0
        cs["issue_comments"] += row["issue_comments"] or 0
        cs["reviews"] += row["reviews"] or 0
        la = row["last_active_at"]
        if la and (cs["last_active_at"] is None or la > cs["last_active_at"]):
            cs["last_active_at"] = la

    results: list[dict[str, Any]] = []
    for project_name, repos in project_repos.items():
        total_commits = 0
        total_prs_opened = 0
        total_prs_merged = 0
        total_issues = 0
        repos_touched: list[str] = []
        last_active: str | None = None

        seen_canon_repos: set[str] = set()
        for repo in repos:
            canon_repo = _canonical_lower(repo, alias_map)
            if canon_repo in seen_canon_repos:
                continue
            seen_canon_repos.add(canon_repo)
            stats = canonical_stats.get(canon_repo)
            if not stats:
                continue
            repos_touched.append(repo)
            total_commits += stats.get("commits") or 0
            total_prs_opened += stats.get("prs_opened") or 0
            total_prs_merged += stats.get("prs_merged") or 0
            total_issues += stats.get("issues_opened") or 0
            la = stats.get("last_active_at")
            if la and (last_active is None or la > last_active):
                last_active = la

        results.append(
            {
                "project_name": project_name,
                "repos_linked": repos,
                "repos_touched": repos_touched,
                "total_commits": total_commits,
                "prs_opened": total_prs_opened,
                "prs_merged": total_prs_merged,
                "issues_opened": total_issues,
                "last_active_at": last_active,
                "is_idle": len(repos_touched) == 0,
            }
        )

    results.sort(key=lambda x: (x["is_idle"], -(len(x["repos_touched"]))), reverse=False)
    return results


# ---------------------------------------------------------------------------
# 2. Org Activity Rollup (Dashboard Org Table)
# ---------------------------------------------------------------------------


def fetch_org_activity(
    conn: sqlite3.Connection,
    since_days: int = 14,
    ignored_repos: list[str] | set[str] | tuple[str, ...] | None = None,
    limit: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return all github_activity rows grouped by canonical GitHub org.

    Collapses mirror org spellings into canonical targets and reconciles
    snapshot rows latest-scan-wins (SOP §6) before combining stats across
    distinct logins and days.
    """
    since_date = (now_utc() - timedelta(days=since_days)).strftime("%Y-%m-%d")  # READ-LAYER-OK: P1 read layer destination for since_cutoff (GH-150)
    alias_map = _get_alias_map()
    ignored_set = {_canonical_lower(r, alias_map) for r in (ignored_repos or []) if r}

    canon_repo_map: dict[str, dict[str, Any]] = {}
    for row in _latest_activity_snapshots(conn, since_date, alias_map):
        canon_name = _canonical_name(row["repo_full_name"], alias_map)
        canon_lower = canon_name.lower()
        if canon_lower in ignored_set:
            continue
        if canon_lower not in canon_repo_map:
            canon_repo_map[canon_lower] = {
                "repo_full_name": canon_name,
                "commits": 0,
                "prs_opened": 0,
                "prs_merged": 0,
                "issues_opened": 0,
                "last_active_at": None,
            }
        cr = canon_repo_map[canon_lower]
        cr["commits"] += int(row["commits"] or 0)
        cr["prs_opened"] += int(row["prs_opened"] or 0)
        cr["prs_merged"] += int(row["prs_merged"] or 0)
        cr["issues_opened"] += int(row["issues_opened"] or 0)
        la = row["last_active_at"]
        if la and (cr["last_active_at"] is None or la > cr["last_active_at"]):
            cr["last_active_at"] = la

    by_org: dict[str, list[dict[str, Any]]] = {}
    for cr in canon_repo_map.values():
        repo = cr["repo_full_name"]
        org = repo.split("/")[0] if "/" in repo else repo
        by_org.setdefault(org, []).append(cr)

    for org_repos in by_org.values():
        org_repos.sort(key=lambda r: r["last_active_at"] or "", reverse=True)
        if limit is not None and limit > 0:
            org_repos[:] = org_repos[:limit]

    return by_org


# ---------------------------------------------------------------------------
# 3. Day Activity Queries (Pulse & Reports)
# ---------------------------------------------------------------------------


def fetch_day_commits(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
    github_login: str,
    cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS,
) -> list[dict[str, Any]]:
    """Return author-scoped commits (PR commits ∪ direct commits) in [start, end).

    Deduplicates commits across PR and direct push sources, as well as mirror org
    spellings, using (canonical_repo.lower(), sha).
    """
    alias_map = _get_alias_map()
    sql_floor = _utc_iso_floor(start)
    commit_filter = _author_filter_sql("c.author_login", cloud_authors)

    rows = conn.execute(
        f"""
        SELECT c.repo_full_name, c.sha, c.message, c.committed_at, c.html_url,
               c.author_login, gi.head_ref
        FROM github_commits c
        LEFT JOIN github_items gi
          ON LOWER(gi.repo_full_name) = LOWER(c.repo_full_name)
         AND gi.item_type = c.item_type
         AND gi.number = c.item_number
        WHERE c.committed_at >= ?
          AND {commit_filter}
        ORDER BY c.committed_at DESC
        """,
        (sql_floor, github_login, *cloud_authors),
    ).fetchall()

    commits: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for r in rows:
        if _in_window(r["committed_at"], start, end):
            canon_name = _canonical_name(r["repo_full_name"], alias_map)
            sha = r["sha"] or ""
            key = (_canonical_lower(r["repo_full_name"], alias_map), sha)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            first_line = (r["message"] or "").splitlines()[0] if r["message"] else ""
            tag = classify_source(
                branch=r["head_ref"],
                author_login=r["author_login"],
                commit_message=r["message"],
            )
            commits.append(
                {
                    "repo": canon_name,
                    "sha": sha[:7] if sha else "",
                    "subject": first_line[:160],
                    "committed_at": r["committed_at"],
                    "html_url": r["html_url"] or "",
                    "author_login": r["author_login"] or "",
                    "source_tag": tag,
                    "source_kind": "pull_request",
                }
            )

    direct_filter = _author_filter_sql("d.author_login", cloud_authors)
    rows_direct = conn.execute(
        f"""
        SELECT d.repo_full_name, d.sha, d.message, d.committed_at, d.html_url,
               d.author_login, d.ref,
               (SELECT GROUP_CONCAT(path, char(10))
                  FROM github_direct_commit_files f
                 WHERE f.repo_full_name = d.repo_full_name AND f.sha = d.sha) AS paths
        FROM github_direct_commits d
        WHERE d.committed_at >= ?
          AND {direct_filter}
        ORDER BY d.committed_at DESC
        """,
        (sql_floor, github_login, *cloud_authors),
    ).fetchall()

    for r in rows_direct:
        if _in_window(r["committed_at"], start, end):
            canon_name = _canonical_name(r["repo_full_name"], alias_map)
            sha = r["sha"] or ""
            key = (_canonical_lower(r["repo_full_name"], alias_map), sha)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            message = r["message"] or ""
            commits.append(
                {
                    "repo": canon_name,
                    "sha": sha[:7] if sha else "",
                    "subject": message.splitlines()[0][:160] if message else "direct commit",
                    "committed_at": r["committed_at"],
                    "html_url": r["html_url"] or "",
                    "author_login": r["author_login"] or "",
                    "paths": (r["paths"] or "").splitlines(),
                    "source_tag": classify_source(
                        branch=r["ref"],
                        author_login=r["author_login"],
                        commit_message=message,
                    ),
                    "source_kind": "direct_push",
                }
            )

    return commits


def fetch_day_items(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
    github_login: str,
    cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS,
) -> list[dict[str, Any]]:
    """Return author-scoped github_items (PRs and issues) in [start, end)."""
    alias_map = _get_alias_map()
    sql_floor = _utc_iso_floor(start)
    item_filter = _author_filter_sql("author_login", cloud_authors)

    rows = conn.execute(
        f"""
        SELECT repo_full_name, item_type, number, title, state, html_url,
               created_at, updated_at, author_login, head_ref, body
        FROM github_items
        WHERE (created_at >= ? OR updated_at >= ?)
          AND (
                {item_filter}
                OR head_ref LIKE 'claude/%'
                OR head_ref LIKE 'codex/%'
                OR head_ref LIKE 'lovable-%'
                OR head_ref LIKE 'lovable/%'
          )
        ORDER BY COALESCE(updated_at, created_at) DESC
        """,
        (sql_floor, sql_floor, github_login, *cloud_authors),
    ).fetchall()

    items: list[dict[str, Any]] = []
    seen_items: set[tuple[str, str, int]] = set()

    for r in rows:
        created_in = _in_window(r["created_at"], start, end)
        updated_in = _in_window(r["updated_at"], start, end)
        if not (created_in or updated_in):
            continue
        canon_name = _canonical_name(r["repo_full_name"], alias_map)
        item_key = (_canonical_lower(r["repo_full_name"], alias_map), r["item_type"], r["number"])
        if item_key in seen_items:
            continue
        seen_items.add(item_key)
        items.append(
            {
                "repo": canon_name,
                "item_type": r["item_type"],
                "number": r["number"],
                "title": r["title"] or "",
                "state": r["state"] or "",
                "html_url": r["html_url"] or "",
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "author_login": r["author_login"] or "",
                "is_new": created_in,
                "source_tag": classify_source(
                    branch=r["head_ref"],
                    author_login=r["author_login"],
                    commit_message=r["body"] or "",
                ),
            }
        )

    return items


def fetch_day_comments(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
    github_login: str,
    cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS,
) -> list[dict[str, Any]]:
    """Return author-scoped github_comments in [start, end).

    Dedup identity is the native GitHub comment id (with comment type), so two
    distinct comments by one author that share a timestamp both survive while a
    mirror-spelling copy of the same comment counts once.
    """
    alias_map = _get_alias_map()
    sql_floor = _utc_iso_floor(start)
    comment_filter = _author_filter_sql("author_login", cloud_authors)

    rows = conn.execute(
        f"""
        SELECT repo_full_name, item_type, item_number, comment_type,
               github_comment_id, body, created_at, html_url, author_login
        FROM github_comments
        WHERE created_at >= ?
          AND {comment_filter}
        ORDER BY created_at DESC
        """,
        (sql_floor, github_login, *cloud_authors),
    ).fetchall()

    comments: list[dict[str, Any]] = []
    seen_comments: set[tuple[str, str, int, str, str]] = set()
    for r in rows:
        if _in_window(r["created_at"], start, end):
            canon_lower = _canonical_lower(r["repo_full_name"], alias_map)
            c_key = (
                canon_lower,
                r["comment_type"] or "",
                int(r["github_comment_id"] or 0),
                r["created_at"] or "",
                r["author_login"] or "",
            )
            if c_key in seen_comments:
                continue
            seen_comments.add(c_key)
            canon_name = _canonical_name(r["repo_full_name"], alias_map)
            preview = (r["body"] or "").splitlines()[0] if r["body"] else ""
            comments.append(
                {
                    "repo": canon_name,
                    "item_type": r["item_type"],
                    "item_number": r["item_number"],
                    "comment_type": r["comment_type"],
                    "preview": preview[:160],
                    "created_at": r["created_at"],
                    "html_url": r["html_url"] or "",
                    "author_login": r["author_login"] or "",
                }
            )

    return comments


# ---------------------------------------------------------------------------
# 4. Watched Activity Query (Pulse Watched Section)
# ---------------------------------------------------------------------------


def fetch_watched_activity(
    conn: sqlite3.Connection,
    external_repos: list[str],
    *,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Whole-repo activity for watched external repos in [start, end)."""
    if not external_repos:
        return []

    alias_map = _get_alias_map()
    canonical_targets = {
        _canonical_lower(r, alias_map): _canonical_name(r, alias_map)
        for r in external_repos
        if r and r.strip()
    }
    if not canonical_targets:
        return []

    sql_floor = _utc_iso_floor(start)
    activity: dict[str, dict[str, Any]] = {
        k: {
            "repo": v,
            "commits": 0,
            "items": [],
            "comments": 0,
            "_seen_shas": set(),
            "_seen_items": set(),
            "_seen_comments": set(),
        }
        for k, v in canonical_targets.items()
    }

    # PR commits
    rows = conn.execute(
        """
        SELECT repo_full_name, sha, committed_at FROM github_commits
        WHERE committed_at >= ?
        """,
        (sql_floor,),
    ).fetchall()
    for r in rows:
        canon_lower = _canonical_lower(r["repo_full_name"], alias_map)
        if canon_lower in activity and _in_window(r["committed_at"], start, end):
            sha = r["sha"] or ""
            if sha not in activity[canon_lower]["_seen_shas"]:
                activity[canon_lower]["_seen_shas"].add(sha)
                activity[canon_lower]["commits"] += 1

    # Direct commits
    rows = conn.execute(
        """
        SELECT repo_full_name, sha, committed_at FROM github_direct_commits
        WHERE committed_at >= ?
        """,
        (sql_floor,),
    ).fetchall()
    for r in rows:
        canon_lower = _canonical_lower(r["repo_full_name"], alias_map)
        if canon_lower in activity and _in_window(r["committed_at"], start, end):
            sha = r["sha"] or ""
            if sha not in activity[canon_lower]["_seen_shas"]:
                activity[canon_lower]["_seen_shas"].add(sha)
                activity[canon_lower]["commits"] += 1

    # Items
    rows = conn.execute(
        """
        SELECT repo_full_name, item_type, number, title, state, html_url,
               created_at, updated_at
        FROM github_items
        WHERE (created_at >= ? OR updated_at >= ?)
        ORDER BY COALESCE(updated_at, created_at) DESC
        """,
        (sql_floor, sql_floor),
    ).fetchall()
    for r in rows:
        canon_lower = _canonical_lower(r["repo_full_name"], alias_map)
        if canon_lower not in activity:
            continue
        item_key = (r["item_type"], r["number"])
        if item_key in activity[canon_lower]["_seen_items"]:
            continue
        created_in = _in_window(r["created_at"], start, end)
        updated_in = _in_window(r["updated_at"], start, end)
        if not (created_in or updated_in):
            continue
        activity[canon_lower]["_seen_items"].add(item_key)
        activity[canon_lower]["items"].append(
            {
                "item_type": r["item_type"],
                "number": r["number"],
                "title": r["title"] or "",
                "state": r["state"] or "",
                "html_url": r["html_url"] or "",
                "is_new": created_in,
            }
        )

    # Comments — identity is the native GitHub comment id (with comment type),
    # so distinct comments sharing a timestamp both count while mirror copies
    # of one comment count once.
    rows = conn.execute(
        """
        SELECT repo_full_name, item_type, item_number, comment_type,
               github_comment_id, created_at, author_login FROM github_comments
        WHERE created_at >= ?
        """,
        (sql_floor,),
    ).fetchall()
    for r in rows:
        canon_lower = _canonical_lower(r["repo_full_name"], alias_map)
        if canon_lower in activity and _in_window(r["created_at"], start, end):
            c_key = (
                r["comment_type"] or "",
                int(r["github_comment_id"] or 0),
                r["created_at"] or "",
                r["author_login"] or "",
            )
            if c_key not in activity[canon_lower]["_seen_comments"]:
                activity[canon_lower]["_seen_comments"].add(c_key)
                activity[canon_lower]["comments"] += 1

    out: list[dict[str, Any]] = []
    for entry in activity.values():
        commits = entry["commits"]
        items = entry["items"]
        comments = entry["comments"]
        if commits or items or comments:
            out.append(
                {
                    "repo": entry["repo"],
                    "commits": commits,
                    "items": items,
                    "comments": comments,
                }
            )

    out.sort(key=lambda a: (len(a["items"]), a["commits"], a["comments"]), reverse=True)
    return out


# ---------------------------------------------------------------------------
# 5. Open Items for Projects (Next Actions)
# ---------------------------------------------------------------------------


def fetch_open_items_for_projects(
    conn: sqlite3.Connection,
    project_repos: dict[str, list[str]],
) -> dict[str, list[dict[str, Any]]]:
    """Read open GitHub items per project using canonical repo identity.

    Mirrored copies of one item resolve to the newest record first; only then is
    the open state checked, so a stale mirror copy saying "open" can never keep
    a closed item on the list (SOP §6).
    """
    alias_map = _get_alias_map()
    out: dict[str, list[dict[str, Any]]] = {project: [] for project in project_repos}
    repo_to_projects: dict[str, set[str]] = {}
    for project, repos in project_repos.items():
        for repo in repos:
            canon_lower = _canonical_lower(repo, alias_map)
            if canon_lower:
                repo_to_projects.setdefault(canon_lower, set()).add(project)

    if not repo_to_projects:
        return out

    rows = conn.execute(
        """
        SELECT repo_full_name, item_type, number, title, state, html_url,
               created_at, updated_at, fetched_at
        FROM github_items
        """
    ).fetchall()

    resolved = _recency_desc(_resolve_newest_items(rows, alias_map).items())
    for key, record in resolved:
        if (record.get("state") or "").lower() != "open":
            continue
        canon_lower, _item_type, _number = key
        for project in repo_to_projects.get(canon_lower, set()):
            out[project].append(
                {
                    "repo": _canonical_name(record["repo_full_name"], alias_map),
                    "item_type": record["item_type"],
                    "number": record["number"],
                    "title": record["title"] or "",
                    "html_url": record["html_url"] or "",
                    "created_at": record["created_at"],
                    "updated_at": record["updated_at"],
                }
            )

    return out


# ---------------------------------------------------------------------------
# 6. Repo Diagnostics Query (Diagnose)
# ---------------------------------------------------------------------------


def fetch_repo_diagnostics(
    conn: sqlite3.Connection,
    repo_name: str,
    *,
    sha: str | None = None,
    pr: int | None = None,
) -> dict[str, Any]:
    """Diagnostic data for a single repo: meta, table counts, commits, and PRs."""
    alias_map = _get_alias_map()
    canon_name = _canonical_name(repo_name, alias_map)
    spellings = _all_repo_spellings(repo_name, alias_map)
    placeholders = ",".join("?" * len(spellings))

    # Meta
    meta_row = conn.execute(
        f"SELECT default_branch, fetched_at FROM github_repo_meta WHERE LOWER(repo_full_name) IN ({placeholders})",
        spellings,
    ).fetchone()

    counts: dict[str, int] = {"items": 0, "commits": 0, "comments": 0, "documents": 0}
    last_synced: str | None = None

    for table, key, distinct_expr in (
        ("github_items", "items", "DISTINCT item_type || ':' || number"),
        ("github_commits", "commits", "DISTINCT sha"),
        ("github_comments", "comments", "DISTINCT COALESCE(github_comment_id, item_type || ':' || item_number || ':' || created_at)"),
        ("github_documents", "documents", "DISTINCT source_type || ':' || source_number || ':' || doc_type"),
    ):
        row = conn.execute(
            f"SELECT COUNT({distinct_expr}) AS c, MAX(fetched_at) AS m FROM {table} WHERE LOWER(repo_full_name) IN ({placeholders})",
            spellings,
        ).fetchone()
        if row:
            counts[key] = int(row["c"] or 0)
            candidate = row["m"]
            if candidate and (not last_synced or candidate > last_synced):
                last_synced = candidate

    if not last_synced and meta_row:
        last_synced = meta_row["fetched_at"]

    # SHA lookup
    commit_matches: list[dict[str, Any]] = []
    if sha:
        sha_clean = sha.strip().lower()
        rows = conn.execute(
            f"""
            SELECT sha, item_type, item_number, author_login,
                   committed_at, message, html_url, repo_full_name
            FROM github_commits
            WHERE LOWER(repo_full_name) IN ({placeholders}) AND LOWER(sha) LIKE ?
            ORDER BY CASE WHEN repo_full_name = ? THEN 0 ELSE 1 END, committed_at DESC
            """,
            (*spellings, f"{sha_clean}%", canon_name),
        ).fetchall()
        seen_shas: set[str] = set()
        for r in rows:
            s = r["sha"]
            if s not in seen_shas:
                seen_shas.add(s)
                commit_matches.append(
                    {
                        "sha": r["sha"],
                        "associated": f"{r['item_type']}#{r['item_number']}",
                        "author": r["author_login"],
                        "committed_at": r["committed_at"],
                        "message_first_line": (r["message"] or "").splitlines()[0][:200] if r["message"] else "",
                        "html_url": r["html_url"],
                    }
                )
                if len(commit_matches) >= 5:
                    break

    # PR lookup
    pr_data: dict[str, Any] | None = None
    if pr is not None:
        row = conn.execute(
            f"""
            SELECT title, state, is_merged, author_login, created_at,
                   updated_at, merged_at, comments_count,
                   commits_count, fetched_at, html_url, repo_full_name
            FROM github_items
            WHERE LOWER(repo_full_name) IN ({placeholders})
              AND item_type = 'pull_request' AND number = ?
            ORDER BY CASE WHEN repo_full_name = ? THEN 0 ELSE 1 END, updated_at DESC
            LIMIT 1
            """,
            (*spellings, pr, canon_name),
        ).fetchone()
        if row:
            d = dict(row)
            d.pop("repo_full_name", None)
            pr_data = d

    return {
        "repo_full_name": canon_name,
        "default_branch": meta_row["default_branch"] if meta_row else None,
        "last_synced": last_synced,
        "counts": counts,
        "commit_matches": commit_matches,
        "pr_data": pr_data,
    }


# ---------------------------------------------------------------------------
# 7. Release Readiness Query (Github Readiness)
# ---------------------------------------------------------------------------


def fetch_release_readiness_data(
    conn: sqlite3.Connection,
    repo_full_name: str,
    *,
    milestone_title: str = "",
) -> dict[str, Any]:
    """Retrieve raw milestone, issues, PRs, and links for release readiness evaluation.

    All item facts derive from one resolved set (newest record per canonical
    item wins, SOP §6) before any state or milestone filter is applied.
    """
    alias_map = _get_alias_map()
    spellings = _all_repo_spellings(repo_full_name, alias_map)
    placeholders = ",".join("?" * len(spellings))

    repo_meta_row = conn.execute(
        f"SELECT * FROM github_repo_meta WHERE LOWER(repo_full_name) IN ({placeholders})",
        spellings,
    ).fetchone()
    repo_meta = dict(repo_meta_row) if repo_meta_row else None

    # Milestone
    milestone: dict[str, Any] | None = None
    if milestone_title.strip():
        m_row = conn.execute(
            f"""
            SELECT * FROM github_milestones
            WHERE LOWER(repo_full_name) IN ({placeholders}) AND title = ?
            LIMIT 1
            """,
            (*spellings, milestone_title.strip()),
        ).fetchone()
        if m_row:
            milestone = dict(m_row)
    else:
        m_rows = conn.execute(
            f"""
            SELECT * FROM github_milestones
            WHERE LOWER(repo_full_name) IN ({placeholders}) AND state = 'open'
            ORDER BY
                CASE WHEN open_issues > 0 THEN 0 ELSE 1 END,
                CASE WHEN due_on IS NULL THEN 1 ELSE 0 END,
                due_on ASC,
                updated_at DESC
            """,
            spellings,
        ).fetchall()
        if m_rows:
            milestone = dict(m_rows[0])

    # One resolution pass over every copy of this repo's items: the newest
    # record per (canonical repo, item_type, number) wins (SOP §6). Every
    # item-derived fact below — milestone issues, PR list, promotion PR,
    # deployment issue — reads this resolved set, so a stale mirror copy can
    # never outvote the newest state.
    item_rows = conn.execute(
        f"""
        SELECT * FROM github_items
        WHERE LOWER(repo_full_name) IN ({placeholders})
        """,
        spellings,
    ).fetchall()
    resolved_items = _resolve_newest_items(item_rows, alias_map)

    deduped_issues: list[dict[str, Any]] = []
    deduped_prs: list[dict[str, Any]] = []
    for (_canon_lower, item_type, _number), record in resolved_items.items():
        d = dict(record)
        d["repo_full_name"] = _canonical_name(d["repo_full_name"], alias_map)
        if item_type == "issue":
            deduped_issues.append(d)
        elif item_type == "pull_request":
            deduped_prs.append(d)
    deduped_issues.sort(key=lambda d: (d.get("state") or "", int(d["number"])))
    deduped_prs.sort(key=lambda d: int(d["number"]))
    if milestone:
        deduped_issues = [
            d for d in deduped_issues if (d.get("milestone_title") or "") == milestone["title"]
        ]

    seen_links: set[tuple[int, int]] = set()
    deduped_links: list[dict[str, Any]] = []
    link_rows = conn.execute(
        f"""
        SELECT source_number, target_number
        FROM github_links
        WHERE LOWER(repo_full_name) IN ({placeholders})
          AND source_type = 'pull_request'
          AND target_type = 'issue'
        """,
        spellings,
    ).fetchall()
    for r in link_rows:
        d = dict(r)
        key = (int(d["source_number"]), int(d["target_number"]))
        if key not in seen_links:
            seen_links.add(key)
            deduped_links.append(d)

    # Branches
    branch_rows = conn.execute(
        f"""
        SELECT name, is_default
        FROM github_branches
        WHERE LOWER(repo_full_name) IN ({placeholders})
        ORDER BY name ASC
        """,
        spellings,
    ).fetchall()
    seen_branches: set[str] = set()
    branches: list[dict[str, Any]] = []
    for r in branch_rows:
        b_name = r["name"]
        if b_name not in seen_branches:
            seen_branches.add(b_name)
            branches.append(dict(r))

    # Promotion PR — derived from the resolved set: a stale open copy under an
    # old spelling must not outrank a newer closed record.
    default_branch = repo_meta.get("default_branch") or "main" if repo_meta else "main"
    prod_branches = list({"main", default_branch})
    promotion_pr: dict[str, Any] | None = None
    for d in deduped_prs:
        if d.get("state") != "open" or d.get("base_ref") not in prod_branches:
            continue
        head_ref = d.get("head_ref") or ""
        if head_ref != default_branch and not head_ref.startswith("release/"):
            continue
        if promotion_pr is None or _ts_or_epoch(d.get("updated_at")) > _ts_or_epoch(
            promotion_pr.get("updated_at")
        ):
            promotion_pr = d

    # Deployment issue — same resolved set; the title pattern matches
    # "...deployment: <milestone>..." case-insensitively.
    deployment_issue: dict[str, Any] | None = None
    if milestone:
        mstone_lower = milestone["title"].lower()
        for (_canon_lower, item_type, _number), record in resolved_items.items():
            if item_type != "issue":
                continue
            title = (record.get("title") or "").lower()
            pos = title.find("deployment:")
            if pos == -1 or record.get("state") != "open":
                continue
            if title.find(mstone_lower, pos) == -1:
                continue
            if deployment_issue is None or _ts_or_epoch(record.get("updated_at")) > _ts_or_epoch(
                deployment_issue.get("updated_at")
            ):
                d = dict(record)
                d["repo_full_name"] = _canonical_name(d["repo_full_name"], alias_map)
                deployment_issue = d

    # Recent release
    rel_row = conn.execute(
        f"""
        SELECT tag_name, published_at, target_commitish
        FROM github_releases
        WHERE LOWER(repo_full_name) IN ({placeholders})
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT 1
        """,
        spellings,
    ).fetchone()
    recent_release = dict(rel_row) if rel_row else None

    return {
        "repo_meta": repo_meta,
        "milestone": milestone,
        "issues": deduped_issues,
        "prs": deduped_prs,
        "links": deduped_links,
        "branches": branches,
        "promotion_pr": promotion_pr,
        "deployment_issue": deployment_issue,
        "recent_release": recent_release,
    }


# ---------------------------------------------------------------------------
# 8. Dashboard Presentation Queries (Shared SQL for TUI & Web)
# ---------------------------------------------------------------------------


def fetch_recent_github(
    conn: sqlite3.Connection,
    limit: int = 9,
) -> list[dict[str, Any]]:
    """Recent GitHub events (PRs and issues) across all repos."""
    alias_map = _get_alias_map()
    rows = conn.execute(
        """
        SELECT repo_full_name, item_type, number, title, state, is_merged,
               author_login, comments_count, created_at, updated_at
        FROM github_items
        ORDER BY COALESCE(updated_at, created_at) DESC
        """
    ).fetchall()

    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for r in rows:
        canon_lower = _canonical_lower(r["repo_full_name"], alias_map)
        key = (canon_lower, r["item_type"], r["number"])
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "repo_full_name": _canonical_name(r["repo_full_name"], alias_map),
                "item_type": r["item_type"],
                "number": r["number"],
                "title": r["title"] or "",
                "state": r["state"] or "",
                "is_merged": bool(r["is_merged"]),
                "author_login": r["author_login"] or "",
                "comments_count": r["comments_count"] or 0,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
        )
        if len(out) >= limit:
            break
    return out


def fetch_repo_activity_counts(
    conn: sqlite3.Connection,
    days: int = 7,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Top active repos ranked by activity score in the last N days.

    Snapshot rows reconcile latest-scan-wins per (login, canonical repo, day)
    before scoring, so a renamed org's two spellings of one day count once.
    """
    since_date = (now_utc() - timedelta(days=days)).strftime("%Y-%m-%d")
    alias_map = _get_alias_map()

    canon_map: dict[str, dict[str, Any]] = {}
    for row in _latest_activity_snapshots(conn, since_date, alias_map):
        c_name = _canonical_name(row["repo_full_name"], alias_map)
        c_lower = c_name.lower()
        if c_lower not in canon_map:
            canon_map[c_lower] = {
                "repo": c_name,
                "score": 0,
                "commits": 0,
                "prs": 0,
                "issues": 0,
                "last_active_at": None,
            }
        cm = canon_map[c_lower]
        commits = row["commits"] or 0
        prs_opened = row["prs_opened"] or 0
        prs_merged = row["prs_merged"] or 0
        issues_opened = row["issues_opened"] or 0
        issue_comments = row["issue_comments"] or 0
        reviews = row["reviews"] or 0
        cm["score"] += (
            commits + prs_opened + prs_merged + issues_opened + issue_comments + reviews
        )
        cm["commits"] += commits
        cm["prs"] += prs_opened + prs_merged
        cm["issues"] += issues_opened
        la = row["last_active_at"]
        if la and (cm["last_active_at"] is None or la > cm["last_active_at"]):
            cm["last_active_at"] = la

    ranked = sorted(
        (cm for cm in canon_map.values() if cm["score"] > 0),
        key=lambda x: x["score"],
        reverse=True,
    )
    return ranked[:limit]


def fetch_open_prs(
    conn: sqlite3.Connection,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Open PRs with review decision and check status.

    Mirrored copies of one PR resolve to the newest record before the open-state
    check, so a stale "open" copy can never list a PR that has since closed.
    """
    alias_map = _get_alias_map()
    rows = conn.execute(
        """
        SELECT repo_full_name, item_type, number, title, author_login, state, is_draft,
               review_decision, check_status, comments_count, created_at, updated_at,
               fetched_at
        FROM github_items
        WHERE item_type = 'pull_request'
        """
    ).fetchall()

    out: list[dict[str, Any]] = []
    for _key, record in _recency_desc(_resolve_newest_items(rows, alias_map).items()):
        if (record.get("state") or "") != "open":
            continue
        out.append(
            {
                "repo_full_name": _canonical_name(record["repo_full_name"], alias_map),
                "number": record["number"],
                "title": record["title"] or "",
                "author_login": record["author_login"] or "",
                "is_draft": bool(record["is_draft"]),
                "review_decision": record["review_decision"] or "",
                "check_status": record["check_status"] or "",
                "comments_count": record["comments_count"] or 0,
                "created_at": record["created_at"],
                "updated_at": record["updated_at"],
            }
        )
        if len(out) >= limit:
            break
    return out


__all__ = [
    "fetch_github_balance",
    "fetch_org_activity",
    "fetch_day_commits",
    "fetch_day_items",
    "fetch_day_comments",
    "fetch_watched_activity",
    "fetch_open_items_for_projects",
    "fetch_repo_diagnostics",
    "fetch_release_readiness_data",
    "fetch_recent_github",
    "fetch_repo_activity_counts",
    "fetch_open_prs",
]
