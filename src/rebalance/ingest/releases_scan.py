"""GH-310: opt-in, read-only scan of local RELEASES ledgers under operator-given dirs.

Finds ``releases.db`` ledgers in git clones/worktrees below the directories the operator
names (no guessed paths), reads each through the read-only gateway (``mode=ro``) and
reports the repo's in-progress and parked roadmap tasks, disagreements between clones,
and per-ledger errors. Never writes, migrates or runs the releases CLI; a WAL-mode
ledger is skipped so no ``-shm`` sidecar can be created.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.lib.git_ops import parse_github_remote_url, run_git, should_descend

LEDGER_NAME = "releases.db"
_IN_PROGRESS_MARKER = "\U0001f6a7"
_REQUIRED_COLUMNS = {"global_id", "repo_id", "gh_number", "title", "section", "status_marker"}
_OPTIONAL_COLUMNS = (
    "status_label",
    "rating_pri",
    "rating_sev",
    "rating_appeal",
    "rating_effort",
    "issue_url",
    "doc_path",
    "updated_at",
)
_INTEGRATION_BRANCHES = ("development", "main")


def discover_ledgers(dirs: list[str], *, max_depth: int = 3, cap: int = 200) -> dict[str, Any]:
    """Ledger roots (a dir holding ``releases.db`` and ``.git``) at directory depth <= max_depth."""
    roots: list[Path] = []
    seen: set[Path] = set()
    skipped_non_repo = 0
    truncated = False
    for raw in dirs:
        base = Path(raw).expanduser()
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            here = Path(dirpath)
            depth = len(here.relative_to(base).parts)
            dirnames[:] = sorted(d for d in dirnames if should_descend(d)) if depth < max_depth else []
            if LEDGER_NAME not in filenames:
                continue
            if not (here / ".git").exists():
                skipped_non_repo += 1
                continue
            key = here.resolve()
            if key in seen:
                continue
            if len(roots) >= cap:
                truncated = True
                break
            seen.add(key)
            roots.append(here)
        if truncated:
            break
    return {"roots": roots, "skipped_non_repo": skipped_non_repo, "truncated": truncated}


def _git(path: Path, *args: str) -> str:
    try:
        done = run_git(path, *args, timeout=5)
    except Exception:  # OSError or subprocess.TimeoutExpired: no git answer is an empty answer
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def _origin_repo(path: Path, hops: int = 3) -> str:
    """owner/name of the clone's origin, following local-path origins for a few hops."""
    for _ in range(hops + 1):
        url = _git(path, "remote", "get-url", "origin")
        repo = parse_github_remote_url(url)
        if repo:
            return repo
        local = Path(url.removeprefix("file://")).expanduser() if url else None
        if local is None or not local.is_dir():
            return ""
        path = local
    return ""


def _is_wal(db_path: Path) -> bool:
    with db_path.open("rb") as handle:
        header = handle.read(20)
    return len(header) == 20 and header[18] == 2 and header[19] == 2


def _task_status(row: sqlite3.Row) -> str | None:
    label = (row["status_label"] or "").strip().lower()
    section = (row["section"] or "").strip().lower()
    if label == "in-progress" or row["status_marker"] == _IN_PROGRESS_MARKER or section.startswith("in progress"):
        return "in-progress"
    if section.startswith("queue"):
        return label or "parked"
    return None


def _read_ledger(root: Path, repo_full_name: str) -> dict[str, Any]:
    repo_lower = repo_full_name.casefold()
    basename = repo_lower.rsplit("/", 1)[-1]
    entry: dict[str, Any] = {
        "clone_path": str(root),
        "branch": _git(root, "branch", "--show-current"),
        "error": None,
        "matched_rows": 0,
        "other_repo_rows": 0,
        "tasks": [],
    }
    origin: str | None = None

    def origin_matches() -> bool:
        nonlocal origin
        if origin is None:
            origin = _origin_repo(root)
        return bool(origin) and origin.casefold() == repo_lower

    db_path = root / LEDGER_NAME
    try:
        if _is_wal(db_path):
            entry["error"] = "wal-mode"
            return entry
        with db_connection_readonly(db_path) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"roadmap_items", "repos"} <= tables:
                entry["error"] = "missing-table"
                return entry
            columns = {r[1] for r in conn.execute("PRAGMA table_info(roadmap_items)")}
            if not _REQUIRED_COLUMNS <= columns:
                entry["error"] = "unsupported-schema"
                return entry
            slugs = {r["id"]: (r["slug"] or "") for r in conn.execute("SELECT id, slug FROM repos")}
            optional = ", ".join(c if c in columns else f"NULL AS {c}" for c in _OPTIONAL_COLUMNS)
            rows = conn.execute(
                "SELECT global_id, repo_id, gh_number, title, section, status_marker, "
                f"{optional} FROM roadmap_items ORDER BY id"
            ).fetchall()
    except (OSError, sqlite3.Error):
        entry["error"] = "unreadable"
        return entry

    unresolved = 0
    for row in rows:
        slug = slugs.get(row["repo_id"], "").casefold()
        if "/" in slug:
            matches = slug == repo_lower
        elif slug == basename:
            matches = origin_matches()
            unresolved += 0 if origin else 1
        else:
            matches = False
        if not matches:
            entry["other_repo_rows"] += 1
            continue
        entry["matched_rows"] += 1
        status = _task_status(row)
        if status is None:
            continue
        ratings = [row[c] for c in ("rating_pri", "rating_sev", "rating_appeal", "rating_effort")]
        entry["tasks"].append(
            {
                "repo": repo_full_name,
                "clone_path": entry["clone_path"],
                "branch": entry["branch"],
                "global_id": row["global_id"],
                "gh_number": row["gh_number"],
                "title": row["title"] or "",
                "section": row["section"] or "",
                "status": status,
                "rating": "/".join(str(v) for v in ratings) if all(v is not None for v in ratings) else None,
                "issue_url": row["issue_url"] or "",
                "doc_path": row["doc_path"] or "",
                "updated_at": row["updated_at"] or "",
            }
        )
    if unresolved and not entry["matched_rows"]:
        entry["error"] = "identity-unresolved"
    return entry


def scan_releases(dirs: list[str], repo_full_name: str, *, max_depth: int = 3) -> dict[str, Any]:
    """Per-repo view of local ledger tasks across every clone found under *dirs*."""
    repo_full_name = repo_full_name.strip()
    found = discover_ledgers(dirs, max_depth=max_depth)
    ledgers: list[dict[str, Any]] = []
    other_repo_ledgers = 0
    for root in found["roots"]:
        entry = _read_ledger(root, repo_full_name)
        if entry["error"] in ("unreadable", "missing-table", "unsupported-schema", "wal-mode"):
            origin = _origin_repo(root)
            if origin and origin.casefold() != repo_full_name.casefold():
                other_repo_ledgers += 1
                continue
        elif not entry["error"] and not entry["matched_rows"]:
            other_repo_ledgers += 1
            continue
        ledgers.append(entry)

    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in ledgers:
        for task in entry["tasks"]:
            key = f"#{task['gh_number']}" if task["gh_number"] is not None else str(task["global_id"])
            groups.setdefault(key, []).append(task)
    tasks: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for key, items in groups.items():
        preferred = max(items, key=lambda t: (t["updated_at"], t["branch"] in _INTEGRATION_BRANCHES))
        disagree = len({(t["section"], t["status"]) for t in items}) > 1
        if disagree:
            conflicts.append(
                {
                    "key": key,
                    "preferred_clone": preferred["clone_path"],
                    "values": [
                        {k: t[k] for k in ("clone_path", "branch", "section", "status", "updated_at")} for t in items
                    ],
                }
            )
        tasks.append({**preferred, "clones": len(items), "conflict": disagree})
    tasks.sort(
        key=lambda t: (t["status"] != "in-progress", t["gh_number"] is None, t["gh_number"] or 0, t["global_id"])
    )
    listed = [{k: e[k] for k in ("clone_path", "branch", "error")} | {"tasks": len(e["tasks"])} for e in ledgers]
    return {
        "scanned_dirs": [str(Path(d).expanduser()) for d in dirs],
        "ledgers_found": len(found["roots"]),
        "skipped_non_repo": found["skipped_non_repo"],
        "truncated": found["truncated"],
        "other_repo_ledgers": other_repo_ledgers,
        "ledgers": listed,
        "tasks": tasks,
        "conflicts": conflicts,
        "drift": [],
        "counts": {
            "ledgers": len(ledgers),
            "ledger_errors": sum(1 for e in ledgers if e["error"]),
            "tasks": len(tasks),
            "in_progress": sum(1 for t in tasks if t["status"] == "in-progress"),
            "conflicts": len(conflicts),
            "drift": 0,
        },
    }
