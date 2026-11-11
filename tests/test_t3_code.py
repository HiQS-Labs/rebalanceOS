"""GH-375: opt-in, read-only T3 Code session activity collector.

The fixture T3 store is built from the pinned DDL subset of t3code's
``055_OrchestrationV2.ts`` (threads/runs/messages), ``005_Projections.ts``
(projects) and ``OrchestrationV2/Foundation.ts`` (projection metadata). Its
workspace roots are a temp git repo with a GitHub ``origin`` and one plain
directory (an unresolvable root).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from rebalance.ingest import t3_code
from rebalance.ingest.db import db_connection, ensure_schema, run_migrations
from rebalance.ingest.db import migrate

FROZEN = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone.utc)
DEVICE = "test-mac"
PR_URL = "https://github.com/acme/widgets/pull/7"

T3_DDL = """
CREATE TABLE orchestration_v2_projection_metadata (
  projection_name TEXT PRIMARY KEY, schema_version INTEGER NOT NULL,
  last_sequence INTEGER NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE orchestration_v2_projection_threads (
  thread_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL,
  default_provider TEXT NOT NULL, runtime_mode TEXT NOT NULL, interaction_mode TEXT NOT NULL,
  active_provider_thread_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  archived_at TEXT, deleted_at TEXT, payload_json TEXT NOT NULL);
CREATE TABLE orchestration_v2_projection_runs (
  run_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
  provider TEXT NOT NULL, provider_thread_id TEXT, status TEXT NOT NULL,
  requested_at TEXT NOT NULL, completed_at TEXT, payload_json TEXT NOT NULL);
CREATE TABLE orchestration_v2_projection_messages (
  message_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, run_id TEXT, node_id TEXT,
  role TEXT NOT NULL, streaming INTEGER NOT NULL, created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL, payload_json TEXT NOT NULL);
CREATE TABLE projection_projects (
  project_id TEXT PRIMARY KEY, title TEXT NOT NULL, workspace_root TEXT NOT NULL,
  default_model TEXT, scripts_json TEXT NOT NULL, created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL, deleted_at TEXT);
CREATE TABLE auth_pairing_tokens (token TEXT);
INSERT INTO auth_pairing_tokens VALUES ('PAIRING-SECRET');
"""

SECRET_TEXT = "SECRET PROMPT BODY"


# --------------------------------------------------------------------------- fixtures


def _freeze(at: datetime = FROZEN):
    return patch("rebalance.lib.time_ops._current_time", lambda tz=None: at.astimezone(tz or timezone.utc))


def _git_repo(path: Path, remote: str) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "remote", "add", "origin", remote], check=True)
    return path


def _thread(conn, tid, project, provider, created_by, branch=None, prs=None):
    payload = {"createdBy": created_by, "creationSource": "web", "branch": branch, "pullRequests": prs}
    conn.execute(
        "INSERT INTO orchestration_v2_projection_threads VALUES (?,?,?,?,?,?,NULL,?,?,NULL,NULL,?)",
        (tid, project, "t", provider, "full", "default", "2026-09-01T00:00:00.000Z", "2026-11-11T00:00:00.000Z",
         json.dumps(payload)),
    )


def _run(conn, rid, tid, ordinal, provider, status, requested_at):
    conn.execute(
        "INSERT INTO orchestration_v2_projection_runs VALUES (?,?,?,?,NULL,?,?,NULL,'{}')",
        (rid, tid, ordinal, provider, status, requested_at),
    )


def _msg(conn, mid, tid, rid, role, created_by, created_at):
    conn.execute(
        "INSERT INTO orchestration_v2_projection_messages VALUES (?,?,?,NULL,?,0,?,?,?)",
        (mid, tid, rid, role, created_at, created_at, json.dumps({"createdBy": created_by, "text": SECRET_TEXT})),
    )


def build_t3(tmp_path: Path, *, version: int = 2, empty: bool = False, drop_role: bool = False) -> Path:
    db = tmp_path / "statev2.sqlite"
    repo = _git_repo(tmp_path / "widgets", "git@github.com:acme/widgets.git")
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    ddl = T3_DDL
    if drop_role:
        ddl = ddl.replace("role TEXT NOT NULL, streaming", "streaming")
    with sqlite3.connect(db) as conn:
        conn.executescript(ddl)
        conn.execute(
            "INSERT INTO orchestration_v2_projection_metadata VALUES ('thread-projections', ?, 1, 'x')", (version,)
        )
        conn.execute("INSERT INTO projection_projects VALUES ('P1','w',?,NULL,'[]','x','x',NULL)", (str(repo),))
        conn.execute("INSERT INTO projection_projects VALUES ('P2','n',?,NULL,'[]','x','x',NULL)", (str(plain),))
        if empty or drop_role:
            return db
        _thread(conn, "T1", "P1", "codex", "user", "feat/x", [{"url": PR_URL, "number": 7, "snapshot": {"t": 1}}])
        _thread(conn, "T2", "P1", "codex", "agent")
        _thread(conn, "T3", "P2", "codex", "user")
        # R1 crosses midnight: counted on its requested_at day.
        _run(conn, "R1", "T1", 1, "codex", "completed", "2026-11-10T23:59:30.000Z")
        # T2 switches provider within one day.
        _run(conn, "R2a", "T2", 1, "codex", "completed", "2026-11-11T09:00:00.000Z")
        _run(conn, "R2b", "T2", 2, "claudeAgent", "failed", "2026-11-11T10:00:00.000Z")
        _run(conn, "R3", "T3", 1, "codex", "completed", "2026-11-11T08:00:00.000Z")  # unresolved root
        _run(conn, "Rold", "T1", 0, "codex", "completed", "2026-09-01T00:00:00.000Z")  # outside window
        _msg(conn, "M1", "T1", None, "user", "user", "2026-11-01T10:00:00.000Z")  # null run_id
        _msg(conn, "M2", "T1", "R1", "user", "user", "2026-11-10T23:59:20.000Z")
        _msg(conn, "M3", "T1", "R1", "assistant", "agent", "2026-11-11T00:04:00.000Z")
        _msg(conn, "M4", "T2", "R2b", "user", "agent", "2026-11-11T10:00:01.000Z")
        _msg(conn, "M5", "T2", "R2b", "assistant", "agent", "2026-11-11T10:01:00.000Z")
        _msg(conn, "M6", "T3", "R3", "user", "user", "2026-11-11T08:00:01.000Z")
    return db


def _row(day, provider, threads, runs, completed, prompts, agent, branches, prs, first, last):
    return {
        "repo_full_name": "acme/widgets",
        "day": day,
        "provider": provider,
        "threads": threads,
        "runs": runs,
        "runs_completed": completed,
        "user_prompts": prompts,
        "agent_threads": agent,
        "branches": branches,
        "pr_urls": prs,
        "first_at": first,
        "last_at": last,
    }


EXPECTED = [
    _row("2026-11-01", "codex", 1, 0, 0, 1, 0, ["feat/x"], [PR_URL], "2026-11-01T10:00:00.000Z", "2026-11-01T10:00:00.000Z"),
    _row("2026-11-10", "codex", 1, 1, 1, 1, 0, ["feat/x"], [PR_URL], "2026-11-10T23:59:20.000Z", "2026-11-10T23:59:30.000Z"),
    _row("2026-11-11", "claudeAgent", 1, 1, 0, 0, 1, [], [], "2026-11-11T10:00:00.000Z", "2026-11-11T10:01:00.000Z"),
    _row("2026-11-11", "codex", 2, 1, 1, 0, 1, ["feat/x"], [PR_URL], "2026-11-11T00:04:00.000Z", "2026-11-11T09:00:00.000Z"),
]


def _cfg(t3_db: Path, *, enabled: bool = True, watch: bool = False) -> dict[str, Any]:
    return {
        "t3_code_activity_enabled": enabled,
        "t3_code_db_path": str(t3_db),
        "t3_code_window_days": 30,
        "watch_repos_from_agent_sessions": watch,
    }


@pytest.fixture
def rdb(tmp_path: Path) -> Path:
    db = tmp_path / "rebalance.db"
    with db_connection(db, ensure_schema) as conn:
        run_migrations(conn)
    return db


@pytest.fixture(autouse=True)
def _device():
    with patch("rebalance.ingest.t3_code.get_device_id", return_value=DEVICE):
        yield


def _sync(rdb: Path, t3_db: Path, **kw: Any) -> dict[str, Any]:
    with _freeze(kw.pop("at", FROZEN)):
        return t3_code.sync_t3_code_activity(rdb, config=_cfg(t3_db), **kw)


def _activity(rdb: Path) -> list[dict[str, Any]]:
    with db_connection(rdb) as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM agent_session_activity ORDER BY day, provider")]


def _health(rdb: Path) -> dict[str, Any] | None:
    with db_connection(rdb) as conn:
        row = conn.execute("SELECT * FROM agent_session_source_health").fetchone()
    return dict(row) if row else None


def _as_expected(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        r = dict(r)
        r["branches"] = json.loads(r.pop("branches_json"))
        r["pr_urls"] = json.loads(r.pop("pr_urls_json"))
        for k in ("source", "device_id", "scanned_at"):
            r.pop(k)
        out.append(r)
    return out


# --------------------------------------------------------------------------- aggregation


def test_refresh_index_writes_predicted_rows(tmp_path: Path, rdb: Path) -> None:
    from rebalance.ingest.index_ops import refresh_index

    t3_db = build_t3(tmp_path)
    with _freeze(), patch("rebalance.ingest.t3_code.get_t3_code_config", return_value=_cfg(t3_db)):
        out = refresh_index(rdb, scope=["t3_code"], update_dashboard_note=False)
    assert out["errors"] == []
    res = next(r for r in out["results"] if r["scope"] == "t3_code")
    assert res["rows"] == 4 and res["unresolved_roots"] == 1
    rows = _activity(rdb)
    assert {(r["source"], r["device_id"]) for r in rows} == {("t3-code", DEVICE)}
    assert _as_expected(rows) == EXPECTED
    health = _health(rdb)
    assert health["status"] == "ok" and health["observed_schema_version"] == 2
    assert health["last_success_at"] == health["last_attempt_at"]
    # Metadata only: no message text and no auth table content reaches rebalance.db.
    with db_connection(rdb) as conn:
        dump = "\n".join(conn.iterdump())
    assert SECRET_TEXT not in dump and "PAIRING-SECRET" not in dump


def test_dry_run_returns_aggregates_and_writes_nothing(tmp_path: Path, rdb: Path) -> None:
    res = _sync(rdb, build_t3(tmp_path), dry_run=True)
    assert res["aggregates"] == EXPECTED
    assert _activity(rdb) == [] and _health(rdb) is None


def test_aggregation_edge_cases_exact(tmp_path: Path, rdb: Path) -> None:
    """Null run_id, provider switch in one thread, run crossing midnight: no multiplied rows."""
    _sync(rdb, build_t3(tmp_path))
    by_key = {(r["day"], r["provider"]): r for r in _activity(rdb)}
    assert by_key[("2026-11-01", "codex")]["user_prompts"] == 1  # null run_id → thread default_provider
    assert by_key[("2026-11-10", "codex")]["runs"] == 1  # R1 counted on its requested_at day
    assert by_key[("2026-11-11", "claudeAgent")]["runs"] == 1  # provider switch: one run each side
    assert by_key[("2026-11-11", "codex")]["runs"] == 1
    assert by_key[("2026-11-11", "claudeAgent")]["user_prompts"] == 0  # role user, createdBy agent


def test_row_joined_query_inflates(tmp_path: Path) -> None:
    """Red control for the aggregation contract: a row-to-row join multiplies counts."""
    t3_db = build_t3(tmp_path)
    with sqlite3.connect(t3_db) as conn:
        naive = conn.execute(
            "SELECT COUNT(r.run_id) FROM orchestration_v2_projection_runs r "
            "JOIN orchestration_v2_projection_messages m ON m.thread_id = r.thread_id "
            "WHERE r.provider = 'claudeAgent' AND date(r.requested_at) = '2026-11-11'"
        ).fetchone()[0]
    expected = next(r for r in EXPECTED if r["provider"] == "claudeAgent")["runs"]
    assert naive != expected  # 2 joined rows for 1 run


def test_mcp_agent_session_activity(tmp_path: Path, rdb: Path) -> None:
    from rebalance.mcp.server import create_server

    _sync(rdb, build_t3(tmp_path))
    server = create_server(rdb)

    def call(args: dict[str, Any]) -> list[dict[str, Any]]:
        with _freeze():
            result = asyncio.run(server.call_tool("agent_session_activity", args))
        content = result[0] if isinstance(result, tuple) else result
        return [json.loads(block.text) for block in content]

    (repo,) = call({"since_days": 14})
    assert repo["repo"] == "acme/widgets"
    assert repo["runs"] == 3 and repo["runs_completed"] == 2 and repo["user_prompts"] == 2
    # One thread on two providers in one day counts once per provider (plan QA r1 S1).
    assert repo["thread_provider_days"] == 5
    assert repo["providers"]["codex"] == {"thread_days": 4, "runs": 2, "runs_completed": 2, "user_prompts": 2}
    assert repo["providers"]["claudeAgent"] == {"thread_days": 1, "runs": 1, "runs_completed": 0, "user_prompts": 0}
    assert repo["pr_urls"] == [PR_URL] and repo["branches"] == ["feat/x"]
    assert repo["last_at"] == "2026-11-11T10:01:00.000Z"
    (narrow,) = call({"since_days": 0})  # clamped to 1 → 2026-11-10 onward
    assert narrow["runs"] == 3 and narrow["user_prompts"] == 1


# --------------------------------------------------------------------------- guard, empty, missing


@pytest.mark.parametrize("kind", ["version3", "missing_column"])
def test_unsupported_schema_skips_with_drift(tmp_path: Path, rdb: Path, kind: str) -> None:
    t3_db = build_t3(tmp_path, version=3) if kind == "version3" else build_t3(tmp_path, drop_role=True)
    res = _sync(rdb, t3_db)
    assert res["skipped"] is True and res["reason"].startswith("unsupported T3 schema")
    assert _activity(rdb) == []
    health = _health(rdb)
    assert health["status"] == "drift" and health["last_success_at"] is None
    assert health["observed_schema_version"] == (3 if kind == "version3" else None)


def test_empty_store_ok(tmp_path: Path, rdb: Path) -> None:
    res = _sync(rdb, build_t3(tmp_path, empty=True))
    assert res["rows"] == 0 and _activity(rdb) == []
    assert _health(rdb)["status"] == "ok"


def test_missing_file_records_missing(tmp_path: Path, rdb: Path) -> None:
    res = _sync(rdb, tmp_path / "absent.sqlite")
    assert res["skipped"] is True and _activity(rdb) == []
    assert _health(rdb)["status"] == "missing"


def test_disabled_never_opens_store(tmp_path: Path, rdb: Path) -> None:
    t3_db = build_t3(tmp_path)
    with patch("rebalance.ingest.t3_code._open_t3", side_effect=AssertionError("opened")):
        res = t3_code.sync_t3_code_activity(rdb, config=_cfg(t3_db, enabled=False))
    assert res["skipped"] is True and _activity(rdb) == [] and _health(rdb) is None


# --------------------------------------------------------------------------- idempotency, rollback


def test_rerun_identical_and_single_row_delta(tmp_path: Path, rdb: Path) -> None:
    t3_db = build_t3(tmp_path)
    _sync(rdb, t3_db)
    first = _activity(rdb)
    _sync(rdb, t3_db)
    assert _activity(rdb) == first  # scanned_at included
    with sqlite3.connect(t3_db) as conn:
        _msg(conn, "M7", "T2", "R2b", "user", "user", "2026-11-11T11:00:00.000Z")
    _sync(rdb, t3_db)
    before = {(r["day"], r["provider"]): r for r in first}
    after = {(r["day"], r["provider"]): r for r in _activity(rdb)}
    assert before.keys() == after.keys()
    changed = {k for k in before if before[k] != after[k]}
    assert changed == {("2026-11-11", "claudeAgent")}
    assert after[("2026-11-11", "claudeAgent")]["user_prompts"] == 1


def test_insert_failure_rolls_back(tmp_path: Path, rdb: Path) -> None:
    t3_db = build_t3(tmp_path)
    _sync(rdb, t3_db)
    rows_before, health_before = _activity(rdb), _health(rdb)
    with db_connection(rdb) as conn:  # abort the 2nd insert of a scan
        conn.execute(
            "CREATE TRIGGER fail_second BEFORE INSERT ON agent_session_activity "
            "WHEN (SELECT COUNT(*) FROM agent_session_activity WHERE scanned_at = NEW.scanned_at) >= 1 "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
        conn.commit()
    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        _sync(rdb, t3_db, at=FROZEN + timedelta(hours=1))
    assert _activity(rdb) == rows_before
    assert _health(rdb) == health_before


# --------------------------------------------------------------------------- migration


def _tables(conn) -> set[str]:
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def test_migration_0010_fresh_and_from_0009(tmp_path: Path) -> None:
    new = {"agent_session_activity", "agent_session_source_health"}
    fresh = tmp_path / "fresh.db"
    with db_connection(fresh, ensure_schema) as conn:
        assert run_migrations(conn) >= 10
        assert new <= _tables(conn)

    old = tmp_path / "old.db"
    original = migrate.discover_migrations
    with patch.object(migrate, "discover_migrations", lambda: [m for m in original() if m[0] <= 9]):
        with db_connection(old, ensure_schema) as conn:
            assert run_migrations(conn) == 9
            assert not (new & _tables(conn))
    with db_connection(old) as conn:
        v = run_migrations(conn)
        assert v >= 10 and new <= _tables(conn)
        rows = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
        assert run_migrations(conn) == v  # second run is a no-op
        assert conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == rows


# --------------------------------------------------------------------------- frozen GitHub contract


def _github_hash(rdb: Path) -> str:
    with db_connection(rdb) as conn:
        rows = conn.execute("SELECT * FROM github_activity ORDER BY id").fetchall()
    return hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()


def test_github_contract_unchanged(tmp_path: Path, rdb: Path) -> None:
    from rebalance.ingest.db import ensure_github_schema, ensure_project_schema
    from rebalance.ingest.github_scan import get_hiqs_work_activity
    from rebalance.ingest.index_ops import refresh_index

    with db_connection(rdb) as conn:
        ensure_project_schema(conn)
        ensure_github_schema(conn)
        conn.execute(
            "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, prs_opened, prs_merged,"
            " issues_opened, issue_comments, reviews, last_active_at, scanned_at)"
            " VALUES ('me', 'acme/widgets', date('now','-1 day'), 3, 1, 1, 0, 0, 0, 0, '2026-11-10T00:00:00Z', 'x')"
        )
        conn.commit()
    project_repos = {"Widgets": ["acme/widgets"]}

    def hiqs() -> list[dict[str, Any]]:
        return get_hiqs_work_activity(database_path=rdb, project_repos=project_repos, since_days=30)

    hash_before, hiqs_before = _github_hash(rdb), hiqs()
    t3_db = build_t3(tmp_path)
    with _freeze(), patch("rebalance.ingest.t3_code.get_t3_code_config", return_value=_cfg(t3_db)):
        refresh_index(rdb, scope=["t3_code"], update_dashboard_note=False)
    assert _activity(rdb)  # the refresh really wrote T3 rows
    assert _github_hash(rdb) == hash_before
    assert hiqs() == hiqs_before
    # Red control: the comparison detects a one-counter mutation.
    with db_connection(rdb) as conn:
        conn.execute("UPDATE github_activity SET commits = commits + 1")
        conn.commit()
    assert _github_hash(rdb) != hash_before


# --------------------------------------------------------------------------- privacy

ALLOWED_PATHS = {"$.createdBy", "$.creationSource", "$.branch", "$.worktreePath", "$.pullRequests"}
ALLOWED_TABLES = {
    "orchestration_v2_projection_metadata",
    "orchestration_v2_projection_threads",
    "orchestration_v2_projection_runs",
    "orchestration_v2_projection_messages",
    "projection_projects",
}
_PATH_RE = re.compile(r"\$\.[A-Za-z_][\w.\[\]]*")
_TABLE_RE = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z_]\w*)", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(r"auth_|secret|token|pairing|webhook", re.IGNORECASE)


def metadata_only_violations(sql: str) -> list[str]:
    bad = [p for p in _PATH_RE.findall(sql) if p not in ALLOWED_PATHS]
    bad += [t for t in _TABLE_RE.findall(sql) if t not in ALLOWED_TABLES]
    bad += _FORBIDDEN_RE.findall(sql)
    return bad


def test_executed_sql_is_metadata_only(tmp_path: Path, rdb: Path) -> None:
    executed: list[str] = []
    real = t3_code.db_connection_readonly

    @contextmanager
    def traced(path):
        with real(path) as conn:
            conn.set_trace_callback(executed.append)
            yield conn

    with patch("rebalance.ingest.t3_code.db_connection_readonly", traced):
        _sync(rdb, build_t3(tmp_path))
    selects = [s for s in executed if "SELECT" in s.upper()]
    assert len(selects) >= 4  # probes + version + three streams actually ran
    assert {s: metadata_only_violations(s) for s in executed if metadata_only_violations(s)} == {}
    # Red control: a text read is caught.
    assert metadata_only_violations("SELECT json_extract(payload_json,'$.text') FROM orchestration_v2_projection_messages")


# --------------------------------------------------------------------------- doctor, watched set


def _seed_health(rdb: Path, status: str, *, success: str | None, version: int | None = 2) -> None:
    with db_connection(rdb) as conn:
        conn.execute(
            "INSERT INTO agent_session_source_health VALUES ('t3-code', ?, ?, ?, ?, ?, 'm')",
            (DEVICE, "2026-11-11T11:00:00+00:00", success, status, version),
        )
        conn.commit()


@pytest.mark.parametrize(
    ("enabled", "status", "success", "version", "level", "needle"),
    [
        (False, None, None, None, "OK", "not enabled"),
        (False, "ok", "2026-11-11T11:00:00+00:00", 2, "OK", "retained health: ok"),
        (True, None, None, None, "WARN", "no scan recorded"),
        (True, "missing", None, None, "WARN", "missing"),
        (True, "drift", None, 3, "WARN", "schema_version 3"),
        (True, "error", None, None, "WARN", "error"),
        (True, "ok", "2026-11-08T11:00:00+00:00", 2, "WARN", "stale"),
        (True, "ok", "2026-11-11T11:00:00+00:00", 2, "OK", "last success"),
    ],
)
def test_doctor_t3_code_states(tmp_path, rdb, enabled, status, success, version, level, needle) -> None:
    from rebalance import doctor

    if status:
        _seed_health(rdb, status, success=success, version=version)
    cfg = _cfg(tmp_path / "statev2.sqlite", enabled=enabled)
    with (
        _freeze(),
        patch("rebalance.ingest.config.get_t3_code_config", return_value=cfg),
        patch("rebalance.ingest.t3_code._open_t3", side_effect=AssertionError("doctor opened the T3 store")),
    ):
        check = doctor._check_t3_code(rdb)
    assert check.status == getattr(doctor, level)
    assert needle in check.detail


def test_activity_repos_union_opt_in(rdb: Path) -> None:
    from rebalance.ingest.index_ops import _activity_repos
    from rebalance.lib import time_ops

    today = time_ops.utc_date_days_ago(0)
    with db_connection(rdb) as conn:
        conn.execute(
            "INSERT INTO agent_session_activity (source, device_id, repo_full_name, day, provider, scanned_at)"
            " VALUES ('t3-code', ?, 'acme/agent-only', ?, 'codex', 'x')",
            (DEVICE, today),
        )
        conn.commit()
    with patch("rebalance.ingest.config.get_t3_code_config", return_value=_cfg(Path("x"), watch=False)):
        assert "acme/agent-only" not in _activity_repos(rdb)
    with patch("rebalance.ingest.config.get_t3_code_config", return_value=_cfg(Path("x"), watch=True)):
        assert "acme/agent-only" in _activity_repos(rdb)
