"""T3 Code session activity — an opt-in, read-only raw source (GH-375).

T3 Code keeps every thread, run and message for all of its agent providers in one
local SQLite store (``~/.t3/userdata/statev2.sqlite``). This module turns that
store's *metadata* into a per-device "repo worked, by which agent provider, on
which UTC day" signal in ``agent_session_activity``, plus one health row per
device in ``agent_session_source_health`` so ``rebalance doctor`` can report the
source without opening the T3 file.

This module is the single writer of both tables. It never writes to T3's store.

Privacy contract: no message text, prompt body or auth/secret/pairing/webhook
table is ever selected. The only JSON payload paths read are ``$.createdBy``
(threads and messages), ``$.branch`` and ``$.pullRequests`` (threads); from each
pull-request object only its ``url`` string is kept.

Aggregation contract: runs, messages and thread metadata are three independently
grouped streams merged per ``(repo, day, provider)`` in Python — never joined
row-to-row, so counts cannot multiply. A message's provider comes from its run
(a primary-key lookup) and falls back to the thread's ``default_provider`` when
the message has no run (all activity before T3's 2026-11-07 v2 run cutover).
``branches_json`` / ``pr_urls_json`` are the contributing threads' *current*
payload values (as of the scan), not history.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from rebalance.ingest.config import get_t3_code_config
from rebalance.ingest.db import db_connection
from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.ingest.sync_snapshot import get_device_id
from rebalance.lib import time_ops
from rebalance.lib.git_ops import parse_github_remote_url, run_git

logger = logging.getLogger(__name__)

SOURCE = "t3-code"
SUPPORTED_PROJECTION_SCHEMA_VERSION = 2  # t3code ORCHESTRATION_V2_PROJECTION_SCHEMA_VERSION

# Every table and column this reader depends on, probed with ``SELECT … LIMIT 0``
# before any data is read. A missing table or column is schema drift.
_REQUIRED_COLUMNS: dict[str, str] = {
    "orchestration_v2_projection_metadata": "projection_name, schema_version",
    "orchestration_v2_projection_threads": "thread_id, project_id, default_provider, payload_json",
    "orchestration_v2_projection_runs": "run_id, thread_id, provider, status, requested_at",
    "orchestration_v2_projection_messages": "thread_id, run_id, role, created_at, payload_json",
    "projection_projects": "project_id, workspace_root",
}

_VERSION_SQL = """
SELECT schema_version FROM orchestration_v2_projection_metadata
WHERE projection_name = 'thread-projections'
"""

_THREADS_SQL = """
SELECT t.thread_id,
       p.workspace_root,
       json_extract(t.payload_json, '$.createdBy') AS created_by,
       json_extract(t.payload_json, '$.branch') AS branch,
       json_extract(t.payload_json, '$.pullRequests') AS pull_requests
FROM orchestration_v2_projection_threads AS t
JOIN projection_projects AS p ON p.project_id = t.project_id
"""

_RUNS_SQL = """
SELECT thread_id,
       provider,
       date(requested_at) AS day,
       COUNT(*) AS runs,
       SUM(status = 'completed') AS runs_completed,
       MIN(requested_at) AS first_at,
       MAX(requested_at) AS last_at
FROM orchestration_v2_projection_runs
WHERE requested_at >= ?
GROUP BY thread_id, provider, day
"""

_MESSAGES_SQL = """
SELECT m.thread_id,
       COALESCE(r.provider, t.default_provider) AS provider,
       date(m.created_at) AS day,
       SUM(m.role = 'user' AND json_extract(m.payload_json, '$.createdBy') = 'user') AS user_prompts,
       MIN(m.created_at) AS first_at,
       MAX(m.created_at) AS last_at
FROM orchestration_v2_projection_messages AS m
JOIN orchestration_v2_projection_threads AS t ON t.thread_id = m.thread_id
LEFT JOIN orchestration_v2_projection_runs AS r ON r.run_id = m.run_id
WHERE m.created_at >= ?
GROUP BY m.thread_id, provider, day
"""

_ACTIVITY_COLUMNS = (
    "source",
    "device_id",
    "repo_full_name",
    "day",
    "provider",
    "threads",
    "runs",
    "runs_completed",
    "user_prompts",
    "agent_threads",
    "branches_json",
    "pr_urls_json",
    "first_at",
    "last_at",
    "scanned_at",
)


class T3SchemaDrift(Exception):
    """The T3 store does not have the projection schema this reader supports."""

    def __init__(self, message: str, observed_version: int | None = None) -> None:
        super().__init__(message)
        self.observed_version = observed_version


@contextmanager
def _open_t3(source: Path) -> Iterator[sqlite3.Connection]:
    """Open the T3 store read-only, inside one read transaction (one snapshot)."""
    with db_connection_readonly(source) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        try:
            yield conn
        finally:
            conn.rollback()


def _check_schema(conn: sqlite3.Connection) -> int:
    for table, columns in _REQUIRED_COLUMNS.items():
        try:
            conn.execute(f"SELECT {columns} FROM {table} LIMIT 0")
        except sqlite3.OperationalError as exc:
            raise T3SchemaDrift(f"{table}: {exc}") from exc
    row = conn.execute(_VERSION_SQL).fetchone()
    if row is None:
        raise T3SchemaDrift("no thread-projections schema_version row")
    version = int(row[0])
    if version != SUPPORTED_PROJECTION_SCHEMA_VERSION:
        raise T3SchemaDrift(
            f"thread-projections schema_version {version}, expected {SUPPORTED_PROJECTION_SCHEMA_VERSION}",
            observed_version=version,
        )
    return version


def _repo_for_root(root: str) -> str | None:
    """``owner/repo`` from the workspace root's ``origin`` remote, or None."""
    path = Path(root)
    if not path.is_dir():
        return None
    try:
        proc = run_git(path, "remote", "get-url", "origin", timeout=10)
    except Exception:  # noqa: BLE001 — git missing, timeout: the root is simply unresolved
        return None
    if proc.returncode != 0:
        return None
    return parse_github_remote_url(proc.stdout)


def _pr_urls(raw: Any) -> list[str]:
    try:
        items = json.loads(raw) if isinstance(raw, str) else []
    except ValueError:
        return []
    if not isinstance(items, list):
        return []
    return [item["url"] for item in items if isinstance(item, dict) and isinstance(item.get("url"), str)]


def _aggregate(conn: sqlite3.Connection, window_start: str) -> tuple[list[dict[str, Any]], int]:
    """Merge the three streams per (repo, day, provider); return (rows, unresolved_roots)."""
    repo_cache: dict[str, str | None] = {}
    threads: dict[str, dict[str, Any]] = {}
    for t in conn.execute(_THREADS_SQL):
        root = t["workspace_root"]
        if root not in repo_cache:
            repo_cache[root] = _repo_for_root(root)
        threads[t["thread_id"]] = {
            "repo": repo_cache[root],
            "agent": (t["created_by"] or "") != "user",
            "branch": t["branch"] if isinstance(t["branch"], str) and t["branch"] else None,
            "pr_urls": _pr_urls(t["pull_requests"]),
        }

    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}

    def bucket_for(row: sqlite3.Row) -> dict[str, Any] | None:
        meta = threads.get(row["thread_id"])
        if meta is None or meta["repo"] is None or not row["day"]:
            return None
        key = (meta["repo"], row["day"], row["provider"])
        b = buckets.setdefault(
            key,
            {
                "threads": set(),
                "agent_threads": set(),
                "runs": 0,
                "runs_completed": 0,
                "user_prompts": 0,
                "branches": set(),
                "pr_urls": set(),
                "first_at": None,
                "last_at": None,
            },
        )
        b["threads"].add(row["thread_id"])
        if meta["agent"]:
            b["agent_threads"].add(row["thread_id"])
        if meta["branch"]:
            b["branches"].add(meta["branch"])
        b["pr_urls"].update(meta["pr_urls"])
        if b["first_at"] is None or row["first_at"] < b["first_at"]:
            b["first_at"] = row["first_at"]
        if b["last_at"] is None or row["last_at"] > b["last_at"]:
            b["last_at"] = row["last_at"]
        return b

    for r in conn.execute(_RUNS_SQL, (window_start,)):
        b = bucket_for(r)
        if b is not None:
            b["runs"] += int(r["runs"] or 0)
            b["runs_completed"] += int(r["runs_completed"] or 0)
    for m in conn.execute(_MESSAGES_SQL, (window_start,)):
        b = bucket_for(m)
        if b is not None:
            b["user_prompts"] += int(m["user_prompts"] or 0)

    rows = [
        {
            "repo_full_name": repo,
            "day": day,
            "provider": provider,
            "threads": len(b["threads"]),
            "runs": b["runs"],
            "runs_completed": b["runs_completed"],
            "user_prompts": b["user_prompts"],
            "agent_threads": len(b["agent_threads"]),
            "branches": sorted(b["branches"]),
            "pr_urls": sorted(b["pr_urls"]),
            "first_at": b["first_at"],
            "last_at": b["last_at"],
        }
        for (repo, day, provider), b in sorted(buckets.items())
    ]
    unresolved = sum(1 for repo in repo_cache.values() if repo is None)
    return rows, unresolved


def _upsert_health(
    conn: sqlite3.Connection,
    device_id: str,
    status: str,
    now: str,
    *,
    observed_version: int | None = None,
    message: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO agent_session_source_health
            (source, device_id, last_attempt_at, last_success_at, status, observed_schema_version, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, device_id) DO UPDATE SET
            last_attempt_at = excluded.last_attempt_at,
            last_success_at = COALESCE(excluded.last_success_at, agent_session_source_health.last_success_at),
            status = excluded.status,
            observed_schema_version = excluded.observed_schema_version,
            message = excluded.message
        """,
        (SOURCE, device_id, now, now if status == "ok" else None, status, observed_version, message),
    )


def _record_health(database_path: Path, device_id: str, status: str, now: str, **kw: Any) -> None:
    with db_connection(database_path) as conn:
        _upsert_health(conn, device_id, status, now, **kw)
        conn.commit()


def _write(
    database_path: Path,
    device_id: str,
    rows: list[dict[str, Any]],
    window_start: str,
    now: str,
    version: int,
    message: str,
) -> None:
    """Replace this device's in-window rows and record ``ok`` health in one transaction."""
    placeholders = ", ".join("?" for _ in _ACTIVITY_COLUMNS)
    insert_sql = f"INSERT INTO agent_session_activity ({', '.join(_ACTIVITY_COLUMNS)}) VALUES ({placeholders})"
    with db_connection(database_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                "DELETE FROM agent_session_activity WHERE source = ? AND device_id = ? AND day >= ?",
                (SOURCE, device_id, window_start),
            )
            for row in rows:
                conn.execute(
                    insert_sql,
                    (
                        SOURCE,
                        device_id,
                        row["repo_full_name"],
                        row["day"],
                        row["provider"],
                        row["threads"],
                        row["runs"],
                        row["runs_completed"],
                        row["user_prompts"],
                        row["agent_threads"],
                        json.dumps(row["branches"]),
                        json.dumps(row["pr_urls"]),
                        row["first_at"],
                        row["last_at"],
                        now,
                    ),
                )
            _upsert_health(conn, device_id, "ok", now, observed_version=version, message=message)
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


def t3_code_health(database_path: Path, device_id: str | None = None) -> dict[str, Any] | None:
    """This device's persisted health row, or None. Reads ``rebalance.db`` only."""
    path = Path(database_path)
    if not path.exists():
        return None
    with db_connection_readonly(path) as conn:
        try:
            row = conn.execute(
                "SELECT * FROM agent_session_source_health WHERE source = ? AND device_id = ?",
                (SOURCE, device_id or get_device_id()),
            ).fetchone()
        except sqlite3.OperationalError:  # table absent: migration 0010 not applied yet
            return None
    return dict(row) if row is not None else None


def sync_t3_code_activity(
    database_path: Path,
    *,
    dry_run: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Refresh this device's T3 Code activity rows. ``dry_run`` reads and writes nothing."""
    cfg = config if config is not None else get_t3_code_config()
    result: dict[str, Any] = {"scope": "t3_code", "dry_run": dry_run}
    if not cfg.get("t3_code_activity_enabled"):
        return {**result, "skipped": True, "reason": "disabled (opt-in: t3_code_activity_enabled)"}

    source = Path(cfg["t3_code_db_path"])
    device_id = get_device_id()
    now = time_ops.now_iso()
    window_days = int(cfg["t3_code_window_days"])
    window_start = time_ops.utc_date_days_ago(window_days)
    result["window_start"] = window_start

    if not source.is_file():
        if not dry_run:
            _record_health(database_path, device_id, "missing", now, message=f"T3 store not found: {source}")
        return {**result, "skipped": True, "reason": f"T3 store not found: {source}"}

    try:
        with _open_t3(source) as conn:
            version = _check_schema(conn)
            rows, unresolved = _aggregate(conn, window_start)
    except T3SchemaDrift as drift:
        if not dry_run:
            _record_health(
                database_path,
                device_id,
                "drift",
                now,
                observed_version=drift.observed_version,
                message=str(drift),
            )
        return {**result, "skipped": True, "reason": f"unsupported T3 schema: {drift}"}
    except Exception as exc:
        if not dry_run:
            _record_health(database_path, device_id, "error", now, message=f"{type(exc).__name__}: {exc}")
        raise

    message = f"{len(rows)} rows; {unresolved} unresolved workspace roots"
    result.update({"rows": len(rows), "unresolved_roots": unresolved, "schema_version": version})
    if dry_run:
        return {**result, "aggregates": rows}
    _write(database_path, device_id, rows, window_start, now, version, message)
    logger.info("t3_code: wrote %d rows for %s since %s", len(rows), device_id, window_start)
    return result
